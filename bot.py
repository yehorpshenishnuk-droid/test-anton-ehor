import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))
CHOICE_TOKEN = "GAfIFfG-RCLDRXU-WmmFvSD-IfDGFMS"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("\ud83d\udcb0 \u0412\u0438\u0442\u043e\u0440\u0433 \u0437\u0430 \u0434\u0435\u043d\u044c")],
        [KeyboardButton("\ud83d\uddd5\ufe0f \u0411\u0440\u043e\u043d\u044e\u0432\u0430\u043d\u043d\u044f")],
    ]
)

def get_waiters_sales():
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://joinposter.com/api/dash.getWaitersSales?token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get("response", [])
    except Exception as e:
        print(f"Poster API error: {e}")
        return []

def build_sales_report():
    sales = get_waiters_sales()
    report = f"\ud83d\udcc5 \u0412\u0438\u0442\u043e\u0440\u0433 \u0437\u0430 \u0441\u044c\u043e\u0433\u043e\u0434\u043d\u0456:\n"
    if not sales:
        return report + "\u041d\u0435\u043c\u0430\u0454 \u0434\u0430\u043d\u0438\u0445."
    for i, s in enumerate(sales, 1):
        name = s.get("name", "\u041d\u0435\u0432\u0456\u0434\u043e\u043c\u0438\u0439").strip()
        revenue = int(float(s.get("revenue", 0)))
        report += f"{i}. {name}: {revenue} грн\n"
    return report

def get_bookings():
    now = datetime.utcnow()
    from_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    to_time = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"
    url = (
        f"https://open-api.choiceqr.com/api/bookings/list"
        f"?from={from_time}&till={to_time}&periodField=bookingDt"
    )
    try:
        headers = {"Authorization": f"Bearer {CHOICE_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Choice API error: {e}")
        return []

def build_booking_report():
    bookings = get_bookings()
    if not isinstance(bookings, list):
        return "\ud83d\udcc5 \u0411\u0440\u043e\u043d\u0456: \u043f\u043e\u043c\u0438\u043b\u043a\u0430 API"
    report = f"\ud83d\udcc5 \u0421\u044c\u043e\u0433\u043e\u0434\u043d\u0456\u0448\u043d\u0456 \u0431\u0440\u043e\u043d\u0456:\n"
    if not bookings:
        return report + "\u041d\u0435\u043c\u0430\u0454 \u0431\u0440\u043e\u043d\u0435\u0439."
    for i, b in enumerate(bookings, 1):
        people = b.get("personCount", "?")
        dt = b.get("dateTime", {}).get("$date")
        if dt:
            dt_fmt = datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%H:%M")
        else:
            dt_fmt = "\u043d\u0435\u0432\u0456\u0434\u043e\u043c\u043e"
        report += f"{i}. \u0411\u0440\u043e\u043d\u044c: {people} \u043e\u0441., \u0447\u0430\u0441: {dt_fmt}\n"
    return report

@dp.message_handler(lambda message: message.text == "\ud83d\udcb0 \u0412\u0438\u0442\u043e\u0440\u0433 \u0437\u0430 \u0434\u0435\u043d\u044c")
async def vitorg_handler(message: types.Message):
    msg = build_sales_report()
    await message.answer(msg, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "\ud83d\uddd5\ufe0f \u0411\u0440\u043e\u043d\u044e\u0432\u0430\u043d\u043d\u044f")
async def booking_handler(message: types.Message):
    msg = build_booking_report()
    await message.answer(msg, reply_markup=keyboard)

async def on_startup(dp):
    print("Bot started")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
