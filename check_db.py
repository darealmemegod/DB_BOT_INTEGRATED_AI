# check_db.py
import sqlite3
import os


def check_database():
    """Проверяет структуру базы данных"""
    if not os.path.exists("data/contests.db"):
        print("❌ База данных не найдена")
        return

    conn = sqlite3.connect('data/contests.db')
    c = conn.cursor()

    # Получаем информацию о таблице
    c.execute("PRAGMA table_info(contests)")
    columns = c.fetchall()
    print("Структура таблицы contests:")
    for col in columns:
        print(f"  {col[1]} - {col[2]} (id: {col[0]})")

    # Получаем все записи
    c.execute("SELECT id, title, file_name, file_path FROM contests")
    contests = c.fetchall()
    print(f"\nВсего записей: {len(contests)}")

    for contest in contests:
        contest_id, title, file_name, file_path = contest
        print(f"\nКонкурс ID {contest_id}:")
        print(f"  Название: {title}")
        print(f"  Имя файла: {file_name}")
        print(f"  Путь: {file_path}")
        if file_path:
            exists = os.path.exists(file_path)
            print(f"  Файл существует: {'✅' if exists else '❌'}")
            if exists:
                print(f"  Размер: {os.path.getsize(file_path)} байт")

    conn.close()


if __name__ == "__main__":
    check_database()