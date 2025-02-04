import sqlite3
import os
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DATABASE_PATH

def init_database():
    """Инициализация базы данных"""
    # Проверяем, существует ли файл базы данных
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    # Получаем путь к файлу schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    # Создаем новое соединение
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Читаем SQL-скрипт
    with open(schema_path, 'r') as f:
        sql_script = f.read()
    
    # Выполняем SQL-скрипт
    cursor.executescript(sql_script)
    
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    
    print("База данных успешно инициализирована!")

if __name__ == "__main__":
    init_database() 