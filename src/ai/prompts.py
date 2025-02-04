# Шаблоны промптов для различных задач

TEST_GENERATION_PROMPT = """Please create a test with 10 questions to determine the English level of a student. 
For each question, provide:
1. The question text
2. Three answer options (a, b, c)
3. The correct answer
4. The level this question represents (A1-C1)

Format each question as a JSON object. Return all 10 questions as a JSON array."""

LEARNING_PROGRAM_PROMPT = """Please create a personalized English learning program for a {level} level student.
The program should include:
1. Brief overview of the current level
2. Main learning objectives
3. List of modules with descriptions (Grammar, Vocabulary, Speaking, etc.)
4. Estimated time to complete each module
5. Learning recommendations

Format the response in a clear, structured way using Markdown."""

TEST_ANALYSIS_PROMPT = """Please analyze these test results and determine the user's English level:

{test_results}

Please provide:
1. Determined level (A1-C1)
2. Brief explanation of the level determination
3. Key strengths and weaknesses based on the answers
4. Recommendations for improvement""" 