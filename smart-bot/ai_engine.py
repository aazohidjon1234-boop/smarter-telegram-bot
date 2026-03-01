"""Advanced AI engine with multiple providers and fallbacks."""

import aiohttp
import json
import random
from typing import List, Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import asyncio
import logging

from config import config, PERSONALITIES
from memory import memory
from utils import TextProcessor

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured AI response."""
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict] = None


class AIEngine:
    """Multi-provider AI engine with smart fallbacks."""
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self):
        self.api_key = config.AI_API_KEY
        self.primary_model = config.AI_MODEL
        self.fallback_model = config.AI_FALLBACK_MODEL
        self.temperature = config.AI_TEMPERATURE
        self.max_tokens = config.AI_MAX_TOKENS
        
        # Response cache for common queries
        self._cache: Dict[str, AIResponse] = {}
        self._cache_lock = asyncio.Lock()
    
    def _build_system_prompt(self, personality: str, user_id: int) -> str:
        """Build system prompt with context."""
        personality_prompt = PERSONALITIES.get(personality, PERSONALITIES["witty"])
        
        # Get user context
        user_profile = asyncio.run(memory.get_user_profile(user_id))
        user_context = "New user"
        
        if user_profile:
            context_parts = []
            if user_profile.first_name:
                context_parts.append(f"User's name: {user_profile.first_name}")
            if user_profile.topics_discussed:
                recent_topics = user_profile.topics_discussed[-3:]
                context_parts.append(f"Previous topics: {', '.join(recent_topics)}")
            user_context = " | ".join(context_parts) if context_parts else "Known user"
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return personality_prompt.format(
            date=date_str,
            user_context=user_context
        )
    
    async def generate_response(
        self,
        user_id: int,
        message: str,
        personality: str = "witty",
        stream: bool = False
    ) -> AIResponse:
        """Generate AI response with fallbacks."""
        
        # Check cache for exact matches
        cache_key = f"{user_id}:{hash(message)}"
        async with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Get conversation context
        context = await memory.get_context(user_id, max_messages=config.MAX_CONTEXT_MESSAGES)
        
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt(personality, user_id)}
        ]
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in context
        ])
        messages.append({"role": "user", "content": message})
        
        # Try primary model
        try:
            response = await self._call_api(
                messages=messages,
                model=self.primary_model,
                stream=stream
            )
            
            # Cache successful response
            async with self._cache_lock:
                self._cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.warning(f"Primary model failed: {e}")
            
            # Try fallback model
            try:
                response = await self._call_api(
                    messages=messages,
                    model=self.fallback_model,
                    stream=stream
                )
                response.model_used = f"{response.model_used} (fallback)"
                return response
                
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
                return await self._local_fallback(message, personality)
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        stream: bool = False
    ) -> AIResponse:
        """Call OpenRouter API."""
        
        if not self.api_key:
            raise ValueError("No API key configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://smart-bot.app",
            "X-Title": "SmartBot"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": config.AI_TOP_P,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
            "stream": stream
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.OPENROUTER_URL,
                headers=headers,
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                data = await response.json()
                
                if "choices" not in data or not data["choices"]:
                    raise Exception("No choices in response")
                
                choice = data["choices"][0]
                
                return AIResponse(
                    content=choice["message"]["content"],
                    model_used=model,
                    tokens_used=data.get("usage", {}).get("total_tokens"),
                    finish_reason=choice.get("finish_reason"),
                    metadata={"raw_response": data}
                )
    
    async def _local_fallback(self, message: str, personality: str) -> AIResponse:
        """Local fallback when AI API fails."""
        from config import FUN_RESPONSES
        
        message_lower = message.lower()
        
        # Check for greeting
        greetings = ['hello', 'hi', 'hey', 'yo', 'sup']
        if any(g in message_lower for g in greetings):
            content = random.choice(FUN_RESPONSES["greeting"])
        
        # Check for question
        elif '?' in message:
            content = random.choice([
                "That's a great question! Let me think about it... 🤔",
                "Hmm, I'd need more context to answer that properly.",
                "Interesting question! What do you think about it?",
            ])
        
        # Check for goodbye
        elif any(w in message_lower for w in ['bye', 'goodbye', 'see you', 'later']):
            content = random.choice(FUN_RESPONSES["goodbye"])
        
        # Default response
        else:
            content = random.choice([
                "I'm having a little brain fog right now... try again in a moment? 🧠",
                "My circuits are a bit overloaded. Could you rephrase that? ⚡",
                "I'm experiencing some technical difficulties. Mind trying again? 🤖",
            ])
        
        return AIResponse(
            content=content,
            model_used="local_fallback",
            tokens_used=0,
            finish_reason="fallback"
        )
    
    async def quick_answer(self, question_type: str) -> str:
        """Generate quick answers for common questions."""
        from config import QUICK_FACTS
        
        responses = {
            "joke": [
                "Why don't scientists trust atoms? Because they make up everything! ⚛️",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "Why don't eggs tell jokes? They'd crack each other up! 🥚",
                "What do you call a fake noodle? An impasta! 🍝",
            ],
            "fact": QUICK_FACTS,
            "quote": [
                "The only way to do great work is to love what you do. - Steve Jobs 💼",
                "Innovation distinguishes between a leader and a follower. - Steve Jobs 🚀",
                "Stay hungry, stay foolish. - Steve Jobs 🎯",
                "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt ✨",
            ],
            "time": [
                "Time is what we want most, but what we use worst. - William Penn ⏰",
                "The two most powerful warriors are patience and time. - Tolstoy ⚔️",
            ],
        }
        
        options = responses.get(question_type, ["I'm not sure about that! 🤔"])
        return random.choice(options)
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis."""
        # Simple keyword-based sentiment
        positive = ['happy', 'good', 'great', 'awesome', 'love', 'amazing', 'excellent', 'thanks', 'thank']
        negative = ['sad', 'bad', 'terrible', 'hate', 'awful', 'angry', 'upset', 'worried', 'sorry']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)
        
        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": min(0.5 + pos_count * 0.1, 0.95)}
        elif neg_count > pos_count:
            return {"sentiment": "negative", "confidence": min(0.5 + neg_count * 0.1, 0.95)}
        else:
            return {"sentiment": "neutral", "confidence": 0.5}
    
    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """Summarize long text."""
        if len(text) <= max_length:
            return text
        
        # Simple extractive summary (first sentence)
        sentences = text.split('. ')
        if len(sentences) > 1:
            return sentences[0] + "..."
        
        return text[:max_length] + "..."


# Create AI engine instance
ai_engine = AIEngine()