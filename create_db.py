# create_db.py
from database import init_db

if __name__ == "__main__":
    init_db()
    print("База данных создана! Структура таблицы 'contests':")
    print("| id | title | contest_date | file_name | created_date |")