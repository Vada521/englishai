from openai import OpenAI
from typing import Dict, List, Optional
import json
import logging
from config import OPENAI_API_KEY, ASSISTANT_ID
import asyncio

# Настройка логирования
logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant_id = ASSISTANT_ID

    async def create_thread(self) -> str:
        """Создает новый тред для общения с ассистентом"""
        try:
            # Создаем пустой тред
            thread = self.client.beta.threads.create()
            
            # Добавляем сообщение в тред
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content="Please create a test with 10 questions to determine English level..."
            )
            
            logger.info(f"Successfully created thread with ID: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise

    async def generate_test_questions(self, thread_id: str) -> list:
        """Генерирует вопросы для теста"""
        try:
            prompt = """Generate exactly 10 English test questions. 
            
IMPORTANT FORMAT REQUIREMENTS:
1. Each question MUST have EXACTLY 3 answer options
2. Return ONLY a JSON array with this exact structure:
[
    {
        "question": "What is the correct form?",
        "options": ["option1", "option2", "option3"]
    }
]

Example of a valid question:
{
    "question": "Choose the correct form of 'to be':",
    "options": ["I am", "I is", "I are"]
}

DO NOT include any explanations or additional text.
DO NOT include correct answers or scoring.
ONLY return the JSON array with questions."""

            # Отправляем запрос
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Ждем завершения
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                await asyncio.sleep(1)
            
            # Получаем результат
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1,
                order='desc'
            )
            
            content = messages.data[0].content[0].text.value
            
            # Извлекаем JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Парсим JSON
            questions = json.loads(content)
            
            # Если получили словарь с ключом questions, извлекаем вопросы
            if isinstance(questions, dict) and 'questions' in questions:
                questions = questions['questions']
            
            # Проверяем формат каждого вопроса
            valid_questions = []
            for q in questions:
                if (isinstance(q, dict) and 
                    'question' in q and 
                    'options' in q and 
                    isinstance(q['options'], list) and 
                    len(q['options']) == 3):
                    valid_questions.append(q)
            
            # Если не получили достаточно вопросов, используем стандартные
            if len(valid_questions) < 10:
                logger.warning(f"Not enough valid questions ({len(valid_questions)}), using default questions")
                return self._get_default_questions()
            
            return valid_questions[:10]
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_default_questions()

    def _get_default_questions(self) -> list:
        """Возвращает стандартный набор вопросов"""
        return [
            {
                "question": "Choose the correct form of 'to be'",
                "options": ["am", "is", "are"]
            },
            {
                "question": "Select the correct past form of 'go'",
                "options": ["went", "gone", "going"]
            },
            {
                "question": "Which is correct?",
                "options": ["I can speak", "I can to speak", "I can speaking"]
            },
            {
                "question": "Choose the correct article",
                "options": ["a", "an", "the"]
            },
            {
                "question": "Select the correct preposition",
                "options": ["in", "on", "at"]
            },
            {
                "question": "Which is correct?",
                "options": ["He doesn't know", "He don't know", "He not know"]
            },
            {
                "question": "Choose the correct form",
                "options": ["I am reading", "I reading", "I read"]
            },
            {
                "question": "Select the correct word",
                "options": ["much", "many", "lot"]
            },
            {
                "question": "Which is correct?",
                "options": ["If I were you", "If I was you", "If I be you"]
            },
            {
                "question": "Choose the correct form",
                "options": ["I have been", "I has been", "I had been"]
            }
        ]

    async def analyze_test_results(self, thread_id: str, test_results: Dict) -> Dict:
        """Анализирует результаты теста и определяет уровень"""
        try:
            # Формируем отчет о результатах теста
            report = "Please analyze these test results and determine the user's English level:\n\n"
            for i, (question, answer) in enumerate(test_results.items()):
                report += f"Question {i+1}:\n"
                report += f"Q: {question}\n"
                report += f"User's answer: {answer}\n\n"

            # Отправляем отчет ассистенту
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=report
            )

            # Запускаем анализ
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                analysis = messages.data[0].content[0].text.value
                return {
                    'level': analysis.split('\n')[0].split(':')[-1].strip(),
                    'analysis': analysis
                }
            else:
                logger.error(f"Failed to analyze results. Run status: {run.status}")
                raise Exception("Failed to analyze test results")

        except Exception as e:
            logger.error(f"Error analyzing test results: {e}")
            raise

    async def generate_learning_program(self, thread_id: str, level: str) -> str:
        """Генерирует персонализированную программу обучения"""
        try:
            prompt = f"""Please create a personalized English learning program for a {level} level student.
            The program should include:
            1. Brief overview of the current level
            2. Main learning objectives
            3. List of modules with descriptions (Grammar, Vocabulary, Speaking, etc.)
            4. Estimated time to complete each module
            5. Learning recommendations
            
            Format the response in a clear, structured way using Markdown."""

            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                return messages.data[0].content[0].text.value
            else:
                logger.error(f"Failed to generate learning program. Run status: {run.status}")
                raise Exception("Failed to generate learning program")

        except Exception as e:
            logger.error(f"Error generating learning program: {e}")
            raise

    async def explain_level(self, thread_id: str, user_answers: list) -> dict:
        """Объясняет результаты теста и определяет уровень"""
        try:
            message = f"""Проанализируйте ответы студента на тест по английскому языку.
Для каждого ответа укажите, правильный он или нет, и подсчитайте общее количество правильных ответов.

Ответы студента:
{json.dumps(user_answers, ensure_ascii=False, indent=2)}

На основе анализа ответов:
1. Подсчитайте количество правильных ответов
2. Определите уровень владения английским языком (A1, A2, B1, B2 или C1)
3. Объясните студенту причины определения такого уровня
4. Укажите сильные стороны в знаниях студента
5. Укажите области, требующие улучшения
6. Дайте персональные рекомендации по улучшению уровня

Важно: 
- Обращайтесь к студенту напрямую ("Вы", "Ваш", "Вам")
- Будьте конструктивны и мотивируйте к обучению
- Ответ предоставьте в формате JSON со следующими ключами:
  - correct_answers (число)
  - level (строка)
  - explanation (строка)
  - strengths (строка)
  - weaknesses (строка)
  - recommendations (строка)
- Весь текст должен быть на русском языке

Пример формата ответа:
{{
    "correct_answers": 7,
    "level": "B1",
    "explanation": "Вы продемонстрировали средний уровень владения английским языком...",
    "strengths": "В ходе теста Вы показали...",
    "weaknesses": "Вам необходимо поработать над...",
    "recommendations": "Для улучшения уровня рекомендуем Вам..."
}}"""

            # Отправляем сообщение ассистенту
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Ждем завершения
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            while run_status.status in ['queued', 'in_progress']:
                await asyncio.sleep(1)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1,
                order='desc'
            )
            
            response_text = messages.data[0].content[0].text.value
            
            # Очищаем от markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1]
            if '```' in response_text:
                response_text = response_text.split('```')[0]
            
            response_text = response_text.strip()
            result = json.loads(response_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in explain_level: {e}")
            raise

    async def generate_learning_plan(self, thread_id: str, level: str = 'A1', strengths: str = '', weaknesses: str = '') -> dict:
        """Генерирует персонализированную программу обучения на основе уровня и результатов теста"""
        try:
            prompt = f"""Based on the student's test results:
            Current level: {level}
            Strengths: {strengths}
            Weaknesses: {weaknesses}
            
            Create a detailed learning program that will help them improve their English.
            Focus on addressing their weaknesses while building upon their strengths.
            
            Include:
            1. Current level description
            2. Target level and what needs to be achieved
            3. Detailed list of topics to study (grammar, vocabulary, speaking, etc.)
            4. Estimated time for each topic
            5. Learning objectives for each topic
            
            Return the response in the following JSON format:
            {{
                "current_level": "description of current level",
                "target_level": "next level to achieve",
                "topics": [
                    {{
                        "name": "topic name",
                        "description": "topic description",
                        "duration": "estimated time",
                        "objectives": ["objective1", "objective2", ...],
                        "completed": false
                    }}
                ]
            }}"""

            # Отправляем запрос ассистенту (убираем await)
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Ждем завершения
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            while run_status.status in ['queued', 'in_progress']:
                await asyncio.sleep(1)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            # Получаем результат (убираем await)
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1,
                order='desc'
            )
            
            content = messages.data[0].content[0].text.value
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {e}")
            raise

    def _get_fallback_learning_plan(self) -> str:
        """Возвращает заготовленный план обучения в случае ошибки"""
        return """📋 Ваш персональный план обучения:

🎯 Краткосрочные цели:
• Выучить и активно использовать 300 основных английских слов
• Понимать и использовать простые предложения на английском для повседневных ситуаций

🔮 Долгосрочные цели:
• Вести простые диалоги на английском и понимать основные вопросы
• Читать и понимать короткие тексты на английском

📚 Темы для изучения:
• Алфавит и произношение
• Основы лексики и фразы для знакомства
• Простое настоящее время (Present Simple)
• Числа, цвета, время
• Еда и напитки
• Повседневные диалоги и фразы

✍️ Рекомендуемые упражнения:
• Повторение алфавита
• Карточки со словами
• Построение предложений
• Игры на запоминание
• Ролевая игра в ресторане
• Диалоги с партнером"""

    async def start_learning_topic(self, thread_id: str, topic: dict) -> dict:
        """Начинает обучение по выбранной теме"""
        try:
            prompt = f"""Based on the topic:
            Name: {topic['name']}
            Description: {topic['description']}
            Objectives: {', '.join(topic['objectives'])}
            
            Create a detailed lesson plan that includes:
            1. Theory explanation
            2. Examples
            3. Practice exercises
            4. Quiz questions
            
            Return the response in the following JSON format:
            {{
                "theory": "detailed explanation of the topic",
                "examples": ["example1", "example2", ...],
                "exercises": [
                    {{
                        "question": "exercise question",
                        "correct_answer": "correct answer",
                        "explanation": "explanation of the answer"
                    }}
                ],
                "quiz": [
                    {{
                        "question": "quiz question",
                        "options": ["option1", "option2", "option3"],
                        "correct_answer": "correct option",
                        "explanation": "why this is correct"
                    }}
                ]
            }}"""

            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                await asyncio.sleep(1)
            
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1,
                order='desc'
            )
            
            content = messages.data[0].content[0].text.value
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error starting learning topic: {e}")
            raise

# Создаем глобальный экземпляр ассистента
assistant = AIAssistant() 