"""Utility functions for Smart Bot."""

import re
import html
import random
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for a user."""
    message_count: int = 0
    window_start: datetime = None
    last_message: datetime = None
    
    def __post_init__(self):
        if self.window_start is None:
            self.window_start = datetime.now()


class RateLimiter:
    """Advanced rate limiter with sliding window."""
    
    def __init__(self, max_messages: int = 30, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._users: Dict[int, RateLimitInfo] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[int]]:
        """Check if user is within rate limit. Returns (allowed, retry_after)."""
        async with self._lock:
            now = datetime.now()
            
            if user_id not in self._users:
                self._users[user_id] = RateLimitInfo(
                    message_count=1,
                    window_start=now,
                    last_message=now
                )
                return True, None
            
            user_info = self._users[user_id]
            
            # Reset window if expired
            if now - user_info.window_start > timedelta(seconds=self.window_seconds):
                self._users[user_id] = RateLimitInfo(
                    message_count=1,
                    window_start=now,
                    last_message=now
                )
                return True, None
            
            # Check limit
            if user_info.message_count >= self.max_messages:
                retry_after = int(
                    (user_info.window_start + timedelta(seconds=self.window_seconds) - now).total_seconds()
                )
                return False, max(retry_after, 1)
            
            # Increment count
            user_info.message_count += 1
            user_info.last_message = now
            return True, None
    
    async def get_user_stats(self, user_id: int) -> Optional[RateLimitInfo]:
        """Get rate limit stats for a user."""
        async with self._lock:
            return self._users.get(user_id)
    
    def cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds * 2)
        self._users = {
            uid: info for uid, info in self._users.items()
            if info.window_start > cutoff
        }


class TextProcessor:
    """Text processing utilities."""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML characters."""
        return html.escape(str(text))
    
    @staticmethod
    def truncate(text: str, max_length: int = 4000, suffix: str = "...") -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Simple language detection (basic heuristic)."""
        # This is a simple heuristic - in production, use a proper library
        text_lower = text.lower()
        
        # Indonesian patterns
        indo_markers = ['yang', 'dan', 'dari', 'ini', 'itu', 'dengan', 'untuk', 'tidak', 'saya', 'kamu']
        indo_count = sum(1 for marker in indo_markers if marker in text_lower)
        
        # If enough markers found
        if indo_count >= 2:
            return "id"
        
        # Default to English
        return "en"
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Safely calculate mathematical expressions."""
        try:
            # Remove any non-math characters for safety
            cleaned = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            if not cleaned:
                return "❌ Invalid expression"
            
            # Evaluate safely
            result = eval(cleaned, {"__builtins__": {}}, {})
            return f"🧮 Result: <code>{result}</code>"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format seconds into readable duration."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        elif seconds < 86400:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"
    
    @staticmethod
    def generate_id(*args) -> str:
        """Generate a unique ID from arguments."""
        data = "".join(str(arg) for arg in args)
        return hashlib.md5(data.encode()).hexdigest()[:12]


class ContentFilter:
    """Content filtering for safety."""
    
    # Patterns to detect spam/scams
    SPAM_PATTERNS = [
        r'\b(?:buy|sell|crypto|bitcoin|investment|earn|profit)\s*\$?\d+[k%]?',
        r'\b(?:click|visit)\s+(?:here|now|link)',
        r'https?://\S+\.(?:ru|cn|tk|ml|ga)',
        r'\b(?:viagra|cialis|casino|lottery|prize|winner)\b',
    ]
    
    # Allowed commands to prevent injection
    DANGEROUS_PATTERNS = [
        r'__import__',
        r'exec\s*\(',
        r'eval\s*\(',
        r'os\.system',
        r'subprocess',
        r'import\s+os',
    ]
    
    @classmethod
    def is_spam(cls, text: str) -> bool:
        """Check if text looks like spam."""
        text_lower = text.lower()
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False
    
    @classmethod
    def is_dangerous(cls, text: str) -> bool:
        """Check for potentially dangerous content."""
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """Basic text sanitization."""
        # Remove null bytes
        text = text.replace('\x00', '')
        # Normalize whitespace
        text = ' '.join(text.split())
        return text


class WeatherAPI:
    """Simple weather API client (placeholder - integrate real API)."""
    
    @staticmethod
    async def get_weather(city: str) -> Optional[str]:
        """Get weather for a city (mock implementation)."""
        # This is a placeholder - integrate with OpenWeatherMap or similar
        return f"🌤️ Weather for {city}: This feature needs API integration!\nUse /weather <city> after adding an API key."


class NewsAPI:
    """News API client (placeholder)."""
    
    @staticmethod
    async def get_headlines(category: str = "general") -> str:
        """Get news headlines."""
        # Placeholder implementation
        headlines = [
            "🔹 AI continues to advance at rapid pace",
            "🔹 New technology breakthrough announced",
            "🔹 Scientists make surprising discovery",
        ]
        return "\n".join(headlines[:3])


# Create rate limiter instance
rate_limiter = RateLimiter()