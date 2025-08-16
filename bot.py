import logging
import requests
from aiogram import Bot, Dispatcher, types, executor

# ==== НАСТРОЙКИ ====
API_TOKEN = 'ВАШ_ТОКЕН_БОТА'
CHOICE_TOKEN = 'ВАШ_CHOICE_API_ТОКЕН'
CHOICE_HEADERS = {
    'Authorization': f'Bearer {CHOICE_TOKEN}',
    'Content-Type': 'application/json'
}
ORG_ID = 'ВАШ_ORG_ID'  # Замените на ваш ID организации
VENUE_ID = 'ВАШ_VENUE_ID'  # Замените на ID точки

# ==== ЛОГИ ====
logging.basicConfig(level=logging.INFO)

# ==== ИНИЦИАЛИЗАЦИЯ ====
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ==== КНОПКИ ====
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("Бронирование", "Выторг за день")


# ==== ОБРАБОТКА /start ====
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=keyboard)


# ==== ВЫТОРГ ЗА ДЕНЬ ====
@dp.message_handler(lambda message: message.text == "Выторг за день")
async def handle_revenue(message: types.Message):
    await message.answer("Получаю выторг...")

    url = f"https://api.choiceqr.com/api/integration/v1/analytics/revenue?organization_id={ORG_ID}&venue_id={VENUE_ID}"
    try:
        response = requests.get(url, headers=CHOICE_HEADERS)
        data = response.json()

        if response.status_code == 200 and "revenue" in data:
            revenue = data["revenue"]
            await message.answer(f"Выторг за день: {revenue} ₽")
        else:
            await message.answer("Ошибка: неверный формат ответа от Choice API.")
    except Exception as e:
        await message.answer(f"Ошибка при получении выторга: {e}")


# ==== БРОНИРОВАНИЕ ====
@dp.message_handler(lambda message: message.text == "Бронирование")
async def handle_bookings(message: types.Message):
    await message.answer("Получаю бронирования...")

    url = f"https://api.choiceqr.com/api/integration/v1/venues/{VENUE_ID}/bookings"
    try:
        response = requests.get(url, headers=CHOICE_HEADERS)
        data = response.json()

        if response.status_code == 200 and isinstance(data, list):
            count = len(data)
            await message.answer(f"Всего бронирований: {count}")
        else:
            await message.answer("Ошибка: неверный формат ответа от Choice API.")
    except Exception as e:
        await message.answer(f"Ошибка при получении бронирований: {e}")


# ==== ЗАПУСК ====
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
