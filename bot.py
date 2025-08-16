import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime, timedelta
import requests

# Логирование
logging.basicConfig(level=logging.INFO)

# Токены (можно заменить на os.getenv(...) для Render)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8308742614:AAFnAStBXSvc3NR9wyoEMDAvSEXJmH43iwI"
CHOICE_API_TOKEN = os.getenv("CHOICE_API_TOKEN") or "VlFmffA-HWXnYEm-cOXRIze-FDeVdAw"
POSTER_TOKEN = os.getenv("POSTER_API_TOKEN") or "PASTE_YOUR_POSTER_TOKEN"
POSTER_SPOT_ID = os.getenv("POSTER_SPOT_ID") or "PASTE_YOUR_SPOT_ID"

# Telegram Bot Init
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Кнопки
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("\U0001F4B0 Выторг за день", "\U0001F4C5 Бронирование")

# Обработка /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Выберите действие:", reply_markup=keyboard)

# Обработка кнопок
@dp.message_handler(lambda message: message.text == "\U0001F4B0 Выторг за день")
async def handle_revenue(message: types.Message):
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://joinposter.com/api/dash.getShiftReport?token={POSTER_TOKEN}&spot_id={POSTER_SPOT_ID}&date={today}"
    try:
        response = requests.get(url)
        data = response.json()
        revenue = data.get("response", {}).get("total_sum", 0)
        await message.answer(f"Выторг за сегодня: {round(revenue / 100, 2)} ₽")
    except Exception as e:
        await message.answer(f"Ошибка при получении выторга: {e}")

# Обработка кнопки Бронирование
@dp.message_handler(lambda message: message.text == "\U0001F4C5 Бронирование")
async def handle_bookings(message: types.Message):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_iso = today_start.isoformat() + "Z"
    end_iso = today_end.isoformat() + "Z"

    headers = {"Authorization": f"Bearer {CHOICE_API_TOKEN}"}
    url = f"https://open-api.choiceqr.com/api/v1/reservations?start_date={start_iso}&end_date={end_iso}"

    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        bookings = data.get("data", [])

        future_bookings = []
        for booking in bookings:
            dt_str = booking.get("dateTime")
            if not dt_str:
                continue
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt > now:
                name = booking.get("customer", {}).get("name", "Без имени")
                count = booking.get("personCount", 0)
                time = dt.strftime("%H:%M")
                future_bookings.append(f"{time} — {name} ({count} чел.)")

        if not future_bookings:
            await message.answer("Бронирования на сегодня: нет записей")
        else:
            reply = "Бронирования на сегодня:\n" + "\n".join(future_bookings)
            await message.answer(reply)

    except Exception as e:
        await message.answer(f"Ошибка при получении бронирований: {e}")

# Запуск
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
