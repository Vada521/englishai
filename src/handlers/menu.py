from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States
from src.database.db import get_database
import logging

logger = logging.getLogger(__name__)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает главное меню"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    
    # Проверяем, проходил ли пользователь тест
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT test_score, has_completed_test 
        FROM users 
        WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    has_completed_test = result['has_completed_test'] if result else False
    
    # Формируем клавиатуру в зависимости от статуса теста
    keyboard = []
    if not has_completed_test:
        keyboard = [
            [InlineKeyboardButton("📝 Пройти тест", callback_data='start_test')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📚 План обучения", callback_data='show_learning_plan')],
            [InlineKeyboardButton("👤 Профиль", callback_data='profile')]
        ]
    
    text = "🏠 Главное меню\n\nВыберите действие:"
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return States.START

async def show_learning_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает текущий план обучения"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = update.effective_user.id
        conn = get_database()
        cursor = conn.cursor()
        cursor.execute("SELECT learning_plan FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            await query.edit_message_text(
                "У вас пока нет плана обучения. Пройдите тест, чтобы получить персональный план.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Пройти тест", callback_data='start_test'),
                    InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
                ]])
            )
            return States.START
        
        plan = result[0]
        
        # Форматируем план для отображения
        text = f"📋 Ваш план обучения:\n\n"
        text += f"📊 Текущий уровень: {plan['current_level']}\n"
        text += f"🎯 Цель: {plan['target_level']}\n\n"
        text += "📚 Темы для изучения:\n"
        
        for i, topic in enumerate(plan['topics'], 1):
            completed = "✅" if topic.get('completed', False) else "⏳"
            text += f"\n{completed} {i}. {topic['name']}\n"
            text += f"⏱ Длительность: {topic['duration']}\n"
        
        keyboard = [
            [InlineKeyboardButton("▶️ Начать обучение", callback_data='start_learning')],
            [InlineKeyboardButton("🔄 Пройти тест заново", callback_data='start_test')],
            [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return States.START
        
    except Exception as e:
        logger.error(f"Error showing learning plan: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке плана обучения.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
            ]])
        )
        return States.START 