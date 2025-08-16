import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from datetime import datetime, timezone, timedelta

# Токены из Render (Environment Variables)
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHOICE_TOKEN = os.getenv('CHOICE_TOKEN')

# Проверка наличия токенов
if not (POSTER_TOKEN and TELEGRAM_TOKEN and CHOICE_TOKEN):
    raise ValueError("Одного или нескольких токенов нет в переменных окружения.")

# Настройка бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Клавиатура с двумя кнопками
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("📅 Виторг за день", "📋 Бронирование")

# Получение выторга официантов
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
        print(f"❌ Ошибка Poster API: {e} (ответ: {resp.text if 'resp' in locals() else 'no response'})")
        return []

# Форматирование сообщения по выторгу
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

# Обработчик "Виторг за день"
@dp.message_handler(lambda message: message.text == "📅 Виторг за день")
async def day_revenue_handler(message: types.Message):
    data = get_waiters_revenue()
    msg = format_waiters_message(data)
    await message.answer(msg, reply_markup=keyboard)

# Получение бронирований через Choice API
def fetch_choice_bookings():
    today = datetime.utcnow().date()
    date_from = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    date_to = (datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)).isoformat()
    url = "https://open-api.choiceqr.com/bookings/list"
    params = {
        "from": date_from,
        "till": date_to,
        "periodField": "bookingDt",
    }
    headers = {"Authorization": f"Bearer {CHOICE_TOKEN}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Ошибка Choice API: {e} (status: {resp.status_code if 'resp' in locals() else 'no response'})")
        print("Ответ Choice:", resp.text if 'resp' in locals() else '')
        return []

# Форматирование сообщения по бронированиям
def format_booking_message(bookings):
    if not isinstance(bookings, list) or not bookings:
        return "📋 Бронирования за сегодня:\nНемає записів."

    now_utc = datetime.now(timezone.utc)
    lines = ["📋 Бронирования на сегодня (после текущего времени):"]
    count = 0
    for b in bookings:
        dt_str = b.get("dateTime", {}).get("$date") or b.get("dateTime")
        customer = b.get("customer", {}).get("name", "Без имени")
        persons = b.get("personCount", b.get("guestsCount", "−"))
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt > now_utc:
                time_str = dt.astimezone().strftime("%H:%M")
                lines.append(f"{time_str} — {customer} ({persons} чел.)")
                count += 1
        except Exception:
            continue
    if count == 0:
        return "📋 Бронирования за сегодня:\nНемає найближчих броней."
    return "\n".join(lines)

# Обработчик "Бронирование"
@dp.message_handler(lambda message: message.text == "📋 Бронирование")
async def booking_handler(message: types.Message):
    bookings = fetch_choice_bookings()
    msg = format_booking_message(bookings)
    await message.answer(msg, reply_markup=keyboard)

# Команда /start
@dp.message_handler(commands=['start', 'report'])
async def start_cmd(message: types.Message):
    await message.answer("Натисніть кнопку нижче:", reply_markup=keyboard)

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
