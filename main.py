from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from telegram import Update
from config import TELEGRAM_TOKEN as TOKEN, States, DATABASE_PATH
from src.database.models import init_db
from src.handlers.registration import (
    start_registration,
    get_name,
    get_phone
)
from src.handlers.test import start_test, handle_test_answer, process_test_results
from src.handlers.profile import show_profile
from src.handlers.menu import show_menu
from src.handlers.learning import generate_learning_plan, start_learning, handle_lesson_completion
from src.handlers.exercise import handle_exercise
from src.handlers.learning_plan import generate_learning_plan
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    try:
        # Инициализируем базу данных
        init_db()
        
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем логирование для отслеживания регистрации обработчиков
        logger.info("Registering conversation handlers...")
        
        # Создаем обработчик разговора для регистрации
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_registration)],
            states={
                States.AWAITING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
                ],
                States.AWAITING_PHONE: [
                    MessageHandler(filters.CONTACT, get_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
                ],
                States.START: [
                    CallbackQueryHandler(start_test, pattern='^start_test$'),
                    CallbackQueryHandler(generate_learning_plan, pattern='^get_learning_program$'),
                    CallbackQueryHandler(show_menu, pattern='^main_menu$'),
                    CallbackQueryHandler(show_profile, pattern='^profile$'),
                    CallbackQueryHandler(start_learning, pattern='^start_learning$'),
                    CallbackQueryHandler(handle_exercise, pattern='^exercise_\d+_\d+$')
                ],
                States.AWAITING_LEARNING_PLAN: [
                    CallbackQueryHandler(start_learning, pattern='^start_learning$'),
                    CallbackQueryHandler(show_menu, pattern='^back_to_menu$')
                ],
                States.TEST_IN_PROGRESS: [
                    CallbackQueryHandler(handle_test_answer, pattern='^test_[abc]$'),
                    CallbackQueryHandler(show_menu, pattern='^back_to_menu$')
                ],
                States.PROFILE: [
                    CallbackQueryHandler(show_menu, pattern='^back_to_menu$')
                ],
                States.LEARNING: [
                    CallbackQueryHandler(start_learning, pattern='^start_learning$'),
                    CallbackQueryHandler(handle_lesson_completion, pattern='^complete_topic_')
                ]
            },
            fallbacks=[CommandHandler('start', start_registration)],
            per_chat=True,
            per_user=True
        )
        
        # Добавляем обработчик разговора
        application.add_handler(conv_handler)
        logger.info("Conversation handlers registered successfully")
        
        # Запускаем бота
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 