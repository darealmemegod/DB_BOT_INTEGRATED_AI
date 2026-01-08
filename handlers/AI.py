import os
import re
import aiohttp
import asyncio
import logging
import fitz  # PyMuPDF
from datetime import datetime
from aiogram import types, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import DEEPSEEK_API_KEY, ADMIN_ID
from handlers.contests import main_keyboard
from database import get_all_departments, get_contests_by_department, get_contest_by_id

# ---------------- INIT ----------------
DEEP_URL = "https://api.deepseek.com/v1"

logger = logging.getLogger("ai")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("logs/ai_deepseek.log", encoding='utf-8')
logger.addHandler(fh)

# ---------------- FSM ----------------
class AIStates(StatesGroup):
    choosing_department = State()
    choosing_contest = State()
    waiting_question = State()

# ---------------- UTILS ----------------
SPAM_PATTERNS = [
    r"(http[s]?://)",
    r"(discord\.gg|t\.me|telegram)",
    r"(бесплатно|халява|скидка)",
    r"(.)\1{5,}",
    r"\b(сука|бля|нахуй)\b"
]

def is_spam(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in SPAM_PATTERNS)

def is_too_long(text: str, limit: int = 1000) -> bool:
    return len(text) > limit

def extract_pdf_text(file_path: str, max_chars: int = 5000) -> str:
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        logger.error(f"Ошибка чтения PDF: {e}")
    return text[:max_chars]

def _log_ai(user_id: int, username: str, user_text: str, ai_response: str = "", reason: str = ""):
    try:
        with open("logs/ai_logs.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] UID:{user_id} @{username}\n")
            f.write(f"User: {user_text}\n")
            if reason:
                f.write(f"Reason: {reason}\n")
            f.write(f"AI: {ai_response}\n" + "-"*30 + "\n")
    except Exception:
        pass

def get_departments_keyboard(is_admin=False):
    """Клавиатура с отделами"""
    departments = get_all_departments()
    keyboard = []
    
    # Если отделов нет, создаем стандартные
    if not departments:
        standard_departments = [
            (1, "🚒 Пожарная безопасность"),
            (2, "🚢 Судомодельные"),
            (3, "♟️ Шашки"),
            (4, "🚁 БПЛА"),
            (5, "🏎️ Автомодельные соревнования"),
            (6, "🤖 Робототехника")
        ]
        from database import add_department
        for dept_id, dept_name in standard_departments:
            add_department(dept_name)
        departments = standard_departments
    
    # Группируем по 2 кнопки в ряд
    row = []
    for dept_id, dept_name in departments:
        row.append(InlineKeyboardButton(
            text=dept_name, 
            callback_data=f"ai_dept_{dept_id}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Закончить диалог", callback_data="ai_end_dialog")]
    ])
    return keyboard

def _choose_contest_inline(contests: list):
    buttons = []
    for contest in contests:
        cid, title, date, *_ = contest
        # Ограничиваем длину названия для кнопки
        display_title = title[:30] + "..." if len(title) > 30 else title
        buttons.append([InlineKeyboardButton(
            text=f"📄 {display_title} ({date})", 
            callback_data=f"ai_select_{cid}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Назад к отделам", callback_data="ai_back_to_depts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---------------- HANDLERS ----------------
async def start_question(message: types.Message, state: FSMContext):
    """Начало диалога с ИИ - выбор отдела"""
    print(f"[AI DEBUG] start_question от {message.from_user.id}")
    is_admin = message.from_user.id == ADMIN_ID
    kb = get_departments_keyboard(is_admin)
    await message.answer("Выберите отдел:", reply_markup=kb)
    await state.set_state(AIStates.choosing_department)

async def handle_ai_question(message: types.Message, state: FSMContext):
    """Обработка вопросов к ИИ"""
    print(f"[AI DEBUG] handle_ai_question от {message.from_user.id}: '{message.text}'")
    
    # Проверка команды отмены
    if message.text.strip().lower() in ["отмена", "закончить", "стоп", "/cancel"]:
        await state.clear()
        await message.answer("Диалог с ИИ завершен.", reply_markup=main_keyboard(message.from_user.id))
        return

    data = await state.get_data()
    selected = data.get("selected_contest")
    
    if not selected:
        await message.answer("⚠️ Сначала выберите конкурс", reply_markup=main_keyboard(message.from_user.id))
        return

    text = message.text.strip()
    
    if is_spam(text):
        await message.answer("Сообщение похоже на спам 🚫")
        return
    if is_too_long(text):
        await message.answer("Слишком длинное сообщение. Разбейте на части.")
        return

    pdf_path = selected.get("file_path")
    if not pdf_path or not os.path.exists(pdf_path):
        await message.answer("❌ PDF файл выбранного конкурса не найден")
        await state.clear()
        return

    thinking_msg = await message.answer("ИИ думает... ⏳")

    # Получаем историю диалога
    dialog_history = data.get("dialog_history", [])
    
    # Первый вопрос - добавляем контекст PDF
    if len(dialog_history) == 0:
        pdf_text = extract_pdf_text(pdf_path)
        # ОБНОВЛЕННЫЙ ПРОМПТ ДЛЯ КРАТКИХ ОТВЕТОВ
        system_message = f"""Ты помощник, который отвечает на вопросы о конкурсе. 
        Вот информация о конкурсе: {pdf_text}
        
        Отвечай на вопросы пользователя на основе этой информации.
        БУДЬ КРАТКИМ! Отвечай одним предложением, максимум два.
        Отвечай только по существу вопроса."""
        dialog_history.append({"role": "system", "content": system_message})
    
    # Добавляем вопрос пользователя
    dialog_history.append({"role": "user", "content": text})
    
    # Ограничиваем историю (оставляем system message и последние 6 сообщений)
    max_history = 7  # system + 3 пары вопрос/ответ
    if len(dialog_history) > max_history:
        dialog_history = [dialog_history[0]] + dialog_history[-max_history+1:]
    
    payload = {
        "model": "deepseek-chat",
        "messages": dialog_history,
        "max_tokens": 150,  # Уменьшили для краткости
        "stream": False
    }
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

    answer = ""
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(f"{DEEP_URL}/chat/completions", headers=headers, json=payload, timeout=60) as resp:
                result = await resp.json()
        answer = result["choices"][0]["message"]["content"]
        
        # Добавляем ответ ассистента в историю
        dialog_history.append({"role": "assistant", "content": answer})
        await state.update_data(dialog_history=dialog_history)
        
    except Exception as e:
        answer = f"Ошибка: {e}"
        logger.error(f"DeepSeek error: {e}")

    # Плавный вывод ответа
    display_text = ""
    for i, char in enumerate(answer, 1):
        display_text += char
        if i % 20 == 0:
            try:
                await thinking_msg.edit_text(display_text + "⏳")
            except Exception:
                pass
            await asyncio.sleep(0.05)
    
    # Отправляем окончательный ответ с кнопкой отмены
    try:
        await thinking_msg.edit_text(display_text, reply_markup=get_cancel_keyboard())
    except Exception:
        await message.answer(answer, reply_markup=get_cancel_keyboard())

    _log_ai(message.from_user.id, message.from_user.username, text, answer)
    
    # Оставляем состояние waiting_question для следующего вопроса

# ---------------- INLINE CALLBACKS ----------------
async def ai_inline_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик callback-ов только для AI модуля"""
    data = callback.data or ""
    
    print(f"[AI DEBUG] callback: {data} от {callback.from_user.id}")
    
    try:
        # Выбор отдела
        if data.startswith("ai_dept_"):
            dept_id = int(data.split("_")[2])
            await state.update_data(selected_department_id=dept_id)
            
            # Получаем конкурсы этого отдела
            contests = get_contests_by_department(dept_id)
            
            if not contests:
                await callback.message.edit_text(
                    "📭 В этом отделе пока нет конкурсов.",
                    reply_markup=get_departments_keyboard(callback.from_user.id == ADMIN_ID)
                )
                await callback.answer()
                return
            
            # УДАЛЯЕМ сообщение с выбором отдела
            try:
                await callback.message.delete()
            except:
                pass
            
            # Показываем конкурсы отдела
            kb = _choose_contest_inline(contests)
            await callback.message.answer(
                "Выберите конкурс для вопросов к ИИ:",
                reply_markup=kb
            )
            await state.set_state(AIStates.choosing_contest)
            await callback.answer()
            return
        
        # Выбор конкурса для AI
        if data.startswith("ai_select_"):
            cid = int(data.split("_")[2])
            contest = get_contest_by_id(cid)
            
            if not contest or len(contest) < 5:
                await callback.answer("Конкурс не найден", show_alert=True)
                return

            # УДАЛЯЕМ сообщение с выбором конкурса
            try:
                await callback.message.delete()
            except:
                pass

            # Сохраняем выбранный конкурс и очищаем историю диалога
            await state.update_data(
                selected_contest={
                    "id": contest[0],
                    "title": contest[1],
                    "date": contest[2],
                    "file_name": contest[3],
                    "file_path": contest[4]
                },
                dialog_history=[]
            )
            
            # 1. Сначала отправляем PDF файл положения конкурса
            if contest[4] and os.path.exists(contest[4]):
                await callback.message.answer(
                    f"📄 Положение конкурса:\n"
                    f"📌 {contest[1]}\n"
                    f"📅 {contest[2] if contest[2] else 'Без даты'}\n\n"
                    "⬇️ Файл отправлен ниже:"
                )
                
                await callback.message.answer_document(
                    FSInputFile(contest[4], filename=contest[3]),
                    caption=f"📄 {contest[1]}"
                )
            
            # 2. Затем предлагаем задать вопрос
            await callback.message.answer(
                f"🤖 Теперь вы можете задать вопросы ИИ по этому конкурсу\n\n"
                f"Конкурс: {contest[1]}\n\n"
                "Напишите свой вопрос для ИИ.\n"
                "Диалог будет продолжаться до отмены.\n"
                "Напишите 'отмена' или нажмите кнопку 'Закончить диалог' для завершения.",
                reply_markup=get_cancel_keyboard()
            )
            
            await state.set_state(AIStates.waiting_question)
            await callback.answer()
            return
        
        # Назад к отделам
        if data == "ai_back_to_depts":
            try:
                await callback.message.delete()
            except:
                pass
                
            is_admin = callback.from_user.id == ADMIN_ID
            kb = get_departments_keyboard(is_admin)
            await callback.message.answer("Выберите отдел:", reply_markup=kb)
            await state.set_state(AIStates.choosing_department)
            await callback.answer()
            return
        
        # Завершение диалога с ИИ
        if data == "ai_end_dialog":
            await state.clear()
            await callback.message.answer("Диалог с ИИ завершен.", reply_markup=main_keyboard(callback.from_user.id))
            await callback.answer()
            return

    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        logger.error(f"AI inline handler error: {e}")

# ---------------- REGISTER ----------------
def register_ai_handlers(dp: Dispatcher):
    dp.message.register(start_question, F.text == "❓ Задать вопрос")
    dp.message.register(handle_ai_question, AIStates.waiting_question)
    dp.callback_query.register(ai_inline_callback_handler, F.data.startswith("ai_"))
    
    print("[AI] ✅ Хендлеры зарегистрированы")