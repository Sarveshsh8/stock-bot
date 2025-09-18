#!/bin/bash

# Stock Bot V3 - Local Development Startup Script

echo "🚀 Starting Stock Bot V3 Local Development Environment"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: web_app.py not found. Please run this script from the stock-bot-deployment directory."
    exit 1
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
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env_example.txt .env
    echo "📝 Please edit .env file with your AWS credentials before running the app."
    echo "   You can edit it with: nano .env"
    echo ""
    echo "Press Enter to continue after editing .env file..."
    read
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found. Please ensure the configuration file exists."
    exit 1
fi

echo "✅ Environment setup complete!"
echo ""
echo "🌐 Starting Streamlit web application..."
echo "   The app will be available at: http://localhost:8501"
echo "   Press Ctrl+C to stop the application"
echo ""

# Start Streamlit app
streamlit run web_app.py --server.port 8501 --server.address localhost
