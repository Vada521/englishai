CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_level TEXT,
    test_date TIMESTAMP,
    test_score INTEGER,
    lessons_completed INTEGER DEFAULT 0,
    last_lesson_date TIMESTAMP,
    test_state TEXT DEFAULT 'not_started',
    current_question INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_progress (
    user_id INTEGER,
    lesson_id INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    completion_date TIMESTAMP,
    score INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS learning_path (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    lesson_order INTEGER,
    lesson_type TEXT,
    lesson_content TEXT,
    completed BOOLEAN DEFAULT FALSE,
    completion_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
); 