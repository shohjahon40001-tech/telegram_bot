import os
import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '8026117592:AAE0sN7zSo1FGOpqC5_Zc_DTg-L1T_LrMS8'
ADMIN_PASSWORD = "Shohjahon"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI (ODDIY SQLITE) ---
def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
    conn.commit()
    conn.close()

class AdminStates(StatesGroup):
    waiting_password = State()
    adding_movie_code = State()
    adding_movie_file = State()

# --- WEB SERVER (RENDER UCHUN) ---
async def handle(request):
    return web.Response(text="Bot is running...")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

# --- BOT FUNKSIYALARI ---
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
        await message.answer("Xush kelibsiz Admin! Kino kodini yuboring (masalan: 1)")
        await state.set_state(AdminStates.adding_movie_code)
    else:
        await message.answer("Parol noto'g'ri!")
        await state.clear()

@dp.message(AdminStates.adding_movie_code)
async def get_code(message: types.Message, state: FSMContext):
    await state.update_data(m_code=message.text)
    await message.answer(f"Kod {message.text} uchun videoni yuboring.")
    await state.set_state(AdminStates.adding_movie_file)

@dp.message(AdminStates.adding_movie_file, F.video)
async def get_video(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['m_code']
    file_id = message.video.file_id
    
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?)", (code, file_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"Tayyor! {code} kodi ostida saqlandi.")
    await state.set_state(AdminStates.adding_movie_code)

@dp.message()
async def search_movie(message: types.Message):
    code = message.text
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        await bot.send_video(message.chat.id, row[0], caption=f"Kino kodi: {code}")

async def main():
    init_db()
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
