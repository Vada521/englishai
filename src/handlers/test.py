from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States, DATABASE_PATH
from src.ai.assistant import assistant
from src.utils.keyboards import get_test_answer_keyboard, get_main_menu_keyboard
from src.utils.database import get_database
from src.utils.learning import determine_level, generate_learning_path
import sqlite3
from datetime import datetime
import logging
import asyncio
import json
from telegram.ext import ConversationHandler
from src.handlers.learning_plan import generate_learning_plan

logger = logging.getLogger(__name__)

async def start_level_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает тест на определение уровня"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        logger.debug(f"Начало теста для пользователя {user_id}")
        
        # Начальное сообщение
        message = await query.edit_message_text("🤔 Формирую тест для определения вашего уровня...")
        
        # Серия сообщений о прогрессе
        progress_messages = [
            "📝 Подбираю вопросы...",
            "🎯 Настраиваю сложность...",
            "⚡️ Генерирую варианты ответов...",
            "🔄 Финальная подготовка теста..."
        ]
        
        # Создаем новый тред для теста
        thread_id = await assistant.create_thread()
        context.user_data['thread_id'] = thread_id
        
        # Показываем сообщения о прогрессе во время генерации вопросов
        for msg in progress_messages:
            await asyncio.sleep(1.5)  # Пауза между сообщениями
            await message.edit_text(msg)
        
        # Получаем вопросы для теста
        questions = await assistant.generate_test_questions(thread_id)
        logger.debug(f"Generated questions: {questions}")  # Добавляем лог
        
        if not questions or not isinstance(questions, list):
            logger.error(f"Invalid questions format: {questions}")
            await message.edit_text(
                "Произошла ошибка при генерации вопросов. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            return States.START
            
        # Проверяем первый вопрос
        first_question = questions[0]
        if not isinstance(first_question, dict) or 'options' not in first_question:
            logger.error(f"Invalid first question format: {first_question}")
            await message.edit_text(
                "Произошла ошибка в формате вопросов. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            return States.START
        
        # Сохраняем вопросы и состояние в контексте
        context.user_data['questions'] = questions
        context.user_data['current_question'] = 0
        context.user_data['correct_answers'] = 0
        
        # Отправляем первый вопрос
        current_question = questions[0]
        options = {
            'a': current_question['options'][0],
            'b': current_question['options'][1],
            'c': current_question['options'][2]
        }
        
        await message.edit_text(
            f"Вопрос 1 из 10:\n\n{current_question['question']}",
            reply_markup=get_test_answer_keyboard(options)
        )
        
        return States.TEST_IN_PROGRESS
        
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        await query.edit_message_text(
            "Произошла ошибка при запуске теста. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
        return States.START

async def handle_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответы на вопросы теста"""
    query = update.callback_query
    await query.answer()
    
    try:
        answer = query.data.replace('test_', '')
        current_q = context.user_data.get('current_question', 0)
        questions = context.user_data.get('questions', [])
        
        # Проверяем, есть ли вопросы
        if not questions:
            logger.error("No questions found in context")
            await query.edit_message_text(
                "Произошла ошибка при обработке теста. Попробуйте пройти тест заново.",
                reply_markup=get_main_menu_keyboard()
            )
            return States.START
        
        # Проверяем индекс текущего вопроса
        if current_q >= len(questions):
            logger.error(f"Current question index {current_q} is out of range")
            return await process_test_results(update, context)
        
        # Получаем текущий вопрос и варианты ответов
        current_question = questions[current_q]
        logger.debug(f"Current question: {current_question}")
        
        # Проверяем структуру вопроса
        if not isinstance(current_question, dict) or 'options' not in current_question:
            logger.error(f"Invalid question format: {current_question}")
            await query.edit_message_text(
                "Произошла ошибка в формате вопроса. Попробуйте пройти тест заново.",
                reply_markup=get_main_menu_keyboard()
            )
            return States.START
            
        options = current_question['options']
        
        # Определяем выбранный ответ пользователя
        try:
            user_answer = options[ord(answer) - ord('a')]
        except (IndexError, TypeError) as e:
            logger.error(f"Error getting user answer: {e}, answer: {answer}, options: {options}")
            await query.edit_message_text(
                "Произошла ошибка при обработке ответа. Попробуйте пройти тест заново.",
                reply_markup=get_main_menu_keyboard()
            )
            return States.START
        
        # Сохраняем информацию об ответе
        answer_info = {
            'question': current_question['question'],
            'user_answer': user_answer,
            'options': options
        }
        
        if 'user_answers' not in context.user_data:
            context.user_data['user_answers'] = []
        context.user_data['user_answers'].append(answer_info)
        
        logger.info(f"User {query.from_user.id} answered question {current_q + 1}. Answer: {user_answer}")
        
        current_q += 1
        context.user_data['current_question'] = current_q
        
        if current_q < len(questions):
            # Показываем следующий вопрос
            question = questions[current_q]
            if not isinstance(question, dict) or 'options' not in question:
                logger.error(f"Invalid next question format: {question}")
                await query.edit_message_text(
                    "Произошла ошибка в следующем вопросе. Попробуйте пройти тест заново.",
                    reply_markup=get_main_menu_keyboard()
                )
                return States.START
            
            next_options = question['options']
            if not isinstance(next_options, (list, tuple)) or len(next_options) < 3:
                logger.error(f"Invalid options for next question: {next_options}")
                await query.edit_message_text(
                    "Произошла ошибка в вариантах ответа. Попробуйте пройти тест заново.",
                    reply_markup=get_main_menu_keyboard()
                )
                return States.START
            
            options = {
                'a': next_options[0],
                'b': next_options[1],
                'c': next_options[2]
            }
            
            await query.edit_message_text(
                f"Вопрос {current_q + 1} из {len(questions)}:\n\n{question['question']}",
                reply_markup=get_test_answer_keyboard(options)
            )
            return States.TEST_IN_PROGRESS
        else:
            # Показываем сообщение о загрузке
            await query.edit_message_text(
                "🔄 Анализирую ваши ответы и определяю уровень владения английским языком...\n\n"
                "Это может занять несколько секунд."
            )
            return await process_test_results(update, context)
            
    except Exception as e:
        logger.error(f"Error handling test answer: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка при обработке ответа. Попробуйте пройти тест заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return States.START

async def process_test_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает результаты теста"""
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"Processing test results for user {user_id}")
    
    try:
        if query.data == 'get_learning_program':
            logger.info("User clicked get_learning_program button")
            return await generate_learning_plan(update, context)
            
        user_answers = context.user_data.get('user_answers', [])
        thread_id = context.user_data.get('thread_id')
        
        # Получаем анализ результатов от AI
        result = await assistant.explain_level(thread_id, user_answers)
        logger.info(f"Received AI analysis: {result}")
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("📚 Получить программу обучения", callback_data='get_learning_program')],
            [InlineKeyboardButton("🔄 Пройти тест заново", callback_data='start_test')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            f"📊 Результаты теста:\n\n"
            f"✅ Правильных ответов: {result['correct_answers']} из 10\n"
            f"🎯 Ваш уровень: {result['level']}\n\n"
            f"📝 {result['explanation']}\n\n"
            f"💪 Сильные стороны:\n{result['strengths']}\n\n"
            f"❗️ Области для улучшения:\n{result['weaknesses']}\n\n"
            f"📚 Рекомендации:\n{result['recommendations']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Сохраняем результаты в контексте
        context.user_data['test_results'] = {
            'level': result['level'],
            'strengths': result['strengths'],
            'weaknesses': result['weaknesses']
        }
        
        return States.START
        
    except Exception as e:
        logger.error(f"Error processing test results: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка при обработке результатов теста. Попробуйте пройти тест заново.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Пройти тест заново", callback_data='start_test'),
                InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')
            ]])
        )
        return States.START

def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("Начать обучение", callback_data="start_learning")],
        [InlineKeyboardButton("Пройти тест заново", callback_data="start_test")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает тестирование"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Начальное сообщение
        message = await query.edit_message_text("🤔 Формирую тест для определения вашего уровня...")
        
        # Серия сообщений о прогрессе
        progress_messages = [
            "📝 Подбираю вопросы...",
            "🎯 Настраиваю сложность...",
            "⚡️ Генерирую варианты ответов...",
            "🔄 Финальная подготовка теста..."
        ]
        
        # Показываем сообщения о прогрессе
        for msg in progress_messages:
            await asyncio.sleep(1.5)  # Пауза между сообщениями
            await message.edit_text(msg)
        
        # Создаем новый тред для теста
        thread_id = await assistant.create_thread()
        context.user_data['thread_id'] = thread_id
        
        # Получаем вопросы для теста
        questions = await assistant.generate_test_questions(thread_id)
        
        # Сохраняем вопросы и состояние в контексте
        context.user_data['questions'] = questions
        context.user_data['current_question'] = 0
        context.user_data['correct_answers'] = 0
        
        # Отправляем первый вопрос
        current_question = questions[0]
        options = {
            'a': current_question['options'][0],
            'b': current_question['options'][1],
            'c': current_question['options'][2]
        }
        
        await message.edit_text(
            f"Вопрос 1 из 10:\n\n{current_question['question']}",
            reply_markup=get_test_answer_keyboard(options)
        )
        
        return States.TEST_IN_PROGRESS
        
    except Exception as e:
        logger.error(f"Ошибка в start_test: {e}")
        await query.edit_message_text(
            "Произошла ошибка при запуске теста. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Вернуться в меню", callback_data='back_to_menu')
            ]])
        )
        return States.START 