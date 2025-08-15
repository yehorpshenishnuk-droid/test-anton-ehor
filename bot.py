import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# Переменные окружения
POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

# Клавиатура — только одна кнопка
keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("📅 Виторг за день")]
    ]
)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Получение выручки за день
def get_day_revenue():
    today = datetime.now().strftime('%Y%m%d')
    url = (
        f'https://joinposter.com/api/dash.getSales?'
        f'token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        sales = resp.json().get('response', [])
        total = sum(float(s.get('total_sum', 0)) for s in sales)
        return total
    except Exception as e:
        print(f"❌ Ошибка Poster API: {e}")
        return None

# Обработка кнопки
@dp.message_handler(lambda message: message.text == "📅 Виторг за день")
async def day_revenue_handler(message: types.Message):
    total = get_day_revenue()
    if total is not None:
        formatted = f"{total:,.0f}".replace(",", " ")
        await message.answer(f"📅 Виторг за сьогодні: {formatted} грн", reply_markup=keyboard)
    else:
        await message.answer("❌ Не вдалося отримати виторг за день", reply_markup=keyboard)

# Обработка /start
@dp.message_handler(commands=['start', 'report'])
async def start_cmd(message: types.Message):
    await message.answer("👋 Натисніть кнопку нижче, щоб дізнатись виторг за день:", reply_markup=keyboard)

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp)
