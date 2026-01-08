# database.py
import sqlite3
import os


def init_db():
    """Инициализация базы данных и создание таблиц"""
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()

    # Создаем таблицу для отделов
    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL)''')

    # Создаем таблицу для конкурсов
    c.execute('''CREATE TABLE IF NOT EXISTS contests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  contest_date TEXT NOT NULL,
                  file_name TEXT,
                  file_path TEXT,
                  department_id INTEGER,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (department_id) REFERENCES departments(id))''')

    # Добавляем стандартные отделы если их нет
    default_departments = [
        "Пожарная безопасность",
        "Судомодельные",
        "Шашки",
        "БПЛА",
        "Автомодельные соревнования",
        "Робототехника"
    ]
    
    for dept in default_departments:
        c.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))

    conn.commit()
    conn.close()
    print("✅ База данных успешно создана/обновлена!")


def get_all_departments():
    """Получить все отделы из БД"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments ORDER BY name")
    departments = c.fetchall()
    conn.close()
    return departments


def add_department(name):
    """Добавить новый отдел"""
    try:
        conn = sqlite3.connect('data/contests.db')
        c = conn.cursor()
        c.execute("INSERT INTO departments (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Отдел уже существует


def get_contests_by_department(department_id):
    """Получить конкурсы по ID отдела"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, contest_date, file_name, file_path 
        FROM contests 
        WHERE department_id = ?
        ORDER BY contest_date DESC
    ''', (department_id,))
    contests = c.fetchall()
    conn.close()
    return contests


def add_contest(title, contest_date, file_name, file_path, department_id=1):
    """Добавление нового конкурса в базу"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    c.execute("INSERT INTO contests (title, contest_date, file_name, file_path, department_id) VALUES (?, ?, ?, ?, ?)",
              (title, contest_date, file_name, file_path, department_id))
    conn.commit()
    conn.close()
    return True


def get_all_contests():
    """Получение всех конкурсов"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    c.execute('''
        SELECT c.id, c.title, c.contest_date, c.file_name, c.file_path, d.name as department_name
        FROM contests c
        LEFT JOIN departments d ON c.department_id = d.id
        ORDER BY c.created_date DESC
    ''')
    contests = c.fetchall()
    conn.close()
    return contests


def get_contest_by_id(contest_id):
    """Получение конкурса по ID"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    c.execute('''
        SELECT c.id, c.title, c.contest_date, c.file_name, c.file_path, 
               c.department_id, d.name as department_name
        FROM contests c
        LEFT JOIN departments d ON c.department_id = d.id
        WHERE c.id = ?
    ''', (contest_id,))
    contest = c.fetchone()
    conn.close()
    return contest


def delete_contest(contest_id):
    """Удаление конкурса из базы данных"""
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    # Сначала получаем путь к файлу
    c.execute("SELECT file_path FROM contests WHERE id = ?", (contest_id,))
    result = c.fetchone()

    if result and result[0]:
        # Удаляем файл с диска
        try:
            if os.path.exists(result[0]):
                os.remove(result[0])
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")

    # Удаляем запись из базы данных
    c.execute("DELETE FROM contests WHERE id = ?", (contest_id,))
    conn.commit()
    conn.close()
    return True