# migrate_db.py
import sqlite3
import os

def migrate_database():
    """Добавляет отделы в существующую базу данных"""
    print("Миграция базы данных...")
    
    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()
    
    # 1. Создаем таблицу отделов если её нет
    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL)''')
    
    # 2. Добавляем поле department_id в таблицу конкурсов если его нет
    c.execute("PRAGMA table_info(contests)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'department_id' not in columns:
        c.execute("ALTER TABLE contests ADD COLUMN department_id INTEGER")
        print("✅ Добавлено поле department_id в таблицу contests")
    
    # 3. Добавляем стандартные отделы
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
    
    # 4. Обновляем существующие конкурсы (ставим им department_id = 1 по умолчанию)
    c.execute("UPDATE contests SET department_id = 1 WHERE department_id IS NULL")
    
    conn.commit()
    conn.close()
    print("✅ Миграция завершена успешно!")
    print("✅ Все конкурсы привязаны к отделу 'Пожарная безопасность'")
    print("⚠️  Не забудь вручную поправить department_id у конкурсов!")

if __name__ == "__main__":
    migrate_database()