import logging
import random
import requests
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# 1. BOT TOKEN
API_TOKEN = '8613693212:AAGPxSce8tQEHI-iSLR3YGJalr40PdyQFSc'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RENDER UCHUN WEB SERVER (BOT O'CHIB QOLMASLIGI UCHUN) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render portni o'zi taqdim etadi, bo'lmasa 8080 ishlatiladi
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
# ---------------------------------------------------------

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Salom! Men Lexica bazasidan rasm qidirib beraman. 🚀\n"
                         "Menga inglizcha so'z yozing (masalan: 'Cyberpunk city').")

@dp.message()
async def generate_image(message: types.Message):
    prompt = message.text
    wait_msg = await message.answer("🔍 Rasmlar bazasidan qidiryapman...")

    try:
        url = f"https://lexica.art/api/v1/search?q={prompt}"
        response = requests.get(url)
        data = response.json()

        if data.get('images'):
            random_image = random.choice(data['images'])
            image_url = random_image['src']

            await bot.send_photo(
                chat_id=message.chat.id,
                photo=image_url,
                caption=f"✅ Natija: {prompt}\n🌟 Sifat: Ultra HD"
            )
            await wait_msg.delete()
        else:
            await message.answer("❌ Afsuski, bunday rasm topilmadi.")

    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi.")
        logging.error(f"Xatolik: {e}")

async def main():
    # Web serverni fonda ishga tushiramiz
    asyncio.create_task(start_web_server())
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi! ✅")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")