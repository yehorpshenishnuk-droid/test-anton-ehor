import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# Переменные окружения
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("📅 Виторг за день")]
    ]
)

# Telegram
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Получение выручки по официантам
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
        print(f"❌ Помилка Poster API: {e}")
        return []

# Форматирование отчёта
def format_waiters_message(data):
    if not data:
        return "😕 Немає даних по виторгу за сьогодні."

    # Сортируем по выручке
    sorted_data = sorted(data, key=lambda x: float(x.get('revenue', 0)), reverse=True)

    lines = ["📅 Виторг за сьогодні:"]
    for i, waiter in enumerate(sorted_data, start=1):
        name = waiter.get("name", "Невідомий").strip()
        revenue_cop = float(waiter.get("revenue", 0))  # в копейках
        revenue_uah = revenue_cop / 100
        formatted = f"{revenue_uah:,.0f}".replace(",", " ")
        lines.append(f"{i}. {name}: {formatted} грн")

    return "\n".join(lines)

# Обработка кнопки
@dp.message_handler(lambda message: message.text == "📅 Виторг за день")
async def day_revenue_handler(message: types.Message):
    data = get_waiters_revenue()
    msg = format_waiters_message(data)
    await message.answer(msg, reply_markup=keyboard)

# Обработка /start
@dp.message_handler(commands=['start', 'report'])
async def start_cmd(message: types.Message):
    await message.answer("Натисніть кнопку нижче, щоб дізнатись виторг по кожному офіціанту 👇", reply_markup=keyboard)

# Старт
if __name__ == '__main__':
    executor.start_polling(dp)
