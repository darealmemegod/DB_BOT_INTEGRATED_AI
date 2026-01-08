import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from config import TOKEN
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

# Импортируем регистраторы
from handlers.ID import register_userlog_handler
from handlers.contests import register_contest_handlers, main_keyboard
from handlers.AI import register_ai_handlers
from handlers.admin import register_admin_ai_myid_handler
from handlers.echo import register_echo_handler

logging.basicConfig(level=logging.INFO)

async def start_command(message: types.Message):
    print(f"🟢 /start от {message.from_user.id}")
    await message.answer(
        "👋 Добро пожаловать в бот для работы с конкурсами!\n"
        "Используйте кнопки ниже для навигации.",
        reply_markup=main_keyboard(message.from_user.id)
    )

async def menu_command(message: types.Message):
    print(f"🟢 /menu от {message.from_user.id}")
    await message.answer(
        "📋 Главное меню:",
        reply_markup=main_keyboard(message.from_user.id)
    )

async def main():
    session = AiohttpSession()
    bot = Bot(token=TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_command, Command("start"))
    dp.message.register(menu_command, Command("menu"))

    
    print("🟢 Регистрируем contest хендлеры...")
    register_contest_handlers(dp)  
    
    print("🟢 Регистрируем AI хендлеры...")
    register_ai_handlers(dp)  
    
    print("🟢 Регистрируем admin хендлеры...")
    register_admin_ai_myid_handler(dp) 
    
    print("🟢 Регистрируем userlog хендлер...")
    register_userlog_handler(dp)  
    
    print("🟢 Регистрируем echo хендлер...")
    register_echo_handler(dp)  

    print("✅ Бот запущен!")
    print("📋 Кнопки в меню:")
    print("   - ❓ Задать вопрос")
    print("   - 📂 Положения конкурсов")
    print("   - 📄 Загрузить положение (админ)")
    print("   - 🗑 Удалить положение (админ)")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())