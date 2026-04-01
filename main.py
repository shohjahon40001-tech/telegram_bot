import telebot
import sqlite3
from telebot import types

# --- SOZLAMALAR ---
API_TOKEN = '8026117592:AAF80AiISqgB6VyqrSh2fdc_qKUKmuT6CHY'
ADMIN_ID = 8453381252

bot = telebot.TeleBot(API_TOKEN)

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT, name TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS channels (channel_id TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

# --- OBUNANI TEKSHIRISH ---
def check_all_subs(user_id):
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM channels")
    channels = cursor.fetchall()
    conn.close()
    
    not_subbed = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch[0], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subbed.append(ch[0])
        except Exception:
            # Agar bot kanalga admin bo'lmasa yoki kanal username xato bo'lsa
            not_subbed.append(ch[0])
    return not_subbed

# --- START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    
    not_subbed = check_all_subs(message.from_user.id)
    
    if not not_subbed:
        bot.send_message(message.chat.id, "👋 Salom! Kino kodini yuboring:")
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        for ch_id in not_subbed:
            clean_username = ch_id.replace('@', '')
            # Kompyuter va Telefon uchun eng qulay havola formati:
            link = f"tg://resolve?domain={clean_username}"
            btn = types.InlineKeyboardButton(f"📢 Kanalga a'zo bo'lish", url=link)
            kb.add(btn)
        
        kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:", reply_markup=kb)

# --- TEKSHIRISH TUGMASI ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    not_subbed = check_all_subs(call.from_user.id)
    if not not_subbed:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ Rahmat! Endi kino kodini yuboring:")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali barcha kanallarga a'zo emassiz!", show_alert=True)

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ Kino qo'shish", "❌ Kino o'chirish")
        kb.add("➕ Kanal qo'shish", "❌ Kanal o'chirish")
        kb.add("📊 Statistika")
        bot.send_message(message.chat.id, "🛠 Admin Panel:", reply_markup=kb)

# --- KANAL BOSHQARUVI ---
@bot.message_handler(func=lambda m: m.text == "➕ Kanal qo'shish")
def add_ch(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Kanal username'ini yuboring (@ belgisiz yoki @ bilan):")
        bot.register_next_step_handler(msg, save_ch)

def save_ch(message):
    ch_id = message.text if message.text.startswith("@") else f"@{message.text}"
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO channels VALUES (?)", (ch_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Kanal qo'shildi!")

@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish")
def del_ch_list(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('kino_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels")
        channels = cursor.fetchall()
        conn.close()
        
        if not channels:
            bot.send_message(message.chat.id, "Hozircha kanallar yo'q.")
            return

        kb = types.InlineKeyboardMarkup()
        for ch in channels:
            kb.add(types.InlineKeyboardButton(f"❌ {ch[0]}", callback_data=f"delch_{ch[0]}"))
        bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delch_"))
def del_ch_callback(call):
    ch_id = call.data.split("_")[1]
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_id = ?", (ch_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ {ch_id} o'chirildi!", call.message.chat.id, call.message.message_id)

# --- KINO BOSHQARUVI ---
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish")
def add_m(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Kino uchun KOD kiriting:")
        bot.register_next_step_handler(msg, get_c)

def get_c(message):
    c = message.text
    msg = bot.send_message(message.chat.id, "Kino NOMINI kiriting:")
    bot.register_next_step_handler(msg, get_n, c)

def get_n(message, c):
    n = message.text
    msg = bot.send_message(message.chat.id, "VIDEONI yuboring:")
    bot.register_next_step_handler(msg, get_v, c, n)

def get_v(message, c, n):
    if message.video:
        conn = sqlite3.connect('kino_bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (c, message.video.file_id, n))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Saqlandi!\nKod: {c}\nNomi: {n}")
    else:
        bot.send_message(message.chat.id, "❌ Xato! Video yubormadingiz. Qaytadan urinib ko'ring.")

@bot.message_handler(func=lambda m: m.text == "❌ Kino o'chirish")
def del_movie_start(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan kino kodini yuboring:")
        bot.register_next_step_handler(msg, del_movie_exec)

def del_movie_exec(message):
    code = message.text
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Kod {code} bo'lgan kino o'chirildi!")

# --- STATISTIKA ---
@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('kino_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        u = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM movies")
        m_c = cursor.fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"👤 Foydalanuvchilar: {u}\n🎬 Kinolar soni: {m_c}")

# --- KINO QIDIRISH ---
@bot.message_handler(func=lambda m: m.text.isdigit())
def search(message):
    # Avval obunani tekshiramiz
    not_subbed = check_all_subs(message.from_user.id)
    if not_subbed:
        return start(message)
        
    conn = sqlite3.connect('kino_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, name FROM movies WHERE code = ?", (message.text,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else:
        bot.send_message(message.chat.id, "😔 Afsus, bu kod bilan kino topilmadi.")

# --- BOTNI ISHGA TUSHIRISH ---
print("Bot ishlamoqda...")
bot.infinity_polling()
