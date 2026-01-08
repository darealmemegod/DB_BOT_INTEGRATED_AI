# ai_ping.py
"""
Пинг серверов DeepSeek и проверка работы AI.
Выводит в терминал, работает ли ИИ и почему мог не ответить.
"""

import aiohttp
import asyncio
from config import DEEPSEEK_API_KEY

DEEP_URL = "https://api.deepseek.com/v1"

async def ping_deepseek():
    print("Проверяем сервер DeepSeek...")
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DEEP_URL}/models", headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ Сервер доступен. Доступные модели:")
                    for m in data.get("models", []):
                        print(f" - {m}")
                else:
                    print(f"❌ Сервер вернул статус {resp.status}")
    except asyncio.TimeoutError:
        print("❌ Timeout: сервер не отвечает")
    except Exception as e:
        print(f"❌ Ошибка подключения к серверу: {e}")

async def test_ai_response():
    """
    Пробуем отправить тестовый запрос AI и смотрим, отвечает ли.
    """
    print("\nПроверяем работу AI модели...")
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Проверки ответа от ИИ, в ТГ бота ответ не выходит."}
        ],
        "max_tokens": 50,
        "stream": False
    }
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{DEEP_URL}/chat/completions", headers=headers, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    print(f"❌ AI вернул статус {resp.status}")
                    text = await resp.text()
                    print("Ответ сервера:", text)
                    return
                result = await resp.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if answer:
                    print("✅ AI ответил успешно:")
                    print(answer)
                else:
                    print("❌ AI не вернул текст. Проверьте API ключ или доступ к модели.")
    except asyncio.TimeoutError:
        print("❌ Timeout: AI не ответил")
    except Exception as e:
        print(f"❌ Ошибка при запросе к AI: {e}")

async def main():
    await ping_deepseek()
    await test_ai_response()

if __name__ == "__main__":
    asyncio.run(main())
