#!/bin/bash
# Stock-Bot Start Script
# Starts all services: Streamlit, Flask API, and background processes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STREAMLIT_PORT=8501
FLASK_PORT=5001
STREAMLIT_LOG="streamlit.log"
FLASK_LOG="flask.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}        STOCK-BOT START SCRIPT${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with your AWS credentials${NC}"
    echo -e "${YELLOW}Continuing anyway...${NC}"
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}SUCCESS: Port $port is available${NC}"
        return 0
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local process_name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}PROCESSING: Killing existing process on port $port...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check and clear ports
echo -e "${BLUE}Checking ports...${NC}"
kill_port $STREAMLIT_PORT "Streamlit"
kill_port $FLASK_PORT "Flask API"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}ERROR: Failed to activate virtual environment${NC}"
    exit 1
fi
echo -e "${GREEN}SUCCESS: Virtual environment activated: $VIRTUAL_ENV${NC}"

# Install dependencies if needed
echo -e "${BLUE}Checking dependencies...${NC}"
if ! python3 -c "import streamlit, flask, boto3, pandas, faiss" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}SUCCESS: Dependencies installed${NC}"
else
    echo -e "${GREEN}SUCCESS: Dependencies already installed${NC}"
fi

# Start Streamlit app
echo -e "${BLUE}Starting Streamlit app on port $STREAMLIT_PORT...${NC}"
nohup streamlit run streamlit_app.py --server.port $STREAMLIT_PORT --server.headless true > logs/$STREAMLIT_LOG 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > logs/streamlit.pid

# Wait for Streamlit to start
sleep 5
if kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo -e "${GREEN}SUCCESS: Streamlit started successfully (PID: $STREAMLIT_PID)${NC}"
else
    echo -e "${RED}ERROR: Failed to start Streamlit${NC}"
    exit 1
fi

# Start Flask API
echo -e "${BLUE}Starting Flask API on port $FLASK_PORT...${NC}"
nohup python3 app.py > logs/$FLASK_LOG 2>&1 &
FLASK_PID=$!
echo $FLASK_PID > logs/flask.pid

# Wait for Flask to start
sleep 5
if kill -0 $FLASK_PID 2>/dev/null; then
    echo -e "${GREEN}SUCCESS: Flask API started successfully (PID: $FLASK_PID)${NC}"
else
    echo -e "${RED}ERROR: Failed to start Flask API${NC}"
    exit 1
fi

# Final status
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}SUCCESS: ALL SERVICES STARTED SUCCESSFULLY!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Streamlit App:${NC} http://localhost:$STREAMLIT_PORT"
echo -e "${GREEN}Flask API:${NC} http://localhost:$FLASK_PORT"
echo -e "${GREEN}Logs:${NC} logs/$STREAMLIT_LOG, logs/$FLASK_LOG"
echo -e "${GREEN}PIDs:${NC} Streamlit: $STREAMLIT_PID, Flask: $FLASK_PID"
echo -e ""
echo -e "${YELLOW}To stop all services, run: ./stop.sh${NC}"
echo -e "${YELLOW}To view logs: tail -f logs/$STREAMLIT_LOG or tail -f logs/$FLASK_LOG${NC}"
echo -e "${BLUE}========================================${NC}"

# Save PIDs to a file for easy access
echo "STREAMLIT_PID=$STREAMLIT_PID" > logs/app.pids
echo "FLASK_PID=$FLASK_PID" >> logs/app.pids
echo "STREAMLIT_PORT=$STREAMLIT_PORT" >> logs/app.pids
echo "FLASK_PORT=$FLASK_PORT" >> logs/app.pids
