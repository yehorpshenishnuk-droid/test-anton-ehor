import os
import logging
from datetime import datetime, timezone
import requests
from aiogram import Bot, Dispatcher, executor, types

# Logging
logging.basicConfig(level=logging.INFO)

# Read tokens from environment
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHOICE_TOKEN = os.getenv("CHOICE_TOKEN")

# Check token existence
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")
if not CHOICE_TOKEN:
    raise ValueError("CHOICE_TOKEN not found in environment variables")

# Init bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# API endpoint
CHOICE_API_URL = "https://open-api.choiceqr.com/api/bookings/list"

# Start command
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("\ud83d\udcc5 \u0411\u0440\u043e\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435")
    await message.answer("\u041f\u0440\u0438\u0432\u0435\u0442! \u0427\u0442\u043e \u0445\u043e\u0447\u0435\u0448\u044c \u0441\u0434\u0435\u043b\u0430\u0442\u044c?", reply_markup=keyboard)

# Handler for "\ud83d\udcc5 \u0411\u0440\u043e\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435"
@dp.message_handler(lambda message: message.text == "\ud83d\udcc5 \u0411\u0440\u043e\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435")
async def list_bookings(message: types.Message):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    payload = {
        "from": today_start.isoformat(),
        "till": today_end.isoformat(),
        "periodField": "bookingDt"
    }

    headers = {
        "Authorization": f"Bearer {CHOICE_TOKEN}"
    }

    try:
        response = requests.get(CHOICE_API_URL, params=payload, headers=headers)
        response.raise_for_status()
        bookings = response.json()

        upcoming = []
        for b in bookings:
            booking_time = datetime.fromisoformat(b['bookingDt'].replace('Z', '+00:00'))
            if booking_time > now:
                name = b.get('customerName', '---')
                people = b.get('numberOfPersons', '?')
                time = booking_time.strftime("%H:%M")
                upcoming.append(f"{name} в {time}, {people} чел.")

        if upcoming:
            reply = "\u0411\u0440\u043e\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f \u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f (\u043f\u043e\u0441\u043b\u0435 \u0442\u0435\u043a\u0443\u0449\u0435\u0433\u043e \u0432\u0440\u0435\u043c\u0435\u043d\u0438):\n" + "\n".join(upcoming)
        else:
            reply = "\u041d\u0435\u0442 \u0437\u0430\u043f\u0438\u0441\u0435\u0439 \u043d\u0430 \u043e\u0441\u0442\u0430\u0432\u0448\u0435\u0435\u0441\u044f \u0432\u0440\u0435\u043c\u044f \u0441\u0435\u0433\u043e\u0434\u043d\u044f."

        await message.answer(reply)

    except Exception as e:
        logging.exception("Error while fetching bookings")
        await message.answer("\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u0438 \u0434\u0430\u043d\u043d\u044b\u0445. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0441\u043d\u043e\u0432\u0430.")

# Main entry
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
