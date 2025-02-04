from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States
from src.ai.assistant import assistant
import logging
import asyncio
from src.database.models import save_learning_plan

logger = logging.getLogger(__name__)

async def generate_learning_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует персональный план обучения"""
    query = update.callback_query
    await query.answer()
    
    try:
        logger.info(f"Starting generate_learning_plan for user {update.effective_user.id}")
        
        # Начальное сообщение
        message = await query.edit_message_text("🔄 Генерирую персональный план обучения...")
        
        # Получаем результаты теста из контекста
        test_results = context.user_data.get('test_results')
        logger.info(f"Retrieved test results from context: {test_results}")
        
        if not test_results:
            logger.error("No test results found in context")
            raise Exception("No test results available")
        
        # Серия сообщений о прогрессе
        progress_messages = [
            "📚 Анализирую ваш уровень...",
            "🎯 Подбираю оптимальные материалы...",
            "📋 Составляю программу обучения...",
            "⚡️ Формирую упражнения...",
            "✨ Финальные штрихи..."
        ]
        
        # Показываем сообщения о прогрессе
        for msg in progress_messages:
            await asyncio.sleep(1.5)
            await message.edit_text(msg)
            logger.debug(f"Displayed progress message: {msg}")
        
        # Получаем thread_id из контекста или создаем новый
        thread_id = context.user_data.get('thread_id')
        logger.info(f"Retrieved thread_id from context: {thread_id}")
        
        if not thread_id:
            logger.info("Creating new thread")
            thread_id = await assistant.create_thread()
            context.user_data['thread_id'] = thread_id
            logger.info(f"Created new thread with ID: {thread_id}")
        
        # Генерируем план обучения
        level = test_results.get('level', 'A1')
        strengths = test_results.get('strengths', '')
        weaknesses = test_results.get('weaknesses', '')
        
        logger.info(f"Generating learning plan with params: level={level}, strengths={strengths}, weaknesses={weaknesses}")
        
        learning_plan = await assistant.generate_learning_plan(
            thread_id=thread_id,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        logger.info(f"Received learning plan: {learning_plan}")
        
        # Сохраняем план в базе данных
        if save_learning_plan(update.effective_user.id, learning_plan):
            logger.info("Successfully saved learning plan to database")
            
            # Форматируем план для отображения
            plan_text = format_learning_plan(learning_plan)
            logger.debug(f"Formatted plan text: {plan_text}")
            
            # Создаем клавиатуру с кнопками
            keyboard = [
                [InlineKeyboardButton("▶️ Начать обучение", callback_data='start_learning')],
                [InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')]
            ]
            
            await message.edit_text(
                plan_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info("Successfully displayed learning plan")
            
            return States.START
        else:
            logger.error("Failed to save learning plan to database")
            raise Exception("Failed to save learning plan")
        
    except Exception as e:
        logger.error(f"Error in generate_learning_plan: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка при генерации плана обучения. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
            ]])
        )
        return States.START

def format_learning_plan(plan: dict) -> str:
    """Форматирует план обучения для отображения"""
    text = f"📋 Ваш персональный план обучения:\n\n"
    text += f"📊 Текущий уровень: {plan['current_level']}\n"
    text += f"🎯 Цель: {plan['target_level']}\n\n"
    text += "📚 Темы для изучения:\n"
    
    for i, topic in enumerate(plan['topics'], 1):
        text += f"\n{i}. {topic['name']}\n"
        text += f"⏱ Длительность: {topic['duration']}\n"
        text += f"🎯 Цели:\n"
        for objective in topic['objectives']:
            text += f"• {objective}\n"
    
    return text 