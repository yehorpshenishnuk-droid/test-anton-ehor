import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

# ⛳️ Переменные окружения
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
CHOICE_TOKEN = os.getenv('CHOICE_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not all([POSTER_TOKEN, CHOICE_TOKEN, TELEGRAM_TOKEN]):
    raise ValueError("⛔️ Нет одной из переменных окружения: POSTER_TOKEN, CHOICE_TOKEN, TELEGRAM_TOKEN")

# 🎛 Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("📅 Виторг за день"))
keyboard.add(KeyboardButton("📖 Бронирования"))

# 🔹 Telegram
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# 📌 Виторг по официантам
def get_waiters_revenue():
    today = datetime.now().strftime('%Y%m%d')
    url = (
        f'https://joinposter.com/api/dash.getWaitersSales?'
        f'token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get('response', [])
    except Exception as e:
        print(f"❌ Ошибка Poster API: {e}")
        return []

def format_waiters_message(data):
    if not data:
        return "😕 Немає даних по виторгу за сьогодні."

    sorted_data = sorted(data, key=lambda x: float(x.get('revenue', 0)), reverse=True)
    lines = ["📅 Виторг за сьогодні:"]
    for i, waiter in enumerate(sorted_data, start=1):
        name = waiter.get("name", "Невідомий").strip()
        revenue_cop = float(waiter.get("revenue", 0))
        revenue_uah = revenue_cop / 100
        formatted = f"{revenue_uah:,.0f}".replace(",", " ")
        lines.append(f"{i}. {name}: {formatted} грн")

    return "\n".join(lines)

# 📌 Получение бронирований из Choice
def get_today_bookings():
    now = datetime.utcnow()
    from_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    till_time = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    url = "https://open-api.choiceqr.com/api/bookings/list"
    headers = {
        "accept": "application/json",
        "x-token": CHOICE_TOKEN
    }
    params = {
        "from": from_time,
        "till": till_time,
        "periodField": "bookingDt",
        "perPage": 100
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        bookings = resp.json()
        # Фильтрация
        future = []
        for b in bookings:
            if b.get("status") not in ["CREATED", "CONFIRMED"]:
                continue
            dt_str = b.get("dateTime", {}).get("date")
            if not dt_str:
                continue
            dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt_obj > datetime.utcnow():
                future.append(b)
        return future
    except Exception as e:
        print(f"❌ Ошибка при получении броней: {e}")
        return []

def format_booking_message(bookings):
    if not bookings:
        return "📖 Бронирования на сегодня:\nНет актуальных записей."

    lines = ["📖 Бронирования на сегодня:"]
    for b in bookings:
        name = b.get("customer", {}).get("name", "Без имени")
        person_count = b.get("personCount", 0)
        dt_str = b.get("dateTime", {}).get("date")
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            time = dt.strftime("%H:%M")
        except:
            time = "??:??"
        lines.append(f"🕒 {time} | 👤 {name} | 👥 {person_count} чел.")

    return "\n".join(lines)

# 📌 Обработчики кнопок
@dp.message_handler(lambda msg: msg.text == "📅 Виторг за день")
async def handle_revenue(msg: types.Message):
    data = get_waiters_revenue()
    reply = format_waiters_message(data)
    await msg.answer(reply, reply_markup=keyboard)

@dp.message_handler(lambda msg: msg.text == "📖 Бронирования")
async def handle_bookings(msg: types.Message):
    bookings = get_today_bookings()
    reply = format_booking_message(bookings)
    await msg.answer(reply, reply_markup=keyboard)

@dp.message_handler(commands=['start', 'menu'])
async def start_menu(msg: types.Message):
    await msg.answer("👋 Выберите действие:", reply_markup=keyboard)

# ▶️ Старт
if __name__ == "__main__":
    executor.start_polling(dp)
