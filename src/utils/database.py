import sqlite3
from typing import Any
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.path = DATABASE_PATH

    def execute(self, query: str, params: tuple = ()) -> Any:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return result

def get_database() -> Database:
    """Возвращает экземпляр класса для работы с базой данных"""
    return Database() 