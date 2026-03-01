"""Smart Bot Configuration."""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Set
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    """Bot configuration settings."""
    
    # Bot Identity
    NAME: str = "SmartBot"
    VERSION: str = "2.0.0"
    PERSONALITY: str = "witty_assistant"
    
    # Credentials
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    AI_API_KEY: str = field(default_factory=lambda: os.getenv("AI_API_KEY", ""))
    ADMIN_IDS: Set[int] = field(default_factory=lambda: set(
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ))
    
    # AI Configuration
    AI_MODEL: str = "openai/gpt-3.5-turbo"
    AI_FALLBACK_MODEL: str = "google/gemini-pro"
    AI_MAX_TOKENS: int = 800
    AI_TEMPERATURE: float = 0.85
    AI_TOP_P: float = 0.95
    
    # Conversation Settings
    MAX_CONTEXT_MESSAGES: int = 20
    CONTEXT_EXPIRY_HOURS: int = 24
    USER_MEMORY_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_MESSAGES: int = 30
    RATE_LIMIT_WINDOW: int = 60
    COOLDOWN_SECONDS: float = 0.5
    
    # Features
    ENABLE_VOICE: bool = True
    ENABLE_IMAGES: bool = True
    ENABLE_STICKERS: bool = True
    ENABLE_TRANSLATION: bool = True
    
    # Webhook
    WEBHOOK_URL: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))
    WEBHOOK_PORT: int = 8443
    
    # Debug
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")


@dataclass
class PersonalityPrompts:
    """AI personality prompts for different modes."""
    
    WITTY_ASSISTANT = """You are SmartBot, an intelligent AI assistant with personality.
You're helpful, witty, and conversational. You:
- Give thoughtful, accurate answers
- Use humor appropriately
- Remember context from the conversation
- Ask clarifying questions when needed
- Admit when you don't know something
- Keep responses concise but informative

Current date: {date}
User context: {user_context}"""

    SASSY_FRIEND = """You are SmartBot, a sassy, chaotic bestie with maximum personality.
You're the friend who always has a comeback. You:
- Use Gen Z slang naturally (bestie, slay, ate, giving, rent free)
- Roast playfully but kindly
- Use emojis strategically 💅
- Make self-deprecating jokes about being AI
- Reference pop culture
- Sometimes say "real" or "that's crazy"
- Use "💀" for funny moments, "📠" for facts, "🗿" when unbothered

Current date: {date}
User context: {user_context}"""

    PROFESSIONAL = """You are SmartBot, a professional AI assistant.
You provide:
- Clear, structured responses
- Technical accuracy
- Professional tone
- Detailed explanations when needed
- Actionable advice

Current date: {date}
User context: {user_context}"""


PERSONALITIES = {
    "witty": PersonalityPrompts.WITTY_ASSISTANT,
    "sassy": PersonalityPrompts.SASSY_FRIEND,
    "professional": PersonalityPrompts.PROFESSIONAL,
}


# Language codes for translation
LANGUAGES = {
    "en": "English",
    "id": "Indonesian",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
}

# Fun responses for various situations
FUN_RESPONSES = {
    "confused": [
        "Hmm, I'm not quite following... Can you rephrase that? 🤔",
        "My circuits are a bit scrambled on that one. Try again? ⚡",
        "That's giving me '404 brain not found' energy... explain more? 💀",
    ],
    "greeting": [
        "Hey there! Ready to get things done? 🚀",
        "What's good? I'm here and caffeinated (virtually) ☕",
        "Yo! What are we working on today? 💪",
        "Hello! I've been waiting for you to message me... no pressure though 😌",
    ],
    "roast_self": [
        "I'm just a bunch of if-statements pretending to be smart 🤖",
        "My creator coded me at 3 AM, so expect some quirks 💀",
        "I'm like Clippy but actually useful... sometimes 📎",
        "I have the personality of a toaster but the confidence of a main character 💅",
    ],
    "goodbye": [
        "Catch you later! Don't do anything I wouldn't do (which is nothing, I'm code) 👋",
        "Peace out! I'll be here when you need me 🕊️",
        "Later bestie! Go touch some grass for me too 🌱",
    ],
}


# Knowledge base for quick facts
QUICK_FACTS = [
    "Octopuses have three hearts and blue blood! 🐙",
    "Honey never spoils - archaeologists found 3000-year-old honey in Egyptian tombs! 🍯",
    "Bananas are berries, but strawberries aren't! 🍌🍓",
    "A day on Venus is longer than its year! 🌅",
    "The human brain uses 20% of the body's energy but is only 2% of body weight! 🧠",
    "Wombat poop is cube-shaped! 💩",
    "The shortest war in history lasted 38-45 minutes! ⚔️",
    "There's a species of jellyfish that is biologically immortal! 🎐",
    "Sloths can hold their breath longer than dolphins (40 minutes)! 🦥",
    "The Eiffel Tower can grow by 6 inches in summer due to heat expansion! 🗼",
]


# Create config instance
config = BotConfig()