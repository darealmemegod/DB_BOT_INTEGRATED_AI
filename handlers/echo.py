from aiogram import Dispatcher, F
from aiogram.types import Message
import re

last_messages = {}

def check_duplicate(user_id: int, message: str) -> bool:
    return last_messages.get(user_id) == message

def count_words(text: str) -> int:
    return len(text.strip().split())

def count_letters(text: str) -> int:
    return len(re.sub(r"[^A-Za-zА-Яа-яЁё]", "", text))

async def echo_handler(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    print(f"[DEBUG] echo от {user_id}: '{text}'")

    if not text:
        await message.answer("Пустое сообщение не анализирую.")
        return

    words = count_words(text)
    letters = count_letters(text)

    is_duplicate = check_duplicate(user_id, text)
    last_messages[user_id] = text

    reply = f"В вашем сообщении: {words} слов, {letters} букв."
    if is_duplicate:
        reply += " Вы уже отправляли это сообщение ранее."

    await message.answer(reply)

def register_echo_handler(dp: Dispatcher):
    # Регистрируем ТОЛЬКО для команды /echo или определенного текста
    dp.message.register(echo_handler, F.text.startswith("/echo"))