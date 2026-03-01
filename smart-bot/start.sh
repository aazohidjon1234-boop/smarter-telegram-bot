#!/bin/bash

# Smart Bot Startup Script

echo "🤖 Starting Smart Bot v2.0..."
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found! Creating from example..."
    cp .env.example .env
    echo "❌ Please edit .env file and add your API keys before running again!"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
python3 -c "import telegram, aiohttp" 2>/dev/null || {
    echo "📦 Installing missing dependencies..."
    pip install -r requirements.txt
}

# Run the bot
echo "🚀 Starting bot..."
echo "================================"
python3 main.py

# Deactivate virtual environment on exit
deactivate