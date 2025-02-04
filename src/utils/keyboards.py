from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("👤 Профиль", callback_data='profile')],
        [InlineKeyboardButton("📝 Пройти тест", callback_data='start_test')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_level_selection_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора способа определения уровня"""
    keyboard = [
        [InlineKeyboardButton("🎯 Пройти тест на определение уровня", callback_data='start_test')],
        [InlineKeyboardButton("📝 Выбрать уровень самостоятельно", callback_data='select_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_levels_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с уровнями английского"""
    keyboard = [
        [
            InlineKeyboardButton("A1 (Начальный)", callback_data='level_A1'),
            InlineKeyboardButton("A2 (Элементарный)", callback_data='level_A2')
        ],
        [
            InlineKeyboardButton("B1 (Средний)", callback_data='level_B1'),
            InlineKeyboardButton("B2 (Выше среднего)", callback_data='level_B2')
        ],
        [InlineKeyboardButton("C1 (Продвинутый)", callback_data='level_C1')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_test_answer_keyboard(options: Dict[str, str]) -> InlineKeyboardMarkup:
    """Создает клавиатуру с вариантами ответов на тест"""
    keyboard = []
    for key, value in options.items():
        keyboard.append([InlineKeyboardButton(f"{key.upper()}) {value}", callback_data=f"test_{key}")])
    return InlineKeyboardMarkup(keyboard)

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для профиля"""
    keyboard = [
        [InlineKeyboardButton("📊 Показать прогресс", callback_data="show_progress")],
        [InlineKeyboardButton("🔄 Пройти тест заново", callback_data="start_test")],
        [InlineKeyboardButton("⬅️ Вернуться в главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_learning_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для обучения"""
    keyboard = [
        [InlineKeyboardButton("▶️ Следующий урок", callback_data="next_lesson")],
        [InlineKeyboardButton("⏭️ Пропустить урок", callback_data="skip_lesson")],
        [InlineKeyboardButton("⬅️ Вернуться в меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard) 