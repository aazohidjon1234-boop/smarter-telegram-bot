"""Advanced conversation memory and user context system."""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from collections import defaultdict
import asyncio


@dataclass
class UserProfile:
    """User profile with preferences and history."""
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    language_code: Optional[str]
    message_count: int = 0
    personality_preference: str = "witty"
    topics_discussed: List[str] = None
    preferences: Dict[str, Any] = None
    joined_at: float = 0
    last_active: float = 0
    
    def __post_init__(self):
        if self.topics_discussed is None:
            self.topics_discussed = []
        if self.preferences is None:
            self.preferences = {}
        if self.joined_at == 0:
            self.joined_at = time.time()


@dataclass
class MessageContext:
    """Context for a single message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ConversationMemory:
    """Advanced conversation memory with context management."""
    
    def __init__(self, max_messages: int = 20, expiry_hours: int = 24):
        self.max_messages = max_messages
        self.expiry_seconds = expiry_hours * 3600
        self._conversations: Dict[int, List[MessageContext]] = defaultdict(list)
        self._user_profiles: Dict[int, UserProfile] = {}
        self._lock = asyncio.Lock()
    
    async def add_message(self, user_id: int, role: str, content: str, 
                         metadata: Optional[Dict] = None) -> None:
        """Add a message to conversation history."""
        async with self._lock:
            context = MessageContext(
                role=role,
                content=content,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            self._conversations[user_id].append(context)
            
            # Trim old messages
            if len(self._conversations[user_id]) > self.max_messages:
                self._conversations[user_id] = self._conversations[user_id][-self.max_messages:]
            
            # Clean expired messages
            self._cleanup_expired(user_id)
    
    def _cleanup_expired(self, user_id: int):
        """Remove expired messages."""
        now = time.time()
        cutoff = now - self.expiry_seconds
        self._conversations[user_id] = [
            msg for msg in self._conversations[user_id]
            if msg.timestamp > cutoff
        ]
    
    async def get_context(self, user_id: int, max_messages: Optional[int] = None) -> List[Dict]:
        """Get conversation context for a user."""
        async with self._lock:
            self._cleanup_expired(user_id)
            messages = self._conversations.get(user_id, [])
            
            if max_messages:
                messages = messages[-max_messages:]
            
            return [msg.to_dict() for msg in messages]
    
    async def get_context_summary(self, user_id: int) -> str:
        """Get a summary of recent conversation context."""
        context = await self.get_context(user_id, max_messages=10)
        
        if not context:
            return "New conversation"
        
        # Extract topics mentioned
        topics = []
        for msg in context:
            content = msg['content'].lower()
            # Simple topic extraction
            topic_keywords = ['python', 'code', 'programming', 'help', 'question',
                            'weather', 'time', 'date', 'joke', 'fact',
                            'work', 'school', 'project', 'idea']
            for keyword in topic_keywords:
                if keyword in content:
                    topics.append(keyword)
        
        topics = list(set(topics))[:5]  # Unique, max 5
        
        if topics:
            return f"Recent topics: {', '.join(topics)}"
        return "Ongoing conversation"
    
    async def update_user_profile(self, user_id: int, **kwargs) -> None:
        """Update or create user profile."""
        async with self._lock:
            if user_id not in self._user_profiles:
                self._user_profiles[user_id] = UserProfile(
                    user_id=user_id,
                    username=kwargs.get('username'),
                    first_name=kwargs.get('first_name', 'Unknown'),
                    last_name=kwargs.get('last_name'),
                    language_code=kwargs.get('language_code')
                )
            
            profile = self._user_profiles[user_id]
            profile.last_active = time.time()
            
            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            
            profile.message_count += 1
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile."""
        async with self._lock:
            return self._user_profiles.get(user_id)
    
    async def clear_conversation(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        async with self._lock:
            if user_id in self._conversations:
                self._conversations[user_id] = []
    
    async def set_personality(self, user_id: int, personality: str) -> bool:
        """Set personality preference for user."""
        async with self._lock:
            if user_id in self._user_profiles:
                self._user_profiles[user_id].personality_preference = personality
                return True
            return False
    
    async def get_stats(self) -> Dict:
        """Get memory statistics."""
        async with self._lock:
            total_users = len(self._user_profiles)
            total_conversations = sum(
                len(conv) for conv in self._conversations.values()
            )
            
            return {
                "total_users": total_users,
                "active_conversations": len(self._conversations),
                "total_messages_stored": total_conversations,
                "memory_size_mb": self._estimate_size()
            }
    
    def _estimate_size(self) -> float:
        """Estimate memory usage in MB."""
        try:
            data = {
                "conversations": {
                    k: [asdict(m) for m in v] 
                    for k, v in self._conversations.items()
                },
                "profiles": {
                    k: asdict(v) 
                    for k, v in self._user_profiles.items()
                }
            }
            json_str = json.dumps(data)
            return len(json_str.encode('utf-8')) / (1024 * 1024)
        except Exception:
            return 0.0


# Create memory instance
memory = ConversationMemory()