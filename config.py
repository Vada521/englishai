import os
from dotenv import load_dotenv
import logging
from enum import Enum, auto

# Загружаем переменные окружения
load_dotenv()

# Настройки логирования
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'level': logging.INFO
}

# Токены и ключи
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Пути к файлам
DATABASE_PATH = 'english_bot.db'

# Состояния бота
class States(Enum):
    START = auto()
    REGISTRATION = auto()
    AWAITING_NAME = auto()
    AWAITING_PHONE = auto()
    LEVEL_SELECTION = auto()
    TEST_IN_PROGRESS = auto()
    PROFILE = auto()
    AWAITING_LEARNING_PLAN = auto()
    LEARNING = auto()
    EXERCISE = auto()

# Уровни английского
LEVELS = {
    'A1': 'Начальный',
    'A2': 'Элементарный',
    'B1': 'Средний',
    'B2': 'Выше среднего',
    'C1': 'Продвинутый'
} 