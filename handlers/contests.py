import os
import uuid
import fitz  # PyMuPDF
import logging
from datetime import datetime
from aiogram import types, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from database import init_db, add_contest, get_all_contests, get_contest_by_id, delete_contest, get_all_departments, get_contests_by_department, add_department

# ---------------- INIT ----------------
init_db()
os.makedirs("contests_files", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("pdf_previews", exist_ok=True)

logger = logging.getLogger("contests")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("logs/contests.log", encoding='utf-8')
logger.addHandler(fh)

# ---------------- FSM ----------------
class ContestStates(StatesGroup):
    choosing_department_for_show = State()
    choosing_department_for_upload = State()
    choosing_department_for_delete = State()
    waiting_title = State()
    waiting_date = State()
    waiting_file = State()
    confirmation = State()
    waiting_new_department = State()  # НОВОЕ: для добавления отдела

# ---------------- UTILS ----------------
def generate_pdf_preview(file_path: str, pages: int = 1) -> list:
    previews = []
    try:
        with fitz.open(file_path) as doc:
            for i in range(min(pages, len(doc))):
                pix = doc[i].get_pixmap()
                path = os.path.join("pdf_previews", f"{uuid.uuid4().hex}.png")
                pix.save(path)
                previews.append(path)
    except Exception as e:
        logger.error(f"Ошибка генерации превью PDF: {e}")
    return previews

# ---------------- KEYBOARDS ----------------
def main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    kb = []
    kb.append([KeyboardButton(text="❓ Задать вопрос")])
    kb.append([KeyboardButton(text="📂 Положения конкурсов")])
    
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="📄 Загрузить положение")])
        kb.append([KeyboardButton(text="🗑 Удалить положение")])
        kb.append([KeyboardButton(text="➕ Добавить отдел")])  
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_departments_keyboard(action: str = "show") -> InlineKeyboardMarkup:
    """Клавиатура с отделами для разных действий"""
    departments = get_all_departments()
    keyboard = []
    
    if not departments:
        standard_departments = [
            (1, "🚒 Пожарная безопасность"),
            (2, "🚢 Судомодельные"),
            (3, "♟️ Шашки"),
            (4, "🚁 БПЛА"),
            (5, "🏎️ Автомодельные соревнования"),
            (6, "🤖 Робототехника")
        ]
        for dept_id, dept_name in standard_departments:
            add_department(dept_name)
        departments = standard_departments
    
    row = []
    for dept_id, dept_name in departments:
        row.append(InlineKeyboardButton(
            text=dept_name, 
            callback_data=f"contests_{action}_dept_{dept_id}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"contests_cancel_{action}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def _choose_contest_inline(contests: list, action: str = "download") -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора конкурса"""
    buttons = []
    
    for contest in contests:
        if len(contest) >= 3:
            cid = contest[0]
            title = contest[1]
            date = contest[2] if contest[2] else "без даты"
            
            display_title = title[:30] + "..." if len(title) > 30 else title
            
            if action == "download":
                button_text = f"📄 {display_title}"
                callback_data = f"contests_download_{cid}"
            else:
                button_text = f"🗑 {display_title}"
                callback_data = f"contests_delete_{cid}"
            
            buttons.append([InlineKeyboardButton(
                text=f"{button_text} ({date[:10]})", 
                callback_data=callback_data
            )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к отделам", callback_data="contests_back_to_depts")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да все верно"), KeyboardButton(text="❌ Нет, изменить")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def _log_action(line: str):
    try:
        with open("logs/actions.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {line}\n")
    except Exception:
        pass

# ---------------- ОСНОВНЫЕ ХЕНДЛЕРЫ ----------------
async def show_my_contests(message: types.Message, state: FSMContext):
    """Показать конкурсы - сначала выбор отдела"""
    print(f"[CONTESTS] show_my_contests от {message.from_user.id}")
    
    await state.clear()
    await state.set_state(ContestStates.choosing_department_for_show)
    
    kb = get_departments_keyboard(action="show")
    await message.answer(
        "📊 Выберите отдел:\nПоказать конкурсы из какого отдела?",
        reply_markup=kb
    )

async def start_upload(message: types.Message, state: FSMContext):
    """Начать загрузку - сначала выбор отдела"""
    print(f"[CONTESTS] start_upload от {message.from_user.id}")
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав", reply_markup=main_keyboard(message.from_user.id))
        return
    
    await state.clear()
    await state.set_state(ContestStates.choosing_department_for_upload)
    
    kb = get_departments_keyboard(action="upload")
    await message.answer(
        "📊 Выберите отдел:\nВ какой отдел загрузить конкурс?",
        reply_markup=kb
    )

async def delete_start(message: types.Message, state: FSMContext):
    """Начать удаление - сначала выбор отдела"""
    print(f"[CONTESTS] delete_start от {message.from_user.id}")
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав", reply_markup=main_keyboard(message.from_user.id))
        return
    
    await state.clear()
    await state.set_state(ContestStates.choosing_department_for_delete)
    
    kb = get_departments_keyboard(action="delete")
    await message.answer(
        "📊 Выберите отдел:\nИз какого отдела удалить конкурс?",
        reply_markup=kb
    )

async def add_department_start(message: types.Message, state: FSMContext):
    """Начать добавление нового отдела"""
    print(f"[CONTESTS] add_department_start от {message.from_user.id}")
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав", reply_markup=main_keyboard(message.from_user.id))
        return
    
    await state.clear()
    await state.set_state(ContestStates.waiting_new_department)
    await message.answer(
        "📝 Введите название нового отдела:\n\n"
        "Например:\n"
        "• 🎨 Творческие конкурсы\n"
        "• 🧪 Научные проекты\n"
        "• 💻 IT-олимпиады\n\n"
        "Для отмены введите /cancel или 'отмена'",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ---------------- FSM ДЛЯ ЗАГРУЗКИ И ДОБАВЛЕНИЯ ОТДЕЛА ----------------
async def fsm_text_handler(message: types.Message, state: FSMContext):
    """Обработчик текста для FSM"""
    current = await state.get_state()
    data = await state.get_data()
    txt = message.text.strip()
    
    # Проверка на отмену для всех состояний
    if txt.lower() in ["/cancel", "отмена", "cancel"]:
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=main_keyboard(message.from_user.id))
        return
    
    # ========== ДОБАВЛЕНИЕ НОВОГО ОТДЕЛА ==========
    if current == ContestStates.waiting_new_department.state:
        print(f"[CONTESTS FSM] Добавление отдела: '{txt}'")
        
        if len(txt) < 2:
            await message.answer("❌ Слишком короткое название. Введите еще раз:")
            return
        
        if len(txt) > 100:
            await message.answer("❌ Слишком длинное название. Максимум 100 символов:")
            return
        
        try:
            # Проверяем, нет ли уже такого отдела
            departments = get_all_departments()
            for dept_id, dept_name in departments:
                if dept_name.lower() == txt.lower():
                    await message.answer(f"❌ Отдел с названием '{txt}' уже существует. Введите другое название:")
                    return
            
            # Добавляем отдел в базу
            add_department(txt)
            _log_action(f"Department added: '{txt}' by {message.from_user.id}")
            
            await message.answer(
                f"✅ Отдел успешно добавлен!\n\n"
                f"🏢 Название: {txt}\n\n"
                f"Теперь вы можете загружать конкурсы в этот отдел.",
                reply_markup=main_keyboard(message.from_user.id)
            )
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                await message.answer(f"❌ Отдел с названием '{txt}' уже существует. Введите другое название:")
            else:
                await message.answer(f"❌ Ошибка при добавлении: {error_msg[:100]}", reply_markup=main_keyboard(message.from_user.id))
        
        await state.clear()
        return
    
    # ========== ЗАГРУЗКА КОНКУРСА ==========
    
    # Обработка состояния waiting_title
    if current == ContestStates.waiting_title.state:
        print(f"[CONTESTS FSM] Обработка waiting_title: '{txt}'")
        await state.update_data(title=txt)
        await state.set_state(ContestStates.waiting_date)
        await message.answer("📅 Введите дату конкурса:\n(Например: 15.12.2024 или Декабрь 2024)")
        return
    
    # Обработка состояния waiting_date
    elif current == ContestStates.waiting_date.state:
        print(f"[CONTESTS FSM] Обработка waiting_date: '{txt}'")
        
        if len(txt) < 3:
            await message.answer("❌ Неверная дата. Введите корректную дату:")
            return
        
        await state.update_data(date=txt)
        await state.set_state(ContestStates.waiting_file)
        await message.answer("✅ Дата сохранена!\n📎 Теперь отправьте PDF файл с положением конкурса.")
        return
    
    # Обработка состояния confirmation
    elif current == ContestStates.confirmation.state:
        print(f"[CONTESTS FSM] Обработка confirmation: '{txt}'")
        
        if txt == "✅ Да все верно":
            file_path = data.get("file_path")
            department_id = data.get("department_id", 1)
            title = data.get("title", "Без названия")
            date = data.get("date", "Без даты")
            
            if not file_path or not os.path.exists(file_path):
                await message.answer("❌ Файл не найден на сервере.", reply_markup=main_keyboard(message.from_user.id))
                await state.clear()
                return
            
            try:
                add_contest(title, date, data.get("file_name", ""), file_path, department_id=department_id)
                _log_action(f"Contest added: {title} to dept {department_id} by {message.from_user.id}")
                
                await message.answer(
                    f"✅ Конкурс успешно добавлен!\n\n"
                    f"📌 Название: {title}\n"
                    f"📅 Дата: {date}\n"
                    f"📎 Файл: {data.get('file_name', 'Неизвестно')}",
                    reply_markup=main_keyboard(message.from_user.id)
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка: {str(e)[:100]}", reply_markup=main_keyboard(message.from_user.id))
            
            await state.clear()
            
        elif txt == "❌ Нет, изменить":
            file_path = data.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            await state.clear()
            await message.answer("🔄 Начинаем заново.", reply_markup=main_keyboard(message.from_user.id))
        return
    
    # Если состояние не распознано
    print(f"[CONTESTS FSM] НЕРАСПОЗНАННОЕ СОСТОЯНИЕ: {current}")

async def receive_file(message: types.Message, state: FSMContext):
    """Получение PDF файла"""
    current = await state.get_state()
    print(f"[CONTESTS] receive_file: состояние = {current}")
    
    if current != ContestStates.waiting_file.state:
        print(f"[CONTESTS] receive_file: не то состояние, ожидалось waiting_file")
        return
    
    print(f"[CONTESTS] receive_file: получен документ")
    
    if not message.document or not message.document.file_name.lower().endswith(".pdf"):
        await message.answer("❌ Нужен PDF файл.")
        return
    
    unique = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join("contests_files", unique)
    
    try:
        tg_file = await message.bot.get_file(message.document.file_id)
        await message.bot.download_file(file_path=tg_file.file_path, destination=save_path)
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении файла: {e}")
        await state.clear()
        return
    
    file_name = message.document.file_name
    await state.update_data(file_name=file_name, file_path=save_path)
    
    # Получаем название из имени файла
    title = os.path.splitext(file_name)[0]
    await state.update_data(title=title)
    
    data = await state.get_data()
    s = (f"📄 Проверьте данные:\n\n"
         f"📌 Название: {title}\n"
         f"📅 Дата: {data['date']}\n"
         f"📎 Файл: {file_name}\n"
         f"💾 Сохранён как: {unique}")
    
    await message.answer(s)
    await message.answer("Всё верно?", reply_markup=confirmation_keyboard())
    await state.set_state(ContestStates.confirmation)

# ---------------- CALLBACK ОБРАБОТЧИКИ ----------------
async def contests_inline_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data or ""
    uid = callback.from_user.id
    
    print(f"[CONTESTS CALLBACK] {data} от {uid}")
    print(f"[CONTESTS CALLBACK] Текущее состояние до обработки: {await state.get_state()}")

    try:
        # Выбор отдела для ПОКАЗА конкурсов
        if data.startswith("contests_show_dept_"):
            dept_id = int(data.split("_")[3])
            print(f"[CONTESTS CALLBACK] Выбран отдел для показа: {dept_id}")
            
            contests = get_contests_by_department(dept_id)
            
            if not contests:
                await callback.message.edit_text(
                    "📭 В этом отделе пока нет конкурсов.\nВыберите другой отдел:",
                    reply_markup=get_departments_keyboard(action="show")
                )
                await callback.answer("В отделе нет конкурсов")
                return
            
            try:
                await callback.message.delete()
            except:
                pass
            
            # Получаем название отдела
            departments = get_all_departments()
            dept_name = "Неизвестный отдел"
            for d_id, d_name in departments:
                if d_id == dept_id:
                    dept_name = d_name
                    break
            
            kb = _choose_contest_inline(contests, action="download")
            await callback.message.answer(
                f"📂 {dept_name}\nВыберите конкурс для скачивания:",
                reply_markup=kb
            )
            await callback.answer()
            return
        
        # Выбор отдела для ЗАГРУЗКИ
        if data.startswith("contests_upload_dept_"):
            dept_id = int(data.split("_")[3])
            print(f"[CONTESTS CALLBACK] Выбран отдел для загрузки: {dept_id}")
            print(f"[CONTESTS CALLBACK] Устанавливаем состояние waiting_title")
            
            await state.update_data(department_id=dept_id)
            
            try:
                await callback.message.delete()
            except:
                pass
            
            # ВАЖНО: Устанавливаем состояние ДО отправки сообщения
            await state.set_state(ContestStates.waiting_title)
            print(f"[CONTESTS CALLBACK] Состояние установлено: {await state.get_state()}")
            
            await callback.message.answer(
                "📝 Введите название конкурса:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await callback.answer()
            return
        
        # Выбор отдела для УДАЛЕНИЯ
        if data.startswith("contests_delete_dept_"):
            dept_id = int(data.split("_")[3])
            await state.update_data(selected_department_id=dept_id)
            
            contests = get_contests_by_department(dept_id)
            
            if not contests:
                await callback.message.edit_text(
                    "📭 В этом отделе пока нет конкурсов.\nВыберите другой отдел:",
                    reply_markup=get_departments_keyboard(action="delete")
                )
                await callback.answer("В отделе нет конкурсов")
                return
            
            try:
                await callback.message.delete()
            except:
                pass
            
            departments = get_all_departments()
            dept_name = "Неизвестный отдел"
            for d_id, d_name in departments:
                if d_id == dept_id:
                    dept_name = d_name
                    break
            
            kb = _choose_contest_inline(contests, action="delete")
            await callback.message.answer(
                f"🗑 {dept_name}\n⚠️ Удаление нельзя отменить!\nВыберите конкурс для удаления:",
                reply_markup=kb
            )
            await callback.answer()
            return
        
        # Скачать конкурс
        if data.startswith("contests_download_"):
            cid = int(data.split("_")[2])
            contest = get_contest_by_id(cid)
            
            if contest and contest[4] and os.path.exists(contest[4]):
                try:
                    await callback.message.delete()
                except:
                    pass
                
                await callback.message.answer(f"📄 Скачивание файла: {contest[1]}")
                await callback.message.answer_document(
                    FSInputFile(contest[4], filename=contest[3]),
                    caption=f"📌 {contest[1]}\n📅 {contest[2] if contest[2] else 'Без даты'}"
                )
                await callback.message.answer(
                    "✅ Файл отправлен!",
                    reply_markup=main_keyboard(uid)
                )
            else:
                await callback.message.answer("❌ Файл не найден")
            
            await callback.answer()
            return
        
        # Удалить конкурс
        if data.startswith("contests_delete_"):
            if uid != ADMIN_ID:
                await callback.answer("❌ У вас нет прав", show_alert=True)
                return
            
            cid = int(data.split("_")[2])
            contest = get_contest_by_id(cid)
            
            if contest:
                try:
                    await callback.message.delete()
                except:
                    pass
                
                if contest[4] and os.path.exists(contest[4]):
                    try:
                        os.remove(contest[4])
                    except:
                        pass
                
                delete_contest(cid)
                
                await callback.message.answer(
                    f"✅ Конкурс удален!\n\n"
                    f"🗑 Название: {contest[1]}\n"
                    f"📅 Дата: {contest[2] if contest[2] else 'Без даты'}",
                    reply_markup=main_keyboard(uid)
                )
                _log_action(f"Contest deleted: {contest[1]} by {uid}")
            
            await callback.answer()
            return
        
        # Назад к отделам
        if data == "contests_back_to_depts":
            try:
                await callback.message.delete()
            except:
                pass
            
            await state.set_state(ContestStates.choosing_department_for_show)
            kb = get_departments_keyboard(action="show")
            await callback.message.answer(
                "📊 Выберите отдел:\nПоказать конкурсы из какого отдела?",
                reply_markup=kb
            )
            await callback.answer()
            return
        
        # Отмена действий
        if data.startswith("contests_cancel_"):
            action = data.split("_")[2]
            
            try:
                await callback.message.delete()
            except:
                pass
            
            await state.clear()
            await callback.message.answer(
                "✅ Действие отменено",
                reply_markup=main_keyboard(uid)
            )
            await callback.answer("Отменено")
            return

    except Exception as e:
        print(f"[CONTESTS CALLBACK] Ошибка: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}", show_alert=True)
        logger.error(f"Contests callback error: {e}")

# ---------------- REGISTER ----------------
def register_contest_handlers(dp: Dispatcher):

    dp.message.register(add_department_start, F.text == "➕ Добавить отдел")
    dp.message.register(show_my_contests, F.text == "📂 Положения конкурсов")
    dp.message.register(start_upload, F.text == "📄 Загрузить положение")
    dp.message.register(delete_start, F.text == "🗑 Удалить положение")
    
    # FSM обработчики
    dp.message.register(fsm_text_handler, ContestStates.waiting_title)
    dp.message.register(fsm_text_handler, ContestStates.waiting_date)
    dp.message.register(fsm_text_handler, ContestStates.confirmation)
    dp.message.register(fsm_text_handler, ContestStates.waiting_new_department)  
    
    dp.message.register(receive_file, ContestStates.waiting_file)
    
    # Callback обработчики
    dp.callback_query.register(contests_inline_callback_handler, F.data.startswith("contests_"))
    
    print("[CONTESTS] ✅ Хендлеры зарегистрированы")