from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States, DATABASE_PATH
from src.utils.keyboards import get_main_menu_keyboard, get_profile_keyboard
from src.utils.database import get_database
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает профиль пользователя"""
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем данные пользователя из БД
        cursor.execute('''
            SELECT username, first_name, current_level, test_score, 
                   lessons_completed, last_lesson_date, registration_date
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            await query.edit_message_text(
                "Профиль не найден. Пожалуйста, зарегистрируйтесь.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
                ]])
            )
            return States.START
            
        username, first_name, level, test_score, lessons_completed, last_lesson, reg_date = user_data
        
        # Формируем сообщение с профилем
        message = (
            f"👤 Профиль пользователя\n\n"
            f"📝 Имя: {first_name or 'Не указано'}\n"
            f"🎯 Уровень: {level or 'Не определен'}\n"
            f"📊 Результат теста: {test_score or 0}/10\n"
            f"✅ Пройдено уроков: {lessons_completed or 0}\n"
            f"📅 Последний урок: {last_lesson or 'Нет'}\n"
            f"📌 Дата регистрации: {reg_date or 'Неизвестно'}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить профиль", callback_data='update_profile')],
            [InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return States.PROFILE
        
    except Exception as e:
        logger.error(f"Error showing profile: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке профиля. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
            ]])
        )
        return States.START
    finally:
        if 'conn' in locals():
            conn.close()

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает историю прогресса пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем историю тестов
        cursor.execute('''
            SELECT test_date, score, level_before, level_after
            FROM test_results
            WHERE user_id = ?
            ORDER BY test_date DESC
            LIMIT 5
        ''', (user_id,))
        
        test_results = cursor.fetchall()
        
        if test_results:
            progress_text = "📊 История вашего прогресса:\n\n"
            
            for date, score, level_before, level_after in test_results:
                progress_text += (
                    f"📅 {date}\n"
                    f"✅ Результат: {score}/10\n"
                    f"📈 Прогресс: {level_before} → {level_after}\n\n"
                )
        else:
            progress_text = "У вас пока нет истории тестирования."
        
        keyboard = [
            [InlineKeyboardButton("👤 Вернуться в профиль", callback_data='profile')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        
        await query.message.edit_text(
            progress_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        conn.close()
        return States.START
        
    except Exception as e:
        logger.error(f"Error showing progress: {e}")
        await query.message.edit_text(
            "Извините, произошла ошибка при загрузке прогресса. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(False)
        )
        return States.START 