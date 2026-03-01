# AI Telegram Bot

A powerful AI Telegram bot with GPT-4 and DALL-E 3 integration.

## Features

- Multiple AI Models: GPT-4o, GPT-4o Mini, GPT-4 Turbo
- Image Generation: DALL-E 3 integration
- Conversation Memory: Remembers context for natural conversations
- Customizable Personalities: 6 different personality modes
- Group Chat Support: Works in groups with @mention
- Persistent Storage: SQLite database for user data and history

## Setup

1. Clone and enter the directory
2. Create environment file: `cp .env.example .env`
3. Edit `.env` with your API keys:
   - Get Bot Token from @BotFather
   - Get OpenAI API key from OpenAI Platform
4. Run: `./start.sh`

## Commands

- `/start` - Start the bot
- `/help` - Show all commands
- `/clear` - Clear conversation history
- `/model` - Change AI model
- `/personality` - Change bot personality
- `/image <prompt>` - Generate image
- `/stats` - Show bot statistics (admin only)

## Personalities

- Default: Helpful assistant
- Creative: Imaginative and inspiring
- Professional: Formal business consultant
- Friendly: Cheerful, casual friend
- Teacher: Patient educator
- Coder: Expert programmer

## Image Generation

/image a cyberpunk cat in tokyo