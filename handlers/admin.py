import os
from datetime import datetime
from aiogram import types, Dispatcher
from aiogram.filters import Command
from config import ADMIN_ID

# Глобальные переменные (только для этого модуля)
secret_mode = False
blocked_users = set()

def register_admin_ai_myid_handler(dp: Dispatcher):
    """Регистрация админских команд (старый подход через dp)"""
    
    # /myid - для всех пользователей
    @dp.message(Command("myid"))
    async def myid(message: types.Message):
        print(f"[ADMIN] /myid от {message.from_user.id}")
        user_id = message.from_user.id
        
        if user_id == ADMIN_ID:
            await message.answer(
                f"👑 Твой ID: {user_id}\n\n"
                "Ты админ! Доступные команды:\n"
                "/admin_mode - грубый режим ИИ\n"
                "/troll @user - заблокировать\n"
                "/stats - статистика\n"
                "/author - автор бота"
            )
        else:
            await message.answer(f"🆔 Твой ID: {user_id}")
    
    # /admin_mode - только для админа
    @dp.message(Command("admin_mode"))
    async def toggle_secret_mode(message: types.Message):
        print(f"[ADMIN] /admin_mode от {message.from_user.id}")
        
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ У вас нет прав админа")
            return
        
        global secret_mode
        secret_mode = not secret_mode
        status = "включён 🔥" if secret_mode else "выключен ✅"
        await message.answer(f"Грубый режим ИИ {status}")
    
    # /troll - только для админа
    @dp.message(Command("troll"))
    async def add_blocked_user(message: types.Message):
        print(f"[ADMIN] /troll от {message.from_user.id}")
        
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ У вас нет прав админа")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Укажи пользователя: /troll @username или /troll user_id")
            return
        
        user = parts[1]
        try:
            if user.startswith("@"):
                # Для юзернеймов сохраняем как строку
                blocked_users.add(user)
                await message.answer(f"✅ Пользователь {user} добавлен в черный список 😏")
            else:
                # Для ID сохраняем как число
                user_id = int(user)
                blocked_users.add(user_id)
                await message.answer(f"✅ Пользователь ID:{user} добавлен в черный список 😏")
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте: /troll @username или /troll 123456789")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)[:50]}")
    
    # /stats - только для админа
    @dp.message(Command("stats"))
    async def show_stats(message: types.Message):
        print(f"[ADMIN] /stats от {message.from_user.id}")
        
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ У вас нет прав админа")
            return
        
        # Получаем количество пользователей из базы (если есть)
        try:
            import sqlite3
            conn = sqlite3.connect("bot.db")
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            conn.close()
        except:
            user_count = 0
        
        stats_text = (
            "📊 Статистика бота:\n\n"
            f"👑 Админ ID: {ADMIN_ID}\n"
            f"👥 Всего пользователей: {user_count}\n"
            f"🚫 Заблокированных: {len(blocked_users)}\n"
            f"🤖 Грубый режим ИИ: {'ВКЛ' if secret_mode else 'ВЫКЛ'}\n\n"
            "Доступные команды:\n"
            "/myid - узнать свой ID\n"
            "/admin_mode - грубый режим\n"
            "/troll @user - заблокировать\n"
            "/author - автор"
        )
        
        await message.answer(stats_text)
    
    # /author - для всех пользователей
    @dp.message(Command("author"))
    async def show_author(message: types.Message):
        print(f"[ADMIN] /author от {message.from_user.id}")
        author_name = "Ковалик Иван"
        await message.answer(f"👨‍💻 Автор бота: {author_name}")
        
    # /help или /commands - показать все команды
    @dp.message(Command("help", "commands"))
    async def show_help(message: types.Message):
        help_text = (
            "📋 Доступные команды:\n\n"
            "Для всех:\n"
            "/start - начать работу\n"
            "/menu - главное меню\n"
            "/myid - узнать свой ID\n"
            "/author - автор бота\n"
            "/help - эта справка\n\n"
            "Кнопки меню:\n"
            "❓ Задать вопрос - AI-помощник\n"
            "📂 Положения конкурсов - скачать PDF"
        )
        
        if message.from_user.id == ADMIN_ID:
            help_text += (
                "\n\n👑 Админские команды:\n"
                "/admin_mode - грубый режим ИИ\n"
                "/troll @user - заблокировать\n"
                "/stats - статистика\n\n"
                "Админские кнопки:\n"
                "📄 Загрузить положение\n"
                "🗑 Удалить положение\n"
                "➕ Добавить отдел"
            )
        
        await message.answer(help_text)
    
    print("[ADMIN] ✅ Админские хендлеры зарегистрированы (старый подход)")
