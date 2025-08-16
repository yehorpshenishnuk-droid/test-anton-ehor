import logging
import os
from aiogram import Bot, Dispatcher, types, executor
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные окружения
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
POSTER_TOKEN = os.getenv("POSTER_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
CHOICE_API_TOKEN = os.getenv("CHOICE_API_TOKEH")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Выторг за день", "Бронирование")
    await message.answer("Выберите опцию:", reply_markup=keyboard)

# Получение выторга из Poster
@dp.message_handler(lambda message: message.text == "Выторг за день")
async def revenue_handler(message: types.Message):
    try:
        now = datetime.now(ZoneInfo("Europe/Kyiv"))
        today = now.strftime("%Y-%m-%d")

        url = f"https://joinposter.com/api/dash.getTurnover?token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}"
        response = requests.get(url)
        data = response.json()

        if "response" not in data or not data["response"]:
            await message.answer("Выторг не найден или пустой.")
            return

        turnover_data = data["response"][0]
        revenue = float(turnover_data.get("turnover", 0)) / 100  # копейки → гривны

        await message.answer(f"Выторг за {today}: 💸 {revenue:.2f} грн")

    except Exception as e:
        logging.exception("Ошибка при получении выторга:")
        await message.answer("Произошла ошибка при получении выторга.")

# Получение бронирований из Choice
@dp.message_handler(lambda message: message.text == "Бронирование")
async def booking_handler(message: types.Message):
    await message.answer("Получаю бронирования...")

    try:
        now = datetime.now(ZoneInfo("Europe/Kyiv"))
        today = now.strftime("%Y-%m-%d")

        headers = {
            "Authorization": f"Bearer {CHOICE_API_TOKEN}"
        }

        url = "https://api.choiceqr.com/api/v1/bookings"
        params = {
            "date": today
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if not isinstance(data, list):
            await message.answer("Ошибка: неверный формат ответа от Choice API.")
            return

        future_bookings = []
        for booking in data:
            dt = datetime.fromisoformat(booking["dateTime"])
            if dt > now:
                name = booking["customerName"]
                guests = booking["guestsCount"]
                time = dt.strftime("%H:%M")
                future_bookings.append(f"👤 {name} — {time} — {guests} чел.")

        if future_bookings:
            result = "\n".join(future_bookings)
        else:
            result = "Нет будущих бронирований на сегодня."

        await message.answer(f"📅 Бронирования на {today}:\n{result}")

    except Exception as e:
        logging.exception("Ошибка при получении бронирований:")
        await message.answer("Произошла ошибка при получении бронирований.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
