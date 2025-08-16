import os
import logging
from aiogram import Bot, Dispatcher, types, executor
import requests
from datetime import datetime, timedelta

# ВСТАВЛЕННЫЙ НАПРЯМУЮ ТОКЕН CHOICE
CHOICE_API_TOKEN = "VlFmffA-HWXnYEm-cOXRIze-FDeVdAw"

# Токен Telegram-бота (замени, если у тебя другой)
TELEGRAM_BOT_TOKEN = "8308742614:AAFnAStBXSvc3NR9wyoEMDAvSEXJmH43iwI"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Кнопки
@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Выторг за день", "Бронирование"]
    keyboard.add(*buttons)
    await message.answer("Выберите опцию:", reply_markup=keyboard)

# Выторг
@dp.message_handler(lambda message: message.text == "Выторг за день")
async def handle_turnover(message: types.Message):
    await message.answer("Функция выторга ещё не подключена.")  # Заглушка

# Бронирование
@dp.message_handler(lambda message: message.text == "Бронирование")
async def handle_booking(message: types.Message):
    await message.answer("Получаю бронирования...")

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time = now.time()

    url = f"https://open-api.choiceqr.com/api/v1/reservations"
    params = {
        "token": CHOICE_API_TOKEN,
        "start_date": today_str,
        "end_date": today_str
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not isinstance(data, list):
            await message.answer("Ошибка: неверный формат ответа от Choice API.")
            return

        bookings = []
        for item in data:
            dt_str = item.get("dateTime", "")
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone()
                if dt.date() == now.date() and dt.time() >= current_time:
                    name = item.get("customer", {}).get("name", "Без имени")
                    persons = item.get("personCount", "?")
                    time_only = dt.strftime("%H:%M")
                    bookings.append(f"{time_only} — {name} ({persons} чел.)")
            except Exception as e:
                continue  # пропускаем ошибочные даты

        if bookings:
            result = "\n".join(bookings)
        else:
            result = "Нет предстоящих броней на сегодня."

        await message.answer(f"Бронирование за сегодня:\n{result}")

    except Exception as e:
        logging.error(f"Ошибка запроса: {e}")
        await message.answer("Произошла ошибка при получении данных.")

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
