import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
TOKEN = os.getenv("TG_TOKEN")

# ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Проверка
if not DEEPSEEK_API_KEY:
    raise ValueError("API ключ DeepSeek не найден! Установи переменную окружения DEEPSEEK_API_KEY")