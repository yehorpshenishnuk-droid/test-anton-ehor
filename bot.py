import logging
import os
from aiogram import Bot, Dispatcher, types, executor
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Получение токенов из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
POSTER_TOKEN = os.getenv("POSTER_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
CHOICE_API_TOKEN = os.getenv("CHOICE_API_TOKEH")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Выторг за день", "Бронирование")
    await message.answer("Выберите опцию:", reply_markup=keyboard)

# Кнопка "Выторг за день"
@dp.message_handler(lambda message: message.text == "Выторг за день")
async def handle_revenue(message: types.Message):
    await message.answer("Функция выторга ещё не подключена.")

# Кнопка "Бронирование"
@dp.message_handler(lambda message: message.text == "Бронирование")
async def handle_booking(message: types.Message):
    await message.answer("Получаю бронирования...")

    try:
        # Текущая дата и время в Киеве
        now = datetime.now(ZoneInfo("Europe/Kyiv"))
        today_date = now.strftime("%Y-%m-%d")

        headers = {
            "Authorization": f"Bearer {CHOICE_API_TOKEN}"
        }

        url = "https://api.choiceqr.com/api/v1/bookings"
        params = {
            "date": today_date
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if not isinstance(data, list):
            await message.answer("Ошибка: неверный формат ответа от Choice API.")
            return

        bookings = []

        for booking in data:
            booking_time = datetime.fromisoformat(booking["dateTime"])
            if booking_time > now:
                name = booking["customerName"]
                time = booking_time.strftime("%H:%M")
                guests = booking["guestsCount"]
                bookings.append(f"👤 {name} — {time} — {guests} чел.")

        if bookings:
            response_text = "\n".join(bookings)
        else:
            response_text = "Нет записей."

        await message.answer(f"Бронирование за сегодня:\n{response_text}")

    except Exception as e:
        logging.exception("Ошибка при получении бронирований")
        await message.answer("Произошла ошибка при получении данных.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
