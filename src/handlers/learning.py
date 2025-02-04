from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import States, DATABASE_PATH
from src.ai.assistant import assistant
from src.utils.keyboards import get_main_menu_keyboard, get_learning_keyboard
from src.utils.database import get_database
import sqlite3
from datetime import datetime
import logging
import json
import asyncio
from src.database.models import save_learning_plan, get_current_topic, mark_topic_completed, update_user_level, get_learning_plan
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

async def generate_learning_program(update: Update, context: ContextTypes.DEFAULT_TYPE, level: str) -> int:
    """Генерация персонализированной программы обучения"""
    user_id = update.effective_user.id
    
    try:
        # Получаем или создаем thread_id
        thread_id = context.user_data.get('thread_id')
        if not thread_id:
            thread_id = await assistant.create_thread()
            context.user_data['thread_id'] = thread_id
        
        # Генерируем программу обучения
        program = await assistant.generate_learning_program(thread_id, level)
        
        # Сохраняем информацию о программе в БД
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET current_module = 'module_1',
                last_lesson_date = ?
            WHERE user_id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
        conn.close()
        
        # Создаем клавиатуру для начала обучения
        keyboard = [
            [InlineKeyboardButton("▶️ Начать обучение", callback_data='start_module_1')],
            [InlineKeyboardButton("📋 Выбрать другой модуль", callback_data='select_module')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        
        # Отправляем программу обучения
        await update.effective_message.reply_text(
            f"🎓 Ваша персонализированная программа обучения (Уровень {level}):\n\n"
            f"{program}\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return States.LEARNING
        
    except Exception as e:
        logger.error(f"Error generating learning program: {e}")
        await update.effective_message.reply_text(
            "Извините, произошла ошибка при создании программы обучения. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(False)
        )
        return States.START

async def start_learning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс обучения"""
    query = update.callback_query
    await query.answer()
    
    # Показываем анимацию загрузки
    loading_message = await query.edit_message_text(
        "⏳ Подготавливаем материалы для обучения..."
    )
    
    try:
        # Получаем план обучения
        plan = get_learning_plan(update.effective_user.id)
        if not plan:
            await query.edit_message_text(
                "Сначала нужно пройти тест для создания плана обучения.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Пройти тест", callback_data='start_test'),
                    InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
                ]])
            )
            return States.START

        # Находим первую незавершенную тему
        current_topic = next((topic for topic in plan['topics'] if not topic.get('completed', False)), None)
        
        if not current_topic:
            await query.edit_message_text(
                "Поздравляем! Вы завершили все темы в текущем плане обучения.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Пройти новый тест", callback_data='start_test'),
                    InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
                ]])
            )
            return States.START

        # Анимация загрузки с точками
        loading_texts = [
            "⏳ Подготавливаем материалы для обучения",
            "📚 Формируем теоретическую часть",
            "✍️ Создаем практические задания",
            "🎯 Разрабатываем тесты",
            "🔄 Финальная подготовка"
        ]
        
        for i, text in enumerate(loading_texts):
            dots = "." * (i % 4)
            await loading_message.edit_text(f"{text}{dots}")
            await asyncio.sleep(0.5)

        # Получаем материалы для темы через глобальный экземпляр assistant
        lesson = await assistant.start_learning_topic(
            context.user_data.get('thread_id', ''),
            current_topic
        )

        # Разбиваем длинное сообщение на части
        text = f"📚 Тема: {current_topic['name']}\n\n"
        text += f"📝 Описание: {current_topic['description']}\n\n"
        text += "🎯 Цели:\n"
        for obj in current_topic['objectives']:
            text += f"• {obj}\n"
        text += "\n📖 Теория:\n"
        text += lesson['theory'][:2000]  # Ограничиваем длину теории

        keyboard = [
            [InlineKeyboardButton("▶️ Начать упражнения", callback_data='start_exercises')],
            [InlineKeyboardButton("◀️ Назад к плану", callback_data='show_learning_plan')]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Сохраняем данные урока в контексте
        context.user_data['current_lesson'] = lesson
        return States.LEARNING

    except BadRequest as e:
        if "Message is too long" in str(e):
            logger.error(f"Ошибка в start_learning: Message_too_long")
            await query.edit_message_text(
                "Извините, произошла ошибка при загрузке материалов. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
                ]])
            )
        return States.START
    except Exception as e:
        logger.error(f"Ошибка в start_learning: {e}")
        await query.edit_message_text(
            "Произошла ошибка при начале обучения. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data='main_menu')
            ]])
        )
        return States.START

async def start_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало модуля обучения"""
    query = update.callback_query
    await query.answer()
    
    # Здесь будет логика начала конкретного модуля
    await query.edit_message_text(
        "Модуль в разработке",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_lesson_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка завершения урока"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = update.effective_user.id
        db = get_database()
        
        # Обновляем статус текущего урока
        db.execute("""
            UPDATE learning_path 
            SET completed = TRUE, completion_date = ? 
            WHERE user_id = ? AND completed = FALSE 
            ORDER BY lesson_order 
            LIMIT 1
        """, (datetime.now().isoformat(), user_id))
        
        # Обновляем статистику пользователя
        db.execute("""
            UPDATE users 
            SET lessons_completed = lessons_completed + 1,
                last_lesson_date = ?
            WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))
        
        await query.edit_message_text(
            "Урок успешно завершен! Хотите продолжить обучение?",
            reply_markup=get_learning_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error completing lesson: {e}")
        await query.edit_message_text(
            "Произошла ошибка при завершении урока. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

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

async def format_learning_plan(plan: dict) -> str:
    """Форматирует план обучения для отображения"""
    text = "📋 Ваш персональный план обучения:\n\n"
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

async def handle_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает отображение урока"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Получаем текущую тему
        topic = context.user_data.get('current_topic')
        
        # Создаем новый тред для урока
        thread_id = await assistant.create_thread()
        
        # Генерируем контент урока
        lesson_content = await assistant.generate_lesson_content(thread_id, topic)
        
        # Сохраняем контент в контексте
        context.user_data['lesson_content'] = lesson_content
        
        # Создаем клавиатуру для навигации по уроку
        keyboard = [
            [
                InlineKeyboardButton("📖 Теория", callback_data="show_theory"),
                InlineKeyboardButton("✍️ Практика", callback_data="show_practice")
            ],
            [
                InlineKeyboardButton("🎯 Тест", callback_data="show_test"),
                InlineKeyboardButton("📝 Домашнее задание", callback_data="show_homework")
            ],
            [InlineKeyboardButton("◀️ Назад к темам", callback_data="back_to_topics")]
        ]
        
        # Отправляем обзор урока
        theory = lesson_content['theory']
        key_points = '\n'.join(f"• {point}" for point in theory['key_points'])
        
        message = (
            f"📚 *{topic['name']}*\n\n"
            f"{theory['explanation']}\n\n"
            f"*Ключевые моменты:*\n"
            f"{key_points}\n\n"
            "Выберите раздел для изучения:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return States.LEARNING_LESSON
        
    except Exception as e:
        logger.error(f"Error in handle_lesson: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке урока. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
        return States.START 