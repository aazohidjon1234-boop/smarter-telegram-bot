#!/usr/bin/env python3
"""
Smart Bot - Advanced AI-Powered Telegram Bot
Token: 8231029002:AAF3Vz2Stsg9vCGcijtcbOIhHir4BEBTEoQ

Features:
- Advanced AI with conversation memory
- Multiple personality modes
- Smart rate limiting
- Multi-language support
- Admin controls
"""

import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import config
from handlers import handlers
from memory import memory

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """Post-initialization setup."""
    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("clear", "Clear conversation history"),
        BotCommand("personality", "Change AI personality"),
        BotCommand("calc", "Calculator"),
        BotCommand("time", "Current time"),
        BotCommand("joke", "Random joke"),
        BotCommand("fact", "Fun fact"),
        BotCommand("quote", "Inspirational quote"),
        BotCommand("8ball", "Magic 8-ball"),
        BotCommand("profile", "Your profile"),
        BotCommand("stats", "Bot statistics"),
        BotCommand("id", "Your Telegram ID"),
        BotCommand("weather", "Weather info"),
        BotCommand("news", "Latest headlines"),
        BotCommand("roast", "Playful roast"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands set")


def main():
    """Main function."""
    logger.info("=" * 50)
    logger.info(f"🤖 Starting {config.NAME} v{config.VERSION}")
    logger.info("=" * 50)
    
    # Validate configuration
    if not config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set! Check your .env file.")
        sys.exit(1)
    
    if not config.AI_API_KEY:
        logger.warning("⚠️ AI_API_KEY not set! Bot will use fallback responses.")
    
    logger.info(f"📝 AI Model: {config.AI_MODEL}")
    logger.info(f"🎭 Default Personality: {config.PERSONALITY}")
    logger.info(f"👑 Admin IDs: {config.ADMIN_IDS}")
    logger.info(f"🔧 Debug Mode: {config.DEBUG}")
    
    # Build application
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("about", handlers.about_command))
    application.add_handler(CommandHandler("personality", handlers.personality_command))
    application.add_handler(CommandHandler("clear", handlers.clear_command))
    application.add_handler(CommandHandler("calc", handlers.calc_command))
    application.add_handler(CommandHandler("time", handlers.time_command))
    application.add_handler(CommandHandler("date", handlers.time_command))
    application.add_handler(CommandHandler("joke", handlers.joke_command))
    application.add_handler(CommandHandler("fact", handlers.fact_command))
    application.add_handler(CommandHandler("quote", handlers.quote_command))
    application.add_handler(CommandHandler("8ball", handlers.eightball_command))
    application.add_handler(CommandHandler("profile", handlers.profile_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    application.add_handler(CommandHandler("id", handlers.id_command))
    application.add_handler(CommandHandler("weather", handlers.weather_command))
    application.add_handler(CommandHandler("news", handlers.news_command))
    application.add_handler(CommandHandler("roast", handlers.roast_command))
    application.add_handler(CommandHandler("broadcast", handlers.broadcast_command))
    
    # Message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text_message)
    )
    application.add_handler(
        MessageHandler(filters.VOICE, handlers.handle_voice)
    )
    application.add_handler(
        MessageHandler(filters.PHOTO, handlers.handle_photo)
    )
    application.add_handler(
        MessageHandler(filters.Sticker.ALL, handlers.handle_sticker)
    )
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    
    # Error handler
    application.add_error_handler(handlers.handle_error)
    
    logger.info("🚀 Bot is running! Press Ctrl+C to stop.")
    logger.info("=" * 50)
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)