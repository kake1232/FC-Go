import os
import logging
from threading import Event
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    Filters
)
import requests
import sqlite3
from datetime import datetime, timedelta

# Константы состояний
MIN_PRICE, MAX_PRICE = range(2)

# Настройки
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
API_URL = "https://api.fragment.com/numbers"
DB_NAME = "users.db"

# Инициализация БД
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        min_price REAL,
        max_price REAL
    )
''')
conn.commit()

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🎯 Установить ценовой диапазон", callback_data='set_price')],
        [InlineKeyboardButton("📊 Текущие настройки", callback_data='show_settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "🚀 Добро пожаловать в NFT-монитор Fragment!",
        reply_markup=reply_markup
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == 'set_price':
        query.message.reply_text("Введите минимальную цену в TON:")
        return MIN_PRICE
    elif query.data == 'show_settings':
        show_settings(update, context)
    return ConversationHandler.END

def min_price_input(update: Update, context: CallbackContext):
    try:
        price = float(update.message.text)
        context.user_data['min_price'] = price
        update.message.reply_text("Теперь введите максимальную цену в TON:")
        return MAX_PRICE
    except ValueError:
        update.message.reply_text("❌ Ошибка! Введите число. Попробуйте снова:")
        return MIN_PRICE

def max_price_input(update: Update, context: CallbackContext):
    try:
        max_price = float(update.message.text)
        min_price = context.user_data.get('min_price', 0)
        
        if max_price <= min_price:
            raise ValueError("Максимум должен быть больше минимума")
        
        # Сохранение в БД
        user_id = update.effective_user.id
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, min_price, max_price)
            VALUES (?, ?, ?)
        ''', (user_id, min_price, max_price))
        conn.commit()
        
        update.message.reply_text(f"✅ Диапазон установлен: {min_price} - {max_price} TON")
        return ConversationHandler.END
    except ValueError as e:
        update.message.reply_text(f"❌ Ошибка: {str(e)}. Введите корректную цену:")
        return MAX_PRICE

def show_settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT min_price, max_price FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        text = f"⚙️ Текущие настройки:\nМинимум: {result[0]} TON\nМаксимум: {result[1]} TON"
    else:
        text = "⚙️ Настройки не установлены"
    
    context.bot.send_message(chat_id=user_id, text=text)

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('🚫 Операция отменена')
    return ConversationHandler.END

# Остальные функции (fetch_fragment_data, send_updates, error_handler) остаются как в оригинале

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Диалог для установки цены
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            MIN_PRICE: [MessageHandler(Filters.text & ~Filters.command, min_price_input)],
            MAX_PRICE: [MessageHandler(Filters.text & ~Filters.command, max_price_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button_handler))

    # Планировщик и обработка ошибок
    jq = updater.job_queue
    jq.run_repeating(send_updates, interval=1800, first=10)
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()