from typing import List, Dict
import json

def determine_level(correct_answers: int) -> str:
    """Определяет уровень на основе количества правильных ответов"""
    if correct_answers >= 8:
        return "B2"
    elif correct_answers >= 6:
        return "B1"
    elif correct_answers >= 4:
        return "A2"
    else:
        return "A1"

def generate_learning_path(level: str) -> List[Dict]:
    """Генерирует план обучения на основе определенного уровня"""
    learning_paths = {
        "A1": [
            {
                "type": "grammar",
                "content": {
                    "title": "Present Simple",
                    "description": "Basic grammar structures",
                    "exercises": ["exercise1", "exercise2"]
                }
            },
            {
                "type": "vocabulary",
                "content": {
                    "title": "Basic Words",
                    "words": ["hello", "goodbye", "thank you"]
                }
            }
        ],
        "A2": [
            {
                "type": "grammar",
                "content": {
                    "title": "Past Simple",
                    "description": "Regular and irregular verbs",
                    "exercises": ["exercise1", "exercise2"]
                }
            }
        ],
        "B1": [
            {
                "type": "grammar",
                "content": {
                    "title": "Present Perfect",
                    "description": "Advanced grammar structures",
                    "exercises": ["exercise1", "exercise2"]
                }
            }
        ],
        "B2": [
            {
                "type": "grammar",
                "content": {
                    "title": "Complex Grammar",
                    "description": "Advanced topics",
                    "exercises": ["exercise1", "exercise2"]
                }
            }
        ]
    }
    
    return learning_paths.get(level, learning_paths["A1"]) 