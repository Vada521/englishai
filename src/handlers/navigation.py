from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.utils.keyboards import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_text(
            text="Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error returning to menu: {e}")
        await query.message.reply_text(
            "Произошла ошибка при возврате в меню. Попробуйте снова."
        ) 