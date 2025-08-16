import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

# 🔐 Переменные окружения
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
CHOICE_TOKEN = os.getenv('CHOICE_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# 🛑 Проверка переменных
if not all([POSTER_TOKEN, CHOICE_TOKEN, TELEGRAM_TOKEN]):
    raise ValueError("⛔️ Переменные окружения не заданы!")

# 🎛 Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("📅 Виторг за день"))
keyboard.add(KeyboardButton("📖 Бронирования на сегодня"))

# 🤖 Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# 📊 Получить выторг по официантам
def get_waiters_revenue():
    today = datetime.now().strftime('%Y%m%d')
    url = f'https://joinposter.com/api/dash.getWaitersSales?token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get('response', [])
    except Exception as e:
        print(f"❌ Ошибка Poster API: {e}")
        return []

# 🧾 Отформатировать сообщение выторга
def format_waiters_message(data):
    if not data:
        return "😕 Немає даних по виторгу за сьогодні."
    sorted_data = sorted(data, key=lambda x: float(x.get('revenue', 0)), reverse=True)
    lines = ["📅 Виторг за сьогодні:"]
    for i, waiter in enumerate(sorted_data, 1):
        name = waiter.get("name", "Невідомий").strip()
        revenue_uah = float(waiter.get("revenue", 0)) / 100
        formatted = f"{revenue_uah:,.0f}".replace(",", " ")
        lines.append(f"{i}. {name}: {formatted} грн")
    return "\n".join(lines)

# 📅 Получить бронирования на сегодня
def get_today_bookings():
    now = datetime.utcnow()
    from_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    till_time = now.replace(hour=23, minute=59, second=59, microsecond=999000).isoformat() + "Z"

    url = "https://open-api.choiceqr.com/api/bookings/list"
    headers = {"x-token": CHOICE_TOKEN}
    params = {
        "from": from_time,
        "till": till_time,
        "periodField": "bookingDt"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        bookings = response.json()
        print("🪵 LOG — Choice API response:", bookings)
        return bookings
    except Exception as e:
        print(f"❌ Ошибка Choice API: {e}")
        return []

# 📄 Форматирование бронирований
def format_booking_message(bookings):
    filtered = []
    now = datetime.utcnow()
    for b in bookings:
        status = b.get("status")
        dt_str = b.get("dateTime")
        customer = b.get("customer", {})
        name = customer.get("name", "Неизвестно")
        count = b.get("personCount", 0)

        if status in ("CREATED", "CONFIRMED") and dt_str:
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                # Без фильтра по времени — показываем все на сегодня
                time_str = dt.strftime('%H:%M')
                filtered.append(f"👤 {name} — {time_str}, {count} чел.")
            except Exception as e:
                print(f"⚠️ Проблема с датой: {e}")

    if not filtered:
        return "📖 Бронирования на сегодня:\nНет актуальных записей."
    result = "\n".join(filtered)
    return f"📖 Бронирования на сегодня:\n{result}"

# 🔘 Обработка кнопки Виторг
@dp.message_handler(lambda m: m.text == "📅 Виторг за день")
async def handle_revenue(m: types.Message):
    data = get_waiters_revenue()
    msg = format_waiters_message(data)
    await m.answer(msg, reply_markup=keyboard)

# 🔘 Обработка кнопки Бронирования
@dp.message_handler(lambda m: m.text == "📖 Бронирования на сегодня")
async def handle_bookings(m: types.Message):
    bookings = get_today_bookings()
    msg = format_booking_message(bookings)
    await m.answer(msg, reply_markup=keyboard)

# 🔘 Команда /start
@dp.message_handler(commands=["start"])
async def cmd_start(m: types.Message):
    await m.answer("👋 Выберите действие ниже:", reply_markup=keyboard)

# ▶️ Старт
if __name__ == '__main__':
    executor.start_polling(dp)
