import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# === Переменные окружения ===
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
CHOICE_TOKEN = os.getenv('CHOICE_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not all([POSTER_TOKEN, CHOICE_TOKEN, TELEGRAM_TOKEN]):
    raise ValueError("Одного или нескольких токенов нет в переменных окружения.")

# === Клавиатура ===
keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("📅 Виторг за день")],
        [KeyboardButton("📖 Бронирование")]
    ]
)

# === Telegram ===
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# === Выручка по официантам ===
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

@dp.message_handler(lambda message: message.text == "📅 Виторг за день")
async def day_revenue_handler(message: types.Message):
    data = get_waiters_revenue()
    msg = format_waiters_message(data)
    await message.answer(msg, reply_markup=keyboard)

# === Бронирования ===
def get_today_bookings():
    from_zone = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    to_zone = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999000).isoformat() + "Z"

    url = "https://open-api.choiceqr.com/api/bookings/list"
    headers = {
        "Authorization": f"Bearer {CHOICE_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "from": from_zone,
        "till": to_zone,
        "periodField": "bookingDt",
        "perPage": 100,
        "page": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        print("📥 RAW BOOKINGS:", data)  # для логов
        return data.get("response", [])
    except Exception as e:
        print(f"❌ Ошибка Choice API: {e}")
        return []

def format_bookings(bookings):
    if not bookings:
        return "📖 Бронирования на сегодня:\nНет записей."

    lines = ["📖 Бронирования на сегодня:"]
    for b in bookings:
        name = b.get("customer", {}).get("name", "Без имени")
        iso_time = b.get("dateTime")
        count = b.get("personCount", 0)
        status = b.get("status", "-")

        time_part = iso_time[11:16] if iso_time else "??:??"
        lines.append(f"👤 {name} — {time_part} — {count} чел. [{status}]")

    return "\n".join(lines)

@dp.message_handler(lambda message: message.text == "📖 Бронирование")
async def booking_handler(message: types.Message):
    bookings = get_today_bookings()
    msg = format_bookings(bookings)
    await message.answer(msg, reply_markup=keyboard)

# === Команда /start ===
@dp.message_handler(commands=['start', 'report'])
async def start_cmd(message: types.Message):
    await message.answer("Выберите действие 👇", reply_markup=keyboard)

# === Старт бота ===
if __name__ == '__main__':
    executor.start_polling(dp)
