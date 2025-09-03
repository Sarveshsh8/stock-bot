#!/bin/bash
# Stock-Bot Stop Script
# Stops all services and cleans up ports

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}        STOCK-BOT STOP SCRIPT${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to kill process by PID file
kill_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}PROCESSING: Stopping $service_name (PID: $pid)...${NC}"
            kill "$pid" 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}PROCESSING: Force killing $service_name...${NC}"
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            # Remove PID file
            rm -f "$pid_file"
            echo -e "${GREEN}SUCCESS: $service_name stopped${NC}"
        else
            echo -e "${YELLOW}WARNING: $service_name not running (PID: $pid)${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}WARNING: PID file not found for $service_name${NC}"
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}PROCESSING: Killing $service_name on port $port...${NC}"
        local pids=$(lsof -ti:$port)
        for pid in $pids; do
            echo -e "${YELLOW}   Killing PID: $pid${NC}"
            kill -9 "$pid" 2>/dev/null || true
        done
        sleep 2
        
        # Verify port is free
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}ERROR: Failed to free port $port${NC}"
        else
            echo -e "${GREEN}SUCCESS: Port $port is now free${NC}"
        fi
    else
        echo -e "${GREEN}SUCCESS: Port $port is already free${NC}"
    fi
}

# Function to kill by process name
kill_by_name() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}PROCESSING: Killing $process_name processes...${NC}"
        for pid in $pids; do
            echo -e "${YELLOW}   Killing PID: $pid${NC}"
            kill -9 "$pid" 2>/dev/null || true
        done
        sleep 2
        echo -e "${GREEN}SUCCESS: $process_name processes killed${NC}"
    else
        echo -e "${GREEN}SUCCESS: No $process_name processes found${NC}"
    fi
}

# Stop services by PID files first
echo -e "${BLUE}Stopping services by PID files...${NC}"
kill_by_pid_file "streamlit.pid" "Streamlit"
kill_by_pid_file "flask.pid" "Flask API"

# Kill by process names as backup
echo -e "${BLUE}Killing processes by name...${NC}"
kill_by_name "streamlit"
kill_by_name "python3 app.py"
kill_by_name "flask"

# Kill by ports as final cleanup
echo -e "${BLUE}Cleaning up ports...${NC}"
kill_port $STREAMLIT_PORT "Streamlit"
kill_port $FLASK_PORT "Flask API"

# Remove PID files
echo -e "${BLUE}Cleaning up PID files...${NC}"
rm -f streamlit.pid flask.pid app.pids

# Final status
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}SUCCESS: ALL SERVICES STOPPED SUCCESSFULLY!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}SUCCESS: Streamlit stopped${NC}"
echo -e "${GREEN}SUCCESS: Flask API stopped${NC}"
echo -e "${GREEN}SUCCESS: Ports cleaned up${NC}"
echo -e "${GREEN}SUCCESS: PID files removed${NC}"
echo -e ""
echo -e "${YELLOW}To start all services, run: ./start.sh${NC}"
echo -e "${BLUE}========================================${NC}"
