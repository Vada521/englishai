import sqlite3
import json
import logging
from datetime import datetime
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

def init_db():
    """Инициализирует базу данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Логируем текущие таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    logger.info(f"Database tables: {tables}")
    
    # Логируем структуру таблицы users
    cursor.execute("PRAGMA table_info(users)")
    structure = cursor.fetchall()
    logger.info(f"Users table structure: {structure}")
    
    conn.close()

def save_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None, phone: str = None):
    """Сохраняет информацию о пользователе"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO users (user_id, username, first_name, last_name, phone)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            phone = excluded.phone
    """, (user_id, username, first_name, last_name, phone))
    
    conn.commit()
    conn.close()

def get_user_profile(user_id: int) -> dict:
    """Получает профиль пользователя"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT u.level, u.test_score, lp.progress, lp.current_level, lp.target_level,
                   (SELECT COUNT(*) FROM learning_progress WHERE user_id = ? AND completed = 1) as completed_topics
            FROM users u
            LEFT JOIN learning_plans lp ON u.user_id = lp.user_id
            WHERE u.user_id = ?
        ''', (user_id, user_id))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            level, test_score, progress, current_level, target_level, completed_topics = result
            return {
                'level': level or 'Не определен',
                'test_score': test_score or 0,
                'progress': progress or 0,
                'current_level': current_level or 'Не определен',
                'target_level': target_level or 'Не определен',
                'completed_topics': completed_topics or 0
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

def save_learning_plan(user_id: int, plan_data: dict):
    """Сохраняет план обучения пользователя"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Преобразуем topics в JSON строку
        topics_json = json.dumps(plan_data.get('topics', []))
        
        cursor.execute("""
            INSERT INTO learning_plans 
            (user_id, current_level, target_level, topics, plan_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            plan_data.get('current_level'),
            plan_data.get('target_level'),
            topics_json,
            json.dumps(plan_data)
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving learning plan: {e}")
        return False

def get_learning_plan(user_id: int) -> dict:
    """Получает план обучения"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        c.execute('SELECT current_level, target_level, topics FROM learning_plans WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            current_level, target_level, topics_json = result
            return {
                'current_level': current_level,
                'target_level': target_level,
                'topics': json.loads(topics_json)
            }
        return None
    except Exception as e:
        logger.error(f"Error getting learning plan: {e}")
        return None

def update_test_score(user_id: int, score: int, level: str):
    """Обновляет результаты теста пользователя"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        # Проверяем существование пользователя
        c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            # Если пользователя нет, создаем его
            c.execute('''
                INSERT INTO users (user_id, test_score, level, last_activity)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, score, level))
        else:
            # Если пользователь есть, обновляем данные
            c.execute('''
                UPDATE users 
                SET test_score = ?, level = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (score, level, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating test score: {e}")
        return False 

def get_current_topic(user_id: int) -> dict:
    """Получает текущую тему обучения пользователя"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        # Получаем план обучения
        c.execute('SELECT topics FROM learning_plans WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            topics = json.loads(result[0])
            # Находим первую незавершенную тему
            for topic in topics:
                c.execute('''
                    SELECT completed FROM learning_progress 
                    WHERE user_id = ? AND topic_id = ?
                ''', (user_id, topic['name']))
                
                completed = c.fetchone()
                if not completed or not completed[0]:
                    return topic
        
        return None
    except Exception as e:
        logger.error(f"Error getting current topic: {e}")
        return None
    finally:
        conn.close()

def mark_topic_completed(user_id: int, topic_id: str, score: int = None) -> bool:
    """Отмечает тему как завершенную"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO learning_progress 
            (user_id, topic_id, completed, score, completed_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
        ''', (user_id, topic_id, score))
        
        # Обновляем общий прогресс в плане обучения
        c.execute('''
            UPDATE learning_plans 
            SET progress = (
                SELECT COUNT(*) * 100 / (
                    SELECT COUNT(*) FROM json_each(topics)
                )
                FROM learning_progress 
                WHERE user_id = ? AND completed = 1
            )
            WHERE user_id = ?
        ''', (user_id, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error marking topic as completed: {e}")
        return False
    finally:
        conn.close()

def update_user_level(user_id: int, new_level: str) -> bool:
    """Обновляет уровень пользователя"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET level = ?, last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (new_level, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating user level: {e}")
        return False
    finally:
        conn.close()

def get_user_progress(user_id: int) -> dict:
    """Получает прогресс обучения пользователя"""
    try:
        conn = sqlite3.connect('english_bot.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                u.level,
                lp.progress,
                (SELECT COUNT(*) FROM learning_progress WHERE user_id = ? AND completed = 1) as completed_topics,
                (SELECT COUNT(*) FROM json_each((SELECT topics FROM learning_plans WHERE user_id = ?))) as total_topics
            FROM users u
            LEFT JOIN learning_plans lp ON u.user_id = lp.user_id
            WHERE u.user_id = ?
        ''', (user_id, user_id, user_id))
        
        result = c.fetchone()
        
        if result:
            level, progress, completed_topics, total_topics = result
            return {
                'level': level or 'Не определен',
                'progress': progress or 0,
                'completed_topics': completed_topics or 0,
                'total_topics': total_topics or 0
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        return None
    finally:
        conn.close() 