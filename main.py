import os
import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '8613693212:AAGJy4J4a27ijFuLwyeiqvVy3NjDVxaaf24'
ADMIN_PASSWORD = "shohjahon"
ADMIN_ID = None  # Birinchi marta kirganda aniqlanadi

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI ---
async def init_db():
    async with aiosqlite.connect("movies.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
        await db.commit()

# --- STATES (ADMIN UCHUN) ---
class AdminStates(StatesGroup):
    waiting_password = State()
    is_admin = State()
    adding_movie_code = State()
    adding_movie_file = State()

# --- WEB SERVER (RENDER UCHUN) ---
async def handle(request):
    return web.Response(text="Kino Bot is Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- BOT BUYRUQLARI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Kino kodini yuboring.")

@dp.message(Command("admin"))
async def admin_login(message: types.Message, state: FSMContext):
    await message.answer("Parolni kiriting:")
    await state.set_state(AdminStates.waiting_password)

@dp.message(AdminStates.waiting_password)
async def check_pass(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        global ADMIN_ID
        ADMIN_ID = message.from_user.id
        await message.answer("Xush kelibsiz Admin! Kino qo'shish uchun kodni yuboring (masalan: 1)")
        await state.set_state(AdminStates.adding_movie_code)
    else:
        await message.answer("Parol noto'g'ri!")
        await state.clear()

# Kino qo'shish: 1-qadam (Kod)
@dp.message(AdminStates.adding_movie_code)
async def get_code(message: types.Message, state: FSMContext):
    await state.update_data(m_code=message.text)
    await message.answer(f"Kod {message.text} uchun videoni yuboring.")
    await state.set_state(AdminStates.adding_movie_file)

# Kino qo'shish: 2-qadam (Video)
@dp.message(AdminStates.adding_movie_file, F.video)
async def get_video(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['m_code']
    file_id = message.video.file_id
    
    async with aiosqlite.connect("movies.db") as db:
        await db.execute("INSERT OR REPLACE INTO movies VALUES (?, ?)", (code, file_id))
        await db.commit()
    
    await message.answer(f"Tayyor! {code} kodi ostida kino saqlandi.")
    await state.set_state(AdminStates.adding_movie_code)

# Kino qidirish (Kod yozilganda)
@dp.message()
async def search_movie(message: types.Message):
    code = message.text
    async with aiosqlite.connect("movies.db") as db:
        async with db.execute("SELECT file_id FROM movies WHERE code = ?", (code,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await bot.send_video(message.chat.id, row[0], caption=f"Kino kodi: {code}")
            else:
                if not message.from_user.id == ADMIN_ID:
                    await message.answer("Bunday kodli kino topilmadi.")

async def main():
    await init_db()
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
