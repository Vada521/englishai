LEVEL_TEST_QUESTIONS = [
    {
        "question": "Choose the correct answer: 'I ___ a student.'",
        "options": {
            "a": "am",
            "b": "is",
            "c": "are"
        },
        "correct": "a",
        "level": "A1"
    },
    {
        "question": "Select the correct past tense: 'Yesterday I ___ to the store.'",
        "options": {
            "a": "go",
            "b": "went",
            "c": "gone"
        },
        "correct": "b",
        "level": "A2"
    },
    {
        "question": "Choose the correct conditional: 'If I ___ rich, I would buy a house.'",
        "options": {
            "a": "am",
            "b": "were",
            "c": "would be"
        },
        "correct": "b",
        "level": "B1"
    }
    # Добавим еще вопросы позже
]

def calculate_level(correct_answers: int) -> str:
    """Определяет уровень на основе количества правильных ответов"""
    if correct_answers <= 3:
        return "A1"
    elif correct_answers <= 6:
        return "A2"
    elif correct_answers <= 9:
        return "B1"
    elif correct_answers <= 12:
        return "B2"
    else:
        return "C1" 