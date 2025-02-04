import sqlite3
from config import DATABASE_PATH
import logging

logger = logging.getLogger(__name__)

def get_database():
    """Возвращает соединение с базой данных"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_database():
    """Инициализирует базу данных"""
    conn = get_database()
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            level TEXT DEFAULT NULL,
            test_score INTEGER DEFAULT 0,
            test_state TEXT DEFAULT NULL,
            has_completed_test BOOLEAN DEFAULT 0,
            learning_plan TEXT,
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Создаем таблицу планов обучения
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            current_level TEXT,
            target_level TEXT,
            topics TEXT,
            plan_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()
    conn.close() 