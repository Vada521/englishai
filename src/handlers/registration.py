from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from src.database.models import save_user
from src.database.db import init_database, get_database
from src.handlers.menu import show_menu
from config import States
import logging
import sqlite3

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс регистрации или показывает меню существующему пользователю"""
    try:
        user = update.effective_user
        user_id = user.id
        logger.info(f"Starting registration for user {user_id}")
        
        # Инициализируем базу данных
        init_database()
        
        # Проверяем, существует ли пользователь
        conn = get_database()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, phone FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        conn.close()
        
        if existing_user and existing_user['first_name'] and existing_user['phone']:
            # Если пользователь уже полностью зарегистрирован, показываем главное меню
            return await show_menu(update, context)
        
        # Для нового пользователя начинаем регистрацию
        await update.message.reply_text(
            "👋 Добро пожаловать в бот для изучения английского языка!\n\n"
            "Для начала давайте познакомимся. Как я могу к вам обращаться?",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return States.AWAITING_NAME
        
    except Exception as e:
        logger.error(f"Ошибка в start_registration: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return States.START

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает имя пользователя и запрашивает телефон"""
    try:
        name = update.message.text
        context.user_data['name'] = name
        
        # Создаем клавиатуру для отправки контакта
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await update.message.reply_text(
            f"Приятно познакомиться, {name}! 👋\n\n"
            "Теперь, пожалуйста, поделитесь своим номером телефона, нажав на кнопку ниже.",
            reply_markup=keyboard
        )
        
        return States.AWAITING_PHONE
        
    except Exception as e:
        logger.error(f"Ошибка в get_name: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=ReplyKeyboardRemove()
        )
        return States.AWAITING_NAME

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает номер телефона и завершает регистрацию"""
    try:
        user = update.effective_user
        
        # Получаем номер телефона
        if update.message.contact:
            phone = update.message.contact.phone_number
        else:
            phone = update.message.text
        
        # Сохраняем пользователя с номером телефона
        save_user(
            user_id=user.id,
            username=user.username,
            first_name=context.user_data.get('name'),
            last_name=user.last_name,
            phone=phone
        )
        
        await update.message.reply_text(
            "Спасибо за регистрацию! ✅\n\n"
            "Теперь давайте определим ваш уровень английского языка. "
            "Для этого пройдите небольшой тест.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Показываем главное меню
        return await show_menu(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в get_phone: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при сохранении номера. Пожалуйста, попробуйте еще раз.",
            reply_markup=ReplyKeyboardRemove()
        )
        return States.AWAITING_PHONE

async def clear_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление данных пользователя (отладка)"""
    try:
        logger.debug("Попытка удаления данных пользователя %s", update.effective_user.id)
        from src.utils.database import get_database
        
        db = get_database()
        db.execute("DELETE FROM users WHERE user_id = ?", (update.effective_user.id,))
        logger.debug("Данные пользователя успешно удалены")
        
        await update.message.reply_text(
            "Ваши данные успешно удалены. Используйте /start для новой регистрации."
        )
    except Exception as e:
        logger.error("Ошибка при удалении данных: %s", str(e), exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при удалении данных."
        )

# Обработчик отмены регистрации
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет процесс регистрации"""
    await update.message.reply_text(
        'Регистрация отменена.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END 