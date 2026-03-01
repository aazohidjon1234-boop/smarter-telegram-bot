from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from ai_engine import AIEngine
from config import Config

db = Database()

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Change Personality", callback_data="personality")],
        [InlineKeyboardButton("Change Model", callback_data="model")],
        [InlineKeyboardButton("Generate Image", callback_data="image")],
        [InlineKeyboardButton("Clear History", callback_data="clear")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = f"""Hello {user.first_name}!

I'm your AI assistant powered by GPT-4. I can:
- Answer questions and have conversations
- Generate images with DALL-E 3
- Remember context from our chats
- Work in groups (mention me with @username)

Use the buttons below or just send me a message!

Commands:
/help - Show help
/clear - Clear conversation history
/image <prompt> - Generate an image
/model - Change AI model
/personality - Change my personality
"""
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """Available Commands:

Basic:
/start - Start the bot
/help - Show this help
/clear - Clear conversation history

AI Settings:
/model - Choose AI model (GPT-4o, etc.)
/personality - Change my personality

Features:
/image <prompt> - Generate image with DALL-E 3

Group Chat:
Add me to a group and mention me with @username to get a response.

Tips:
- I remember the last 20 messages for context
- Use /clear if I start acting weird
- Different personalities work better for different tasks
"""
    await update.message.reply_text(help_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.clear_history(user_id)
    await update.message.reply_text("Conversation history cleared! Starting fresh.")

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for model_id, model_name in Config.ALLOWED_MODELS.items():
        keyboard.append([InlineKeyboardButton(model_name, callback_data=f"set_model:{model_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an AI model:", reply_markup=reply_markup)

async def personality_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for pers_id, pers_desc in Config.BOT_PERSONALITIES.items():
        display_name = pers_id.capitalize()
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"set_personality:{pers_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose my personality:", reply_markup=reply_markup)

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /image <description>\n\nExample: /image a cat wearing a spacesuit on mars")
        return
    
    prompt = " ".join(context.args)
    await update.message.reply_text("Generating image, please wait...")
    
    image_url = await AIEngine.generate_image(prompt)
    
    if image_url and not isinstance(image_url, tuple):
        await update.message.reply_photo(photo=image_url, caption=f"Prompt: {prompt}")
    else:
        error_msg = image_url[1] if isinstance(image_url, tuple) else "Unknown error"
        await update.message.reply_text(f"Failed to generate image: {error_msg}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    db.add_user(update.effective_user.id, update.effective_user.username, 
                update.effective_user.first_name, update.effective_user.last_name)
    db.update_user_activity(user_id)
    
    settings = db.get_user_settings(user_id)
    
    thinking_msg = await update.message.reply_text("Thinking...")
    
    db.add_message(user_id, "user", user_message)
    
    history = db.get_conversation_history(user_id)
    
    response = await AIEngine.get_response(history, settings["model"], settings["personality"])
    
    db.add_message(user_id, "assistant", response)
    
    await thinking_msg.delete()
    
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "clear":
        db.clear_history(user_id)
        await query.edit_message_text("History cleared! Use /start to begin again.")
    
    elif data == "help":
        await query.edit_message_text("Use /help to see all commands!")
    
    elif data == "image":
        await query.edit_message_text("Use the command:\n/image <your description>\n\nExample: /image a futuristic city at sunset")
    
    elif data == "model":
        await model_command(update, context)
    
    elif data == "personality":
        await personality_command(update, context)
    
    elif data.startswith("set_model:"):
        model = data.split(":")[1]
        db.update_user_settings(user_id, model=model)
        await query.edit_message_text(f"Model changed to: {Config.ALLOWED_MODELS.get(model, model)}")
    
    elif data.startswith("set_personality:"):
        personality = data.split(":")[1]
        db.update_user_settings(user_id, personality=personality)
        await query.edit_message_text(f"Personality changed to: {personality.capitalize()}")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not context.bot.username:
        return
    
    bot_username = context.bot.username
    text = update.message.text or ""
    
    if f"@{bot_username}" not in text:
        return
    
    group_id = update.effective_chat.id
    if not db.is_group_allowed(group_id):
        return
    
    clean_text = text.replace(f"@{bot_username}", "").strip()
    
    user_id = update.effective_user.id
    db.add_user(update.effective_user.id, update.effective_user.username,
                update.effective_user.first_name, update.effective_user.last_name)
    
    settings = db.get_user_settings(user_id)
    
    thinking_msg = await update.message.reply_text("Thinking...")
    
    db.add_message(user_id, "user", clean_text)
    history = db.get_conversation_history(user_id)
    response = await AIEngine.get_response(history, settings["model"], settings["personality"])
    db.add_message(user_id, "assistant", response)
    
    await thinking_msg.delete()
    await update.message.reply_text(response)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != Config.ADMIN_USER_ID:
        await update.message.reply_text("Admin only command.")
        return
    
    stats = db.get_stats()
    stats_text = f"""Bot Statistics:

Total Users: {stats['total_users']}
Total Messages: {stats['total_messages']}
Total Groups: {stats['total_groups']}
"""
    await update.message.reply_text(stats_text)