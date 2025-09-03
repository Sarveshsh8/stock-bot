#!/bin/bash

# Stock-Bot Docker Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="stock-bot"
IMAGE_TAG="latest"
CONTAINER_NAME="stock-bot-test"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STOCK-BOT DOCKER BUILD SCRIPT${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Docker is not running!${NC}"
        echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to clean up previous builds
cleanup() {
    echo -e "${YELLOW}Cleaning up previous builds...${NC}"
    
    # Stop and remove test container
    if docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        echo -e "${YELLOW}Stopping test container...${NC}"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # Remove old image
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$IMAGE_NAME:$IMAGE_TAG"; then
        echo -e "${YELLOW}Removing old image...${NC}"
        docker rmi "$IMAGE_NAME:$IMAGE_TAG" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "${BLUE}Building Docker image...${NC}"
    echo -e "${YELLOW}Image: $IMAGE_NAME:$IMAGE_TAG${NC}"
    
    # Build the image
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    else
        echo -e "${RED}❌ Docker build failed!${NC}"
        exit 1
    fi
}

# Function to test Docker image
test_image() {
    echo -e "${BLUE}Testing Docker image...${NC}"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating a sample one...${NC}"
        cat > .env << EOF
# Sample environment variables
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name_here
EOF
        echo -e "${YELLOW}⚠️  Please update .env file with your actual AWS credentials${NC}"
    fi
    
    # Create necessary directories
    mkdir -p data indices logs
    
    # Run the container
    echo -e "${YELLOW}Starting test container...${NC}"
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p 8501:8501 \
        -p 5001:5001 \
        --env-file .env \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/indices:/app/indices" \
        -v "$(pwd)/logs:/app/logs" \
        "$IMAGE_NAME:$IMAGE_TAG"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Test container started successfully!${NC}"
        echo -e "${BLUE}Container name: $CONTAINER_NAME${NC}"
        echo -e "${BLUE}Container ID: $(docker ps -q --filter name=$CONTAINER_NAME)${NC}"
    else
        echo -e "${RED}❌ Failed to start test container!${NC}"
        exit 1
    fi
    
    # Wait for services to start
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Check container status
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$CONTAINER_NAME.*Up"; then
        echo -e "${GREEN}✅ Container is running${NC}"
    else
        echo -e "${RED}❌ Container is not running properly${NC}"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    
    # Check service health
    echo -e "${YELLOW}Checking service health...${NC}"
    
    # Check Streamlit
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Streamlit is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Streamlit health check failed (may still be starting)${NC}"
    fi
    
    # Check Flask
    if curl -s http://localhost:5001/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Flask API is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Flask API check failed (may still be starting)${NC}"
    fi
}

# Function to show container info
show_info() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}CONTAINER INFORMATION${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Container Name:${NC} $CONTAINER_NAME"
    echo -e "${GREEN}Image:${NC} $IMAGE_NAME:$IMAGE_TAG"
    echo -e "${GREEN}Streamlit URL:${NC} http://localhost:8501"
    echo -e "${GREEN}Flask API URL:${NC} http://localhost:5001"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}To view logs:${NC} docker logs -f $CONTAINER_NAME"
    echo -e "${YELLOW}To stop container:${NC} docker stop $CONTAINER_NAME"
    echo -e "${YELLOW}To remove container:${NC} docker rm $CONTAINER_NAME"
    echo -e "${BLUE}========================================${NC}"
}

# Function to stop test container
stop_container() {
    echo -e "${YELLOW}Stopping test container...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✅ Test container stopped and removed${NC}"
}

# Main execution
main() {
    check_docker
    cleanup
    build_image
    test_image
    show_info
    
    echo -e "${GREEN}🎉 Docker build and test completed successfully!${NC}"
    echo -e "${BLUE}Your Stock-Bot application is now running in Docker!${NC}"
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        stop_container
        ;;
    "clean")
        cleanup
        ;;
    "logs")
        if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
            docker logs -f "$CONTAINER_NAME"
        else
            echo -e "${RED}Container $CONTAINER_NAME is not running${NC}"
        fi
        ;;
    "help"|"-h"|"--help")
        echo -e "${BLUE}Usage:${NC}"
        echo -e "  $0          - Build and test Docker image"
        echo -e "  $0 stop     - Stop and remove test container"
        echo -e "  $0 clean    - Clean up previous builds"
        echo -e "  $0 logs     - View container logs"
        echo -e "  $0 help     - Show this help message"
        ;;
    "")
        main
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo -e "${YELLOW}Use '$0 help' for usage information${NC}"
        exit 1
        ;;
esac
