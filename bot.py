import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timezone, timedelta

# --- Зависимости от Environment / Апи-токены ---
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

# Токен Choice (прямо вставлен как ты просил)
CHOICE_API_TOKEN = "VlFmffA-HWXnYEm-cOXRIze-FDeVdAw"

# --- Telegram Bot и Dispatcher ---
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# --- Клавиатура с двумя кнопками ---
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Виторг за день"))
keyboard.add(KeyboardButton("Бронирование"))

# --- Poster: выторг по официантам ---
def fetch_waiters_sales():
    today = datetime.now().strftime('%Y%m%d')
    url = (
        f'https://joinposter.com/api/dash.getWaitersSales?'
        f'token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get('response', [])
    except Exception as e:
        print(f"[Poster API error] {e}")
        return []

def format_waiters_report(data):
    if not data:
        return f"Виторг за {datetime.now():%d.%m.%Y}:\nНет данных."
    rows = sorted(data, key=lambda x: float(x.get('revenue', 0)), reverse=True)
    lines = [f"Виторг за {datetime.now():%d.%m.%Y}:"]
    for i, row in enumerate(rows, 1):
        name = row.get('name', 'Невідомий').strip()
        rev = int(float(row.get('revenue', 0)))
        lines.append(f"{i}. {name}: {rev} грн")
    return "\n".join(lines)

# --- Choice: бронирования за сегодня ---
def fetch_today_bookings():
    # Формируем диапазон с 00:00 до 23:59 UTC
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"
    url = "https://open-api.choiceqr.com/bookings/list"
    headers = {"Authorization": f"Bearer {CHOICE_API_TOKEN}"}
    params = {"from": start, "till": end, "periodField": "bookingDt"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()  # ожидаем список бронирований
    except Exception as e:
        print(f"[Choice API error] {e}")
        return []

def format_booking_report(data):
    if not isinstance(data, list) or not data:
        return "Бронирование за сегодня:\nНет записей."
    lines = [f"Бронирование на сегодня ({datetime.now():%d.%m.%Y}):"]
    # Конверсия UTC -> Kyiv (UTC+3 летом)
    kyiv_tz = timezone(timedelta(hours=3))
    for i, b in enumerate(data, 1):
        cust = b.get('customer', {}).get('name', 'Клиент')
        dt_raw = b.get('dateTime', {}).get('$date', "")
        person_count = b.get('personCount', 0)
        try:
            dt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
            dt_local = dt.astimezone(kyiv_tz)
            time_str = dt_local.strftime("%H:%M")
        except Exception:
            time_str = dt_raw[:16] if dt_raw else "??:??"
        lines.append(f"{i}. {cust} — ⏰ {time_str} — 👥 {person_count}")
    return "\n".join(lines)

# --- Handlers ---
@dp.message_handler(commands=['start', 'report'])
async def handle_start(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "Виторг за день")
async def handler_sales(message: types.Message):
    report = format_waiters_report(fetch_waiters_sales())
    await message.answer(report, reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "Бронирование")
async def handler_booking(message: types.Message):
    bookings = fetch_today_bookings()
    report = format_booking_report(bookings)
    await message.answer(report, reply_markup=keyboard)

# --- Startup ---
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    print("[Bot started, polling activated]")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
