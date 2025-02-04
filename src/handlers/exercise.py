from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States, DATABASE_PATH
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает упражнения"""
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        # Получаем ID темы и номер упражнения из callback_data
        _, topic_id, exercise_num = query.data.split('_')
        topic_id = int(topic_id)
        exercise_num = int(exercise_num)
        
        # Получаем текущую тему и упражнения из контекста
        current_topic = context.user_data.get('current_topic')
        exercises = context.user_data.get('current_exercises', [])
        
        if not current_topic or not exercises:
            await query.edit_message_text(
                "Не удалось загрузить упражнение. Пожалуйста, начните обучение заново.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
                ]])
            )
            return States.START
        
        # Получаем текущее упражнение
        current_exercise = next(
            (ex for ex in exercises if ex['topic_id'] == topic_id), 
            None
        )
        
        if not current_exercise:
            await query.edit_message_text(
                "Упражнение не найдено. Пожалуйста, начните обучение заново.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
                ]])
            )
            return States.START
        
        # Формируем сообщение с упражнением
        message = (
            f"📚 Модуль: {current_topic['name']}\n"
            f"✍️ Упражнение {exercise_num}: {current_exercise['name']}\n\n"
            f"📝 {current_exercise['description']}\n\n"
            f"Тип упражнения: {current_exercise['type']}"
        )
        
        # Формируем клавиатуру
        keyboard = []
        
        # Добавляем кнопки навигации
        nav_buttons = []
        if exercise_num > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Предыдущее", callback_data=f'exercise_{topic_id}_{exercise_num-1}')
            )
        if exercise_num < len(exercises):
            nav_buttons.append(
                InlineKeyboardButton("➡️ Следующее", callback_data=f'exercise_{topic_id}_{exercise_num+1}')
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Добавляем кнопку завершения
        keyboard.append([
            InlineKeyboardButton("✅ Завершить упражнение", callback_data=f'complete_exercise_{topic_id}_{exercise_num}')
        ])
        
        # Добавляем кнопку возврата в меню
        keyboard.append([
            InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return States.EXERCISE
        
    except Exception as e:
        logger.error(f"Error handling exercise: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке упражнения. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
            ]])
        )
        return States.START 