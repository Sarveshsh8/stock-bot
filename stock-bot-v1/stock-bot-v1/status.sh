#!/bin/bash
# Stock-Bot Status Script
# Shows current status of all services

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
echo -e "${BLUE}        STOCK-BOT STATUS${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local pid_file=$3
    
    echo -e "${BLUE}$service_name Status:${NC}"
    
    # Check if PID file exists
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  ${GREEN}SUCCESS: Running (PID: $pid)${NC}"
        else
            echo -e "  ${RED}ERROR: PID file exists but process not running${NC}"
            echo -e "  ${YELLOW}   Cleaning up stale PID file...${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "  ${YELLOW}WARNING: No PID file found${NC}"
    fi
    
    # Check port status
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local port_pid=$(lsof -ti:$port)
        echo -e "  ${GREEN} Port $port active (PID: $port_pid)${NC}"
    else
        echo -e "  ${RED} Port $port not listening${NC}"
    fi
    
    echo ""
}

# Function to check virtual environment
check_venv() {
    echo -e "${BLUE}Virtual Environment Status:${NC}"
    if [ -d "Stock-Bot/venv" ]; then
        echo -e "  ${GREEN} Virtual environment exists${NC}"
        if [ -f "Stock-Bot/venv/bin/activate" ]; then
            echo -e "  ${GREEN}Activation script exists${NC}"
        else
            echo -e "  ${RED}Activation script missing${NC}"
        fi
    else
        echo -e "  ${RED} Virtual environment not found${NC}"
    fi
    echo ""
}

# Function to check environment file
check_env() {
    echo -e "${BLUE}Environment Configuration:${NC}"
    if [ -f ".env" ]; then
        echo -e "  ${GREEN} .env file exists${NC}"
        # Check for required variables (without exposing values)
        if grep -q "AWS_ACCESS_KEY_ID" .env; then
            echo -e "  ${GREEN} AWS_ACCESS_KEY_ID configured${NC}"
        else
            echo -e "  ${RED} AWS_ACCESS_KEY_ID missing${NC}"
        fi
        
        if grep -q "S3_BUCKET_NAME" .env; then
            echo -e "  ${GREEN} S3_BUCKET_NAME configured${NC}"
        else
            echo -e "  ${RED}ERROR: S3_BUCKET_NAME missing${NC}"
        fi
    else
        echo -e "  ${RED}ERROR: .env file not found${NC}"
    fi
    echo ""
}

# Function to check logs
check_logs() {
    echo -e "${BLUE}Log Files Status:${NC}"
    if [ -f "streamlit.log" ]; then
        local size=$(du -h streamlit.log | cut -f1)
        echo -e "  ${GREEN}SUCCESS: streamlit.log exists (Size: $size)${NC}"
    else
        echo -e "  ${YELLOW}WARNING: streamlit.log not found${NC}"
    fi
    
    if [ -f "flask.log" ]; then
        local size=$(du -h flask.log | cut -f1)
        echo -e "  ${GREEN}SUCCESS: flask.log exists (Size: $size)${NC}"
    else
        echo -e "  ${YELLOW}WARNING: flask.log not found${NC}"
    fi
    echo ""
}

# Function to check FAISS index
check_faiss() {
    echo -e "${BLUE}FAISS Index Status:${NC}"
    if [ -f "financial_data.index" ]; then
        local size=$(du -h financial_data.index | cut -f1)
        echo -e "  ${GREEN}SUCCESS: FAISS index exists (Size: $size)${NC}"
    else
        echo -e "  ${YELLOW}WARNING: FAISS index not found${NC}"
    fi
    
    if [ -f "financial_documents.pkl" ]; then
        local size=$(du -h financial_documents.pkl | cut -f1)
        echo -e "  ${GREEN}SUCCESS: Documents pickle exists (Size: $size)${NC}"
    else
        echo -e "  ${YELLOW}WARNING: Documents pickle not found${NC}"
    fi
    echo ""
}

# Function to show system info
show_system_info() {
    echo -e "${BLUE}System Information:${NC}"
    echo -e "  OS: $(uname -s) $(uname -r)"
    echo -e "  Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo -e "  Current Directory: $(pwd)"
    echo -e "  Available Memory: $(free -h 2>/dev/null | grep Mem | awk '{print $7}' || echo 'Unknown')"
    echo ""
}

# Function to show quick actions
show_quick_actions() {
    echo -e "${BLUE}Quick Actions:${NC}"
    echo -e "  ${GREEN}Start all services:${NC} ./start.sh"
    echo -e "  ${RED}Stop all services:${NC} ./stop.sh"
    echo -e "  ${BLUE}View Streamlit logs:${NC} tail -f streamlit.log"
    echo -e "  ${BLUE}View Flask logs:${NC} tail -f flask.log"
    echo -e "  ${YELLOW}Activate venv:${NC} source venv/bin/activate"
    echo ""
}

# Run all checks
check_venv
check_env
check_service "Streamlit App" $STREAMLIT_PORT "streamlit.pid"
check_service "Flask API" $FLASK_PORT "flask.pid"
check_logs
check_faiss
show_system_info
show_quick_actions

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Status check completed!${NC}"
echo -e "${BLUE}========================================${NC}"
