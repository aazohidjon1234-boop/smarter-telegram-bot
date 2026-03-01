"""Smart Bot command and message handlers."""

import logging
import asyncio
import random
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes

from config import config, FUN_RESPONSES, QUICK_FACTS
from memory import memory
from ai_engine import ai_engine, AIResponse
from utils import (
    RateLimiter, rate_limiter, TextProcessor, 
    ContentFilter, WeatherAPI, NewsAPI
)

logger = logging.getLogger(__name__)

# Bot start time for uptime
START_TIME = datetime.now()


class BotHandlers:
    """Main bot handlers class."""
    
    def __init__(self):
        self.rate_limiter = rate_limiter
    
    async def _check_rate_limit(self, update: Update) -> bool:
        """Check rate limit and notify user if exceeded."""
        user_id = update.effective_user.id
        allowed, retry_after = await self.rate_limiter.check_rate_limit(user_id)
        
        if not allowed:
            await update.message.reply_text(
                f"⏳ Whoa there! You're sending messages too fast.\n"
                f"Please wait {retry_after} seconds before trying again."
            )
            return False
        return True
    
    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in config.ADMIN_IDS
    
    # ==================== COMMAND HANDLERS ====================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        # Update user profile
        await memory.update_user_profile(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        
        welcome_text = f"""
👋 <b>Welcome, {TextProcessor.escape_html(user.first_name)}!</b>

I'm <b>{config.NAME}</b> v{config.VERSION}, your intelligent AI assistant! 🚀

<b>What I can do:</b>
💬 <b>Smart Chat</b> - Natural conversations with memory
🎭 <b>Personalities</b> - Switch between witty, sassy, or professional
🌐 <b>Multi-language</b> - I can chat in many languages
🧮 <b>Tools</b> - Calculator, weather, news, and more
🎮 <b>Fun</b> - Jokes, facts, quotes, and games

<b>Get started:</b>
Just send me any message and I'll respond!
Or use /help to see all commands.

<i>Type /personality to change my vibe! 💅</i>
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💬 Start Chatting", callback_data="chat_mode"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ],
            [
                InlineKeyboardButton("🎭 Change Personality", callback_data="personality_menu"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = f"""
<b>📚 {config.NAME} Command Guide</b>

<b>💬 Core Commands:</b>
/start - Start the bot
/help - Show this help message
/clear - Clear conversation history
/personality - Change AI personality

<b>🔧 Utility Commands:</b>
/calc [expression] - Calculator (e.g., /calc 2+2*3)
/time - Current time
/date - Today's date
/weather [city] - Weather info (requires API)
/news - Latest headlines

<b>🎮 Fun Commands:</b>
/joke - Random joke
/fact - Interesting fact
/quote - Inspirational quote
/8ball [question] - Magic 8-ball
/roast - Playful roast

<b>👤 User Commands:</b>
/profile - Your profile info
/stats - Your usage statistics
/id - Your Telegram ID

<b>⚙️ Settings:</b>
/language - Change language preference

<b>👑 Admin Commands:</b>
/broadcast [msg] - Send to all users
/botstats - Detailed bot statistics
/users - List all users
/maintenance - Toggle maintenance mode
        """
        
        await update.message.reply_html(help_text)
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command."""
        uptime = datetime.now() - START_TIME
        mem_stats = await memory.get_stats()
        
        about_text = f"""
<b>🤖 About {config.NAME}</b>

<b>Version:</b> {config.VERSION}
<b>AI Model:</b> {config.AI_MODEL}
<b>Uptime:</b> {TextProcessor.format_duration(int(uptime.total_seconds()))}

<b>📊 Statistics:</b>
👥 Total Users: {mem_stats['total_users']}
💬 Active Conversations: {mem_stats['active_conversations']}
📝 Messages Stored: {mem_stats['total_messages_stored']}
💾 Memory Usage: {mem_stats['memory_size_mb']:.2f} MB

<b>✨ Features:</b>
✅ Advanced AI with context memory
✅ Multiple personality modes
✅ Multi-language support
✅ Smart rate limiting
✅ Content filtering
✅ Admin controls

<i>Built with ❤️ and lots of coffee ☕</i>
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(about_text, reply_markup=reply_markup)
    
    async def personality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /personality command."""
        user_id = update.effective_user.id
        
        current = "witty"
        profile = await memory.get_user_profile(user_id)
        if profile:
            current = profile.personality_preference
        
        text = f"""
<b>🎭 Choose Your Personality</b>

Current: <b>{current.title()}</b>

<b>Available personalities:</b>
🤓 <b>Witty</b> - Helpful with a sense of humor
💅 <b>Sassy</b> - Chaotic bestie energy
👔 <b>Professional</b> - Business mode activated

Select one below:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🤓 Witty", callback_data="personality_witty"),
                InlineKeyboardButton("💅 Sassy", callback_data="personality_sassy")
            ],
            [
                InlineKeyboardButton("👔 Professional", callback_data="personality_professional")
            ],
            [InlineKeyboardButton("🔄 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(text, reply_markup=reply_markup)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command."""
        user_id = update.effective_user.id
        await memory.clear_conversation(user_id)
        
        responses = [
            "🧹 Memory wiped! Starting fresh! 👋",
            "🗑️ Conversation cleared! Who are you again? Just kidding! 😄",
            "✨ Clean slate! Let's start over! 🆕",
            "🧠 Brain reset complete! Ready for new adventures! 🚀"
        ]
        
        await update.message.reply_text(random.choice(responses))
    
    async def calc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /calc command."""
        if not context.args:
            await update.message.reply_html(
                "🧮 <b>Calculator</b>\n\n"
                "Usage: <code>/calc [expression]</code>\n\n"
                "Examples:\n"
                "<code>/calc 2+2</code>\n"
                "<code>/calc (10-5)*3</code>\n"
                "<code>/calc 100/4</code>"
            )
            return
        
        expression = " ".join(context.args)
        result = TextProcessor.calculate(expression)
        await update.message.reply_html(result)
    
    async def time_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /time command."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %B %d, %Y")
        
        await update.message.reply_html(
            f"🕐 <b>Current Time</b>\n\n"
            f"📅 {date_str}\n"
            f"⏰ {time_str}\n\n"
            f"<i>Server time (UTC)</i>"
        )
    
    async def joke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /joke command."""
        joke = await ai_engine.quick_answer("joke")
        await update.message.reply_text(f"😄 {joke}")
    
    async def fact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fact command."""
        fact = await ai_engine.quick_answer("fact")
        await update.message.reply_text(f"🤯 {fact}")
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quote command."""
        quote = await ai_engine.quick_answer("quote")
        await update.message.reply_text(f"💭 {quote}")
    
    async def eightball_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /8ball command."""
        responses = [
            "🎱 It is certain",
            "🎱 Without a doubt",
            "🎱 You may rely on it",
            "🎱 Yes, definitely",
            "🎱 As I see it, yes",
            "🎱 Most likely",
            "🎱 Outlook good",
            "🎱 Yes",
            "🎱 Signs point to yes",
            "🎱 Reply hazy, try again",
            "🎱 Ask again later",
            "🎱 Better not tell you now",
            "🎱 Cannot predict now",
            "🎱 Concentrate and ask again",
            "🎱 Don't count on it",
            "🎱 My reply is no",
            "🎱 My sources say no",
            "🎱 Outlook not so good",
            "🎱 Very doubtful"
        ]
        
        question = " ".join(context.args) if context.args else "your question"
        answer = random.choice(responses)
        
        await update.message.reply_html(
            f"❓ <b>Question:</b> {TextProcessor.escape_html(question)}\n\n"
            f"{answer}"
        )
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command."""
        user = update.effective_user
        profile = await memory.get_user_profile(user.id)
        
        if not profile:
            await update.message.reply_text("❌ No profile found. Send a message first!")
            return
        
        persona = profile.personality_preference
        persona_emoji = {"witty": "🤓", "sassy": "💅", "professional": "👔"}.get(persona, "🤖")
        
        text = f"""
<b>👤 Your Profile</b>

<b>Name:</b> {TextProcessor.escape_html(profile.first_name)}
<b>Username:</b> @{profile.username or 'N/A'}
<b>ID:</b> <code>{profile.user_id}</code>
<b>Language:</b> {profile.language_code or 'N/A'}

<b>🎭 Personality:</b> {persona_emoji} {persona.title()}
<b>💬 Messages:</b> {profile.message_count}
<b>📅 Joined:</b> {datetime.fromtimestamp(profile.joined_at).strftime('%Y-%m-%d')}
        """
        
        await update.message.reply_html(text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        user_id = update.effective_user.id
        
        if not await self._is_admin(user_id):
            # Show user their stats
            profile = await memory.get_user_profile(user_id)
            if profile:
                await update.message.reply_html(
                    f"<b>📊 Your Statistics</b>\n\n"
                    f"💬 Messages sent: {profile.message_count}\n"
                    f"🎭 Personality: {profile.personality_preference.title()}\n"
                    f"⏰ Last active: {datetime.fromtimestamp(profile.last_active).strftime('%H:%M:%S')}"
                )
            return
        
        # Admin stats
        mem_stats = await memory.get_stats()
        uptime = datetime.now() - START_TIME
        
        text = f"""
<b>👑 Admin Statistics</b>

<b>⏱️ Uptime:</b> {TextProcessor.format_duration(int(uptime.total_seconds()))}

<b>👥 Users:</b> {mem_stats['total_users']}
<b>💬 Conversations:</b> {mem_stats['active_conversations']}
<b>📝 Messages:</b> {mem_stats['total_messages_stored']}
<b>💾 Memory:</b> {mem_stats['memory_size_mb']:.2f} MB

<b>⚙️ Config:</b>
AI Enabled: {'✅' if config.AI_API_KEY else '❌'}
Debug Mode: {'✅' if config.DEBUG else '❌'}
        """
        
        await update.message.reply_html(text)
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weather command."""
        if not context.args:
            await update.message.reply_text(
                "🌤️ Usage: /weather [city name]\n\n"
                "Example: /weather Jakarta"
            )
            return
        
        city = " ".join(context.args)
        await update.message.reply_text(f"🔍 Looking up weather for {city}...")
        
        # Placeholder - integrate real weather API
        weather = await WeatherAPI.get_weather(city)
        await update.message.reply_text(weather or "❌ Weather service unavailable")
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /news command."""
        await update.message.reply_text("📰 Fetching latest headlines...")
        headlines = await NewsAPI.get_headlines()
        await update.message.reply_html(f"<b>📰 Latest Headlines</b>\n\n{headlines}")
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command."""
        user = update.effective_user
        chat = update.effective_chat
        
        text = f"""
<b>🆔 Your Information</b>

<b>User ID:</b> <code>{user.id}</code>
<b>Username:</b> @{user.username or 'N/A'}
<b>First Name:</b> {TextProcessor.escape_html(user.first_name)}
<b>Last Name:</b> {TextProcessor.escape_html(user.last_name or 'N/A')}
        """
        
        if chat.type != "private":
            text += f"""
            
<b>Chat Information:</b>
<b>Chat ID:</b> <code>{chat.id}</code>
<b>Chat Type:</b> {chat.type}
<b>Title:</b> {TextProcessor.escape_html(chat.title or 'N/A')}
            """
        
        await update.message.reply_html(text)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command (admin only)."""
        user_id = update.effective_user.id
        
        if not await self._is_admin(user_id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /broadcast [your message]")
            return
        
        message = " ".join(context.args)
        
        # Get all users
        stats = await memory.get_stats()
        
        status_msg = await update.message.reply_text(
            f"📤 Broadcasting to {stats['total_users']} users..."
        )
        
        # In a real implementation, you'd fetch from database
        sent = 0
        failed = 0
        
        await status_msg.edit_text(
            f"✅ Broadcast complete!\n"
            f"📤 Sent: {sent}\n"
            f"❌ Failed: {failed}"
        )
    
    async def roast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /roast command."""
        roasts = [
            "You're like a cloud. When you disappear, it's a beautiful day! ☁️",
            "I'd agree with you but then we'd both be wrong. 🤷",
            "You're not stupid; you just have bad luck thinking. 🧠",
            "I'm not saying I hate you, but I would unplug your life support to charge my phone. 📱",
            "You're the reason the gene pool needs a lifeguard. 🏊",
            "I'm jealous of people who don't know you. 😌",
            "You're not dumb. You just have bad luck when it comes to thinking. 💭",
            "I'd explain it to you, but I left my crayons at home. 🖍️",
            "You're like a software update. Whenever I see you, I think 'not now'. 📱",
            "You bring everyone so much joy... when you leave the room! 🚪",
        ]
        
        target = " ".join(context.args) if context.args else "you"
        roast = random.choice(roasts)
        
        await update.message.reply_text(
            f"🔥 <b>Roast for {TextProcessor.escape_html(target)}</b>\n\n"
            f"{roast}",
            parse_mode="HTML"
        )
    
    # ==================== MESSAGE HANDLERS ====================
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages."""
        if not await self._check_rate_limit(update):
            return
        
        user = update.effective_user
        message_text = update.message.text
        
        # Skip commands
        if message_text.startswith('/'):
            return
        
        # Update user profile
        await memory.update_user_profile(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Check for spam
        if ContentFilter.is_spam(message_text):
            logger.warning(f"Spam detected from user {user.id}")
            await update.message.reply_text(
                "⚠️ That message looks suspicious. Let's keep it friendly!"
            )
            return
        
        # Get user's preferred personality
        profile = await memory.get_user_profile(user.id)
        personality = profile.personality_preference if profile else "witty"
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        try:
            # Generate AI response
            response = await ai_engine.generate_response(
                user_id=user.id,
                message=message_text,
                personality=personality
            )
            
            # Store conversation
            await memory.add_message(user.id, "user", message_text)
            await memory.add_message(
                user.id, "assistant", response.content,
                metadata={"model": response.model_used}
            )
            
            # Send response
            await update.message.reply_text(response.content)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await update.message.reply_text(
                "Oops, my brain had a hiccup! 🧠💥 Try again?"
            )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        if not config.ENABLE_VOICE:
            await update.message.reply_text("🎙️ Voice messages are disabled.")
            return
        
        await update.message.reply_text(
            "🎙️ I heard you! (Voice transcription coming soon...)\n\n"
            "For now, please type your message! ⌨️"
        )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages."""
        if not config.ENABLE_IMAGES:
            await update.message.reply_text("🖼️ Image processing is disabled.")
            return
        
        await update.message.reply_text(
            "🖼️ Nice pic! I can see it but can't analyze images yet.\n"
            "Tell me about it in text! 💬"
        )
    
    async def handle_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle stickers."""
        if not config.ENABLE_STICKERS:
            return
        
        sticker_responses = [
            "Nice sticker! 😎",
            "I see you! 👀",
            "Sticker game strong! 💪",
            "Expressive! 🎨",
            "👍",
        ]
        
        # 30% chance to respond to stickers
        if random.random() < 0.3:
            await update.message.reply_text(random.choice(sticker_responses))
    
    # ==================== CALLBACK HANDLERS ====================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            keyboard = [
                [
                    InlineKeyboardButton("💬 Start Chatting", callback_data="chat_mode"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("🎭 Personality", callback_data="personality_menu"),
                    InlineKeyboardButton("ℹ️ About", callback_data="about")
                ]
            ]
            await query.edit_message_text(
                "<b>🤖 Main Menu</b>\n\nWhat would you like to do?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        
        elif data == "chat_mode":
            await query.edit_message_text(
                "<b>💬 Chat Mode Activated!</b>\n\n"
                "Just send me any message and I'll respond!\n"
                "I remember our conversation and learn your preferences. 🧠\n\n"
                "<i>Use /personality to change my vibe!</i>",
                parse_mode="HTML"
            )
        
        elif data == "help":
            help_text = """
<b>Quick Commands:</b>
/start - Start the bot
/clear - Clear memory
/joke - Random joke
/fact - Fun fact
/8ball - Magic 8-ball

Use /help for full command list!
            """
            await query.edit_message_text(help_text, parse_mode="HTML")
        
        elif data == "about":
            uptime = datetime.now() - START_TIME
            await query.edit_message_text(
                f"<b>🤖 {config.NAME} v{config.VERSION}</b>\n\n"
                f"An intelligent AI bot with:\n"
                f"• Natural conversations\n"
                f"• Multiple personalities\n"
                f"• Smart memory\n"
                f"• Multi-language support\n\n"
                f"<i>Uptime: {TextProcessor.format_duration(int(uptime.total_seconds()))}</i>",
                parse_mode="HTML"
            )
        
        elif data == "personality_menu":
            keyboard = [
                [
                    InlineKeyboardButton("🤓 Witty", callback_data="personality_witty"),
                    InlineKeyboardButton("💅 Sassy", callback_data="personality_sassy")
                ],
                [
                    InlineKeyboardButton("👔 Professional", callback_data="personality_professional")
                ],
                [InlineKeyboardButton("🔄 Back", callback_data="main_menu")]
            ]
            await query.edit_message_text(
                "<b>🎭 Choose Personality</b>\n\n"
                "Select your preferred AI personality:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        
        elif data.startswith("personality_"):
            personality = data.replace("personality_", "")
            user_id = update.effective_user.id
            
            await memory.set_personality(user_id, personality)
            
            emoji = {"witty": "🤓", "sassy": "💅", "professional": "👔"}.get(personality, "🤖")
            
            await query.edit_message_text(
                f"{emoji} <b>Personality Updated!</b>\n\n"
                f"Now chatting in <b>{personality.title()}</b> mode!\n\n"
                f"Start chatting to see the difference! 💬",
                parse_mode="HTML"
            )
    
    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Error: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Oops! Something went wrong. Please try again!"
                )
            except Exception:
                pass


# Create handlers instance
handlers = BotHandlers()