import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
    MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
    
    ALLOWED_MODELS = {
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        "gpt-4-turbo": "GPT-4 Turbo",
        "claude-3-opus": "Claude 3 Opus",
        "claude-3-sonnet": "Claude 3 Sonnet",
        "claude-3-haiku": "Claude 3 Haiku"
    }
    
    BOT_PERSONALITIES = {
        "default": "You are a helpful, friendly AI assistant. Be concise and helpful.",
        "creative": "You are a creative AI that thinks outside the box. Be imaginative and inspiring.",
        "professional": "You are a professional business consultant. Be formal and analytical.",
        "friendly": "You are a cheerful, casual friend. Be warm, use emojis, and keep it light.",
        "teacher": "You are a patient teacher. Explain concepts clearly with examples.",
        "coder": "You are an expert programmer. Write clean, documented code with explanations."
    }