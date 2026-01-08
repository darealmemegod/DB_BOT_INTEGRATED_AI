import sqlite3
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Dispatcher

# Создаем роутер
id_router = Router()

conn = sqlite3.connect("bot.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username

    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username)
        VALUES (?, ?)
    """, (user_id, username))
    conn.commit()

FRIEND_ID = 182491249  

@id_router.message(F.from_user.id == FRIEND_ID)
async def block_friend(message: types.Message):
    print(f"[BLOCK] Блокируем FRIEND_ID {FRIEND_ID}")
    register_user(message)
    await message.answer("саша пошел нахуй, нехер мне бота ломать")

@id_router.message()
async def log_all_users(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state:
        return
    
    if message.text and message.text.strip():
        print(f"[LOG] {message.from_user.id}: '{message.text[:30]}'")
        register_user(message)

def register_userlog_handler(dp: Dispatcher):
    @dp.message(F.from_user.id == FRIEND_ID)
    async def block_friend(message: types.Message):
        print(f"[BLOCK] Блокируем FRIEND_ID {FRIEND_ID}")
        register_user(message)
        await message.answer("саша пошел нахуй, нехер мне бота ломать")
        return  # Важно: прерываем обработку
    
    @dp.message()
    async def log_all_users(message: types.Message, state: FSMContext):
        if message.text and message.text.strip():
            print(f"[LOG] {message.from_user.id}: '{message.text[:30]}'")
            register_user(message)
        
    print("[ID.py] ✅ Хендлеры зарегистрированы (прозрачное логирование)")