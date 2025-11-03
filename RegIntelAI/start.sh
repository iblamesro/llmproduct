#!/bin/bash

# RegIntel AI - Quick Start Script

echo "🏦 RegIntel AI - Setup & Launch"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key before running the app"
    echo "   Open .env and replace 'your_openai_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter when you've added your API key..."
fi

# Launch Streamlit app
echo "🚀 Launching RegIntel AI..."
streamlit run app.py
