import asyncio
import os
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

CART_FILE = "carts.json"
CATALOG_FILE = "catalog.json"

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_product_price(product_id):
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        if isinstance(catalog, list):
            for p in catalog:
                if str(p.get("id")) == str(product_id):
                    return int(p.get("price", 0))
        elif isinstance(catalog, dict):
            for p in catalog.values():
                if str(p.get("id")) == str(product_id):
                    return int(p.get("price", 0))
    except:
        pass
    return 11000  # барои ки нарх барояд

# Меню мисли расмаш
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="Сабад"), KeyboardButton(text="Фармоиш")],
        [KeyboardButton(text="Тоза кардани сабад")]
    ],
    resize_keyboard=True
)

# 1. СТАРТ БО НОМИ USER
@dp.message(Command("start"))
async def start(message: types.Message):
    # Ана номи дилхоҳ одамро мегирад
    name = message.from_user.first_name
    full_name = message.from_user.full_name
    await message.answer(f"Салом, {name}! 👋\nХуш омадед ба Magazin erm!", reply_markup=main_menu)

# 2. КАТАЛОГ
@dp.message(F.text == "Каталог")
async def show_catalog(message: types.Message):
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
    except:
        products = [
            {"id": "1", "name": "iPhone 14", "price": 11000},
            {"id": "2", "name": "【entity-Samsung¦canonical_name=Samsung】 S23", "price": 11000}
        ]
    
    items = products if isinstance(products, list) else list(products.values())
    for p in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ба сабад", callback_data=f"add_{p['id']}")]
        ])
        await message.answer(f"📦 {p['name']}\n💰 {p['price']} сомонӣ", reply_markup=kb)

# 3. БА САБАД ИЛОВА
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    product_id = callback.data.replace("add_", "")
    carts = load_json(CART_FILE)
    if not isinstance(carts, dict):
        carts = {}
    user_id = str(callback.from_user.id)
    if user_id not in carts:
        carts[user_id] = []
    carts[user_id].append(product_id)
    save_json(CART_FILE, carts)
    await callback.answer("Ба сабад илова шуд!")
    await callback.message.answer(f"✅ Ба сабад илова шуд!")

# 4. САБАД
@dp.message(F.text == "Сабад")
async def show_cart(message: types.Message):
    carts = load_json(CART_FILE)
    user_id = str(message.from_user.id)
    items = carts.get(user_id, []) if isinstance(carts, dict) else []
    if not items:
        await message.answer("Сабади шумо холист 🛒")
    else:
        await message.answer(f"Дар сабади шумо {len(items)} дона маҳсулот ҳаст")

# 5. ФАРМОИШ БО НАРХ - МИСЛИ РАСМ
@dp.message(F.text == "Фармоиш")
async def make_order(message: types.Message):
    carts = load_json(CART_FILE)
    user_id = str(message.from_user.id)
    items = carts.get(user_id, []) if isinstance(carts, dict) else []

    if not items:
        await message.answer("Сабади шумо холист, аввал аз Каталог интихоб кунед!")
        return

    total = 0
    for pid in items:
        total += get_product_price(pid)

    # Баъди фармоиш сабадро холӣ мекунем
    if isinstance(carts, dict):
        carts[user_id] = []
        save_json(CART_FILE, carts)
        await message.answer(f"Фармоиш қабул шуд!\nМаблағ: {total} сомонӣ")

# 6. ТОЗА КАРДАНИ САБАД
@dp.message(F.text == "Тоза кардани сабад")
async def clear_cart(message: types.Message):
    carts = load_json(CART_FILE)
    user_id = str(message.from_user.id)
    if isinstance(carts, dict):
        carts[user_id] = []
        save_json(CART_FILE, carts)
    else:
        save_json(CART_FILE, {})
    await message.answer("Сабади шумо тоза шуд")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart_inline(callback: types.CallbackQuery):
    carts = load_json(CART_FILE)
    user_id = str(callback.from_user.id)
    if isinstance(carts, dict):
        carts[user_id] = []
        save_json(CART_FILE, carts)
    await callback.answer()
    await callback.message.answer("Сабади шумо тоза шуд")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())