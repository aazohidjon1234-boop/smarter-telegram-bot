import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from handlers import (
    start_command, help_command, clear_command, model_command, 
    personality_command, image_command, handle_message, 
    handle_callback, handle_group_message, stats_command
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not Config.BOT_TOKEN:
        logger.error("No BOT_TOKEN found! Please check your .env file.")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("model", model_command))
    application.add_handler(CommandHandler("personality", personality_command))
    application.add_handler(CommandHandler("image", image_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_message))
    
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_message))
    
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()