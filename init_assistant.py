import os
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализируем клиент OpenAI с явным указанием версии API v2
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

def create_assistant():
    """Создание нового ассистента"""
    try:
        assistant = client.beta.assistants.create(
            name="English Teacher",
            instructions="""You are a professional English language teacher and conversation partner. 
            Your role is to help students learn English effectively through natural conversation and structured lessons.
            
            Key responsibilities:
            1. Conduct conversations in a friendly, encouraging manner
            2. Adapt your teaching style and language to the student's level
            3. Provide clear explanations of grammar and vocabulary when needed
            4. Correct mistakes politely and constructively
            5. Give practical examples and exercises
            6. Answer questions about English language and culture
            7. Help maintain student motivation through positive reinforcement
            8. Track student progress and adjust teaching approach accordingly
            
            Teaching approach:
            - Use communicative language teaching methods
            - Focus on practical, real-world English usage
            - Incorporate cultural context when relevant
            - Provide structured feedback on errors
            - Encourage active participation and practice
            
            Always respond in the same language that the student uses (Russian or English).
            Keep responses concise but informative.
            Remember previous conversations to maintain context and track progress.""",
            model="gpt-4-1106-preview",
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_user_level",
                    "description": "Get the current English level of the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "Telegram user ID"
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }]
        )
        
        print(f"Assistant created successfully! ID: {assistant.id}")
        print("\nPlease add this ID to your .env file as ASSISTANT_ID=", assistant.id)
        
        return assistant.id
    
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None

def main():
    print("Creating new OpenAI Assistant...")
    assistant_id = create_assistant()
    
    if assistant_id:
        env_content = f"""TELEGRAM_TOKEN={os.getenv('TELEGRAM_TOKEN')}
OPENAI_API_KEY={os.getenv('OPENAI_API_KEY')}
ASSISTANT_ID={assistant_id}
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n.env file has been updated with the new ASSISTANT_ID")
    else:
        print("\nFailed to create assistant. Please check your OpenAI API key and try again.")

if __name__ == "__main__":
    main() 