import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Конфигурация ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Инициализация базы данных
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Модели данных
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    chat_id = Column(Integer)
    status = Column(String)  # 'premium', 'blocked', 'default'
    last_report = Column(DateTime)

class AuthCode(Base):
    __tablename__ = 'auth_codes'
    code = Column(String, primary_key=True)
    used = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# Состояния для ConversationHandler
AUTH, REPORT, ADMIN = range(3)

# --- Вспомогательные функции ---
def generate_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])

async def send_to_admin(context: CallbackContext, message: str):
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# --- Обработчики команд ---
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Добро пожаловать! Введите одноразовый код для авторизации:")
    return AUTH

async def handle_auth_code(update: Update, context: CallbackContext):
    code = update.message.text.upper()
    session = Session()
    auth_code = session.query(AuthCode).filter_by(code=code, used=False).first()
    
    if auth_code:
        auth_code.used = True
        user = User(
            username=update.effective_user.username,
            chat_id=update.effective_chat.id,
            status='default'
        )
        session.add(user)
        session.commit()
        await send_to_admin(context, f"🚨 Код {code} использован пользователем @{user.username}")
        await update.message.reply_text("✅ Авторизация успешна!", reply_markup=main_menu())
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Неверный код! Попробуйте еще раз:")
        return AUTH

async def request_report(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📝 Перед получением данных отправьте отчет:",
        reply_markup=generate_keyboard([("Премиум", "premium"), ("Блок в чате", "blocked"), ("Другое", "other")])
    )
    return REPORT

async def handle_report(update: Update, context: CallbackContext):
    # Логика обработки отчета и сохранения скриншотов
    await update.message.reply_text("📊 Данные за последние 10 минут:")
    # ... (код для отправки данных из Excel)
    return ConversationHandler.END

# --- Админ-панель ---
async def admin_panel(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    buttons = [
        ("Загрузить Excel", "upload_excel"),
        ("Сгенерировать код", "generate_code"),
        ("Список пользователей", "list_users")
    ]
    await update.message.reply_text("⚙️ Панель администратора:", reply_markup=generate_keyboard(buttons))

# --- Планировщик задач ---
async def send_scheduled_data(context: CallbackContext):
    session = Session()
    users = session.query(User).all()
    for user in users:
        # Логика выборки данных из Excel
        await context.bot.send_message(chat_id=user.chat_id, text="📅 Данные: ...")

# --- Инициализация бота ---
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Conversation Handler для основного потока
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUTH: [MessageHandler(filters.TEXT, handle_auth_code)],
            REPORT: [MessageHandler(filters.PHOTO | filters.TEXT, handle_report)]
        },
        fallbacks=[]
    )
    
    # Админ-команды
    application.add_handler(CommandHandler('admin', admin_panel))
    
    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_scheduled_data, 'interval', minutes=10)
    scheduler.start()
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()