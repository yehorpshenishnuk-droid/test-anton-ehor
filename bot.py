import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))
CHOICE_API_TOKEN = os.getenv('CHOICE_API_TOKEN')

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("📊 Виторг по офіціантах")],
        [KeyboardButton("📅 Бронювання")],
    ]
)

# 📌 Poster API — по официантам
def get_waiters_sales():
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
        print(f"Poster API error: {e}")
        return []

def build_waiters_report():
    data = get_waiters_sales()
    if not data:
        return "Немає даних про виторг."

    report = f'📊 Виторг за сьогодні:\n'
    for idx, waiter in enumerate(data, 1):
        name = waiter.get("name", "Невідомий").strip()
        amount = int(float(waiter.get("revenue", 0)))  # revenue = сумма
        report += f"{idx}. {name}: {amount} грн\n"
    return report

# 📌 Choice API — по бронюванням
def get_today_bookings():
    date = datetime.utcnow().strftime("%Y-%m-%d")
    from_time = f"{date}T00:00:00.000Z"
    to_time = f"{date}T23:59:59.999Z"

    url = "https://open-api.choiceqr.com/bookings/list"
    headers = {
        "Authorization": f"Bearer {CHOICE_API_TOKEN}"
    }
    params = {
        "from": from_time,
        "till": to_time
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Choice API error: {e}")
        return []

def build_booking_report():
    bookings = get_today_bookings()
    if not bookings:
        return "Бронювань на сьогодні немає."

    report = f"📅 Бронювання на сьогодні:\n"
    for idx, booking in enumerate(bookings, 1):
        time = booking.get("dateTime", {}).get("start", "")
        time_formatted = datetime.fromisoformat(time).strftime('%H:%M') if time else "??:??"
        guests = booking.get("personCount", 0)
        report += f"{idx}. 🕒 {time_formatted} • 👥 {guests} ос.\n"
    return report

# 🕓 Планувальник
async def send_reports():
    await bot.send_message(GROUP_CHAT_ID, build_waiters_report(), reply_markup=keyboard)

def setup_jobs():
    scheduler.add_job(send_reports, 'cron', hour=15, minute=0)
    scheduler.start()

# 📩 Обробка повідомлень
@dp.message_handler(lambda message: message.text == "📊 Виторг по офіціантах")
async def waiter_report(message: types.Message):
    await message.answer(build_waiters_report(), reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "📅 Бронювання")
async def booking_report(message: types.Message):
    await message.answer(build_booking_report(), reply_markup=keyboard)

async def on_startup(dp):
    setup_jobs()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
