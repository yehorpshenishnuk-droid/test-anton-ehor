import os
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

POSTER_TOKEN = os.getenv('POSTER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

CATEGORIES = {
    '4': 'ЧЕБУРЕКИ',
    '15': 'ЯНТИКИ',
}
EXTRA_CATEGORIES = {
    '33': 'ПИДЕ',
    '13': 'МЯСНІ СТРАВИ',
    '154': 'ПЛОВ',
}

def get_categories_sales():
    today = datetime.now().strftime('%Y%m%d')
    url = (
        f'https://joinposter.com/api/dash.getCategoriesSales?'
        f'token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get('response', [])
    except Exception as e:
        print(f"Ошибка Poster API: {e}")
        return []

def get_products_sales():
    today = datetime.now().strftime('%Y%m%d')
    url = (
        f'https://joinposter.com/api/dash.getProductsSales?'
        f'token={POSTER_TOKEN}&dateFrom={today}&dateTo={today}'
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get('response', [])
    except Exception as e:
        print(f"Ошибка Poster API: {e}")
        return []

def get_pelmeni_sales():
    return get_products_sales()

def build_main_report():
    report = f'Звіт за {datetime.now().strftime("%d.%m.%Y")}:\n'
    categories_sales = get_categories_sales()
    products_sales = get_products_sales()
    total_qty = 0
    main_lines = []
    extra_lines = []

    for cat_id, cat_name in CATEGORIES.items():
        cat_sales = next((cat for cat in categories_sales if str(cat.get('category_id')) == str(cat_id)), None)
        qty = int(float(cat_sales.get('count', 0))) if cat_sales else 0
        total_qty += qty
        main_lines.append(f'🍽️ {cat_name}: {qty} шт')
    main_lines.append(f'ИТОГО: {total_qty} шт')

    for cat_id, cat_name in EXTRA_CATEGORIES.items():
        if cat_id == '154':  # Плов — продукт, а не категория
            prod = next((p for p in products_sales if str(p.get('product_id')) == '154'), None)
            qty = int(float(prod.get('count', 0))) if prod else 0
            extra_lines.append(f'🍽️ {cat_name}: {qty} шт')
        else:
            cat_sales = next((cat for cat in categories_sales if str(cat.get('category_id')) == str(cat_id)), None)
            qty = int(float(cat_sales.get('count', 0))) if cat_sales else 0
            extra_lines.append(f'🍽️ {cat_name}: {qty} шт')

    report += '\n'.join(main_lines) + '\n\n' + '\n'.join(extra_lines)
    return report

def build_pelmeni_report():
    sales = get_pelmeni_sales()
    report = f'Звіт за {datetime.now().strftime("%d.%m.%Y")}:\n\n'

    zal_products = {
        '497': "ПЕЛЬМЕНІ ТЕЛЯ",
        '521': "ПЕЛЬМЕНІ КУРК",
    }

    frozen_products = {
        '493': "ПЕЛЬМЕНІ КУРКА",
        '510': "ПЕЛЬМЕНІ СВИН/ТЕЛЯ",
        '495': "ПЕЛЬМЕНІ ТЕЛЯ",
    }

    # Пельмені в зал
    report += "🥟 ПЕЛЬМЕНІ В ЗАЛ:\n"
    for product_id, name in zal_products.items():
        prod = next((p for p in sales if str(p.get('product_id')) == str(product_id)), None)
        qty = int(float(prod.get('count', 0))) if prod else 0
        report += f"{name}: {qty} шт\n"

    # Заморожені
    report += "\n❄️ ЗАМОРОЖЕНІ ПЕЛЬМЕНІ:\n"
    for product_id, name in frozen_products.items():
        prod = next((p for p in sales if str(p.get('product_id')) == str(product_id)), None)
        qty = int(float(prod.get('count', 0))) if prod else 0
        report += f"❄️ {name}: {qty} шт\n"

    return report

keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False,
    keyboard=[
        [KeyboardButton("🔥 Звіт гаряч")],
        [KeyboardButton("🥟 Звіт пельмені")],
    ]
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

async def send_report():
    msg = build_main_report()
    await bot.send_message(GROUP_CHAT_ID, msg, reply_markup=keyboard)

async def send_pelmeni_report():
    msg = build_pelmeni_report()
    await bot.send_message(GROUP_CHAT_ID, msg, reply_markup=keyboard)

def setup_jobs():
    scheduler.add_job(send_report, 'cron', hour=15, minute=0)
    scheduler.add_job(send_report, 'cron', hour=19, minute=1)
    scheduler.add_job(send_pelmeni_report, 'cron', hour=19, minute=2)
    scheduler.start()

@dp.message_handler(lambda message: message.text == "🔥 Звіт гаряч")
async def hot_report_handler(message: types.Message):
    msg = build_main_report()
    await message.answer(msg, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🥟 Звіт пельмені")
async def pelmeni_report_handler(message: types.Message):
    msg = build_pelmeni_report()
    await message.answer(msg, reply_markup=keyboard)

@dp.message_handler(commands=['report'])
async def manual_report(message: types.Message):
    msg = build_main_report()
    await message.answer(msg, reply_markup=keyboard)

async def on_startup(dp):
    setup_jobs()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
