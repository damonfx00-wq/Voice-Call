#!/bin/bash

# MCP Server Startup Script

echo "🚀 Starting MCP Server..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your NVIDIA_API_KEY"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/documents data/vector_db

# Start the server
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
