import sqlite3
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    model TEXT DEFAULT 'gpt-4o',
                    personality TEXT DEFAULT 'default',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    title TEXT,
                    allowed INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
                ON conversations(user_id)
            ''')
            
            conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def update_user_activity(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP,
                    message_count = message_count + 1
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def get_user_settings(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT model, personality FROM users WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                return {"model": result[0], "personality": result[1]}
            return {"model": Config.DEFAULT_MODEL, "personality": "default"}
    
    def update_user_settings(self, user_id, model=None, personality=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if model:
                cursor.execute('UPDATE users SET model = ? WHERE user_id = ?', (model, user_id))
            if personality:
                cursor.execute('UPDATE users SET personality = ? WHERE user_id = ?', (personality, user_id))
            conn.commit()
    
    def add_message(self, user_id, role, content):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            ''', (user_id, role, content))
            conn.commit()
    
    def get_conversation_history(self, user_id, limit=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            limit = limit or Config.MAX_CONTEXT_MESSAGES
            cursor.execute('''
                SELECT role, content FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    
    def clear_history(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def add_group(self, group_id, title):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO groups (group_id, title)
                VALUES (?, ?)
            ''', (group_id, title))
            conn.commit()
    
    def is_group_allowed(self, group_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT allowed FROM groups WHERE group_id = ?', (group_id,))
            result = cursor.fetchone()
            return result is None or result[0] == 1
    
    def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM groups')
            total_groups = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "total_groups": total_groups
            }