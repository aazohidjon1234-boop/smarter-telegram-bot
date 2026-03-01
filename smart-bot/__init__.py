"""Smart Bot - Advanced AI Telegram Bot."""

__version__ = "2.0.0"
__author__ = "SmartBot Team"
__license__ = "MIT"

from .config import config, BotConfig
from .memory import memory, ConversationMemory
from .ai_engine import ai_engine, AIEngine

__all__ = [
    "config",
    "BotConfig", 
    "memory",
    "ConversationMemory",
    "ai_engine",
    "AIEngine",
]