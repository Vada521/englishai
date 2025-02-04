from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from config import States, DATABASE_PATH
from src.utils.keyboards import get_main_menu_keyboard, get_level_selection_keyboard
from src.database.models import init_database
from src.handlers.registration import start_registration
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.debug(f"Получена команда /start от пользователя {user.id}")
    
    # Проверяем, зарегистрирован ли пользователь
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем существование пользователя
        cursor.execute('SELECT username, first_name, current_level FROM users WHERE user_id = ?', (user.id,))
        result = cursor.fetchone()
        
        if result:
            # Если пользователь уже зарегистрирован
            logger.debug(f"Пользователь {user.id} уже зарегистрирован")
            if result[2]:  # Если уровень определен
                await update.message.reply_text(
                    f"С возвращением, {result[1]}! Выберите действие:",
                    reply_markup=get_main_menu_keyboard()
                )
                return States.START
            else:  # Если уровень еще не определен
                await update.message.reply_text(
                    f"{result[1]}, давайте определим ваш уровень английского:",
                    reply_markup=get_level_selection_keyboard()
                )
                return States.LEVEL_SELECTION
        else:
            # Если пользователь новый, начинаем регистрацию
            logger.debug(f"Начинаем регистрацию для нового пользователя {user.id}")
            return await start_registration(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        return States.START
    finally:
        conn.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего действия и возврат в главное меню"""
    user = update.effective_user
    
    # Получаем информацию о пользователе
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT level FROM users WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        # Если уровень определен, показываем главное меню
        await update.message.reply_text(
            "Действие отменено. Выберите опцию:",
            reply_markup=get_main_menu_keyboard(False)
        )
    else:
        # Если уровень не определен, предлагаем его определить
        await update.message.reply_text(
            "Действие отменено. Давайте определим ваш уровень английского:",
            reply_markup=get_level_selection_keyboard()
        )
    
    return States.START

async def handle_start_learning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки 'Начать обучение'"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем, есть ли у пользователя уровень
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT level FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        # Если уровень определен, показываем меню обучения
        keyboard = [
            [InlineKeyboardButton("📚 Начать первый урок", callback_data='start_module_1')],
            [InlineKeyboardButton("🎯 Пройти тест заново", callback_data='start_test')],
            [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')]
        ]
        await query.message.edit_text(
            f"Ваш текущий уровень: {result[0]}\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.LEARNING
    else:
        # Если уровень не определен, предлагаем пройти тест
        await query.message.edit_text(
            "Прежде чем начать обучение, давайте определим ваш уровень английского:",
            reply_markup=get_level_selection_keyboard()
        )
        return States.LEVEL_SELECTION 