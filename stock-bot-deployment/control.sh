#!/bin/bash

# Stock Bot V3 - Control Script
# Usage: ./control.sh [start|stop|restart|status|logs|urls|clean]

set -e

NAMESPACE="stock-bot-v3"
APP_LABEL="app=stock-bot-v3"
JUPYTER_LABEL="app=stock-bot-v3-jupyter"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} Stock Bot V3 - Control Script${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Function to check if namespace exists
check_namespace() {
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        print_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting Stock Bot V3 services..."
    
    # Start main application
    print_status "Starting main application (Streamlit + Flask)..."
    kubectl scale deployment stock-bot-v3 --replicas=2 -n $NAMESPACE
    
    # Start Jupyter notebook
    print_status "Starting Jupyter notebook..."
    kubectl scale deployment stock-bot-v3-jupyter --replicas=1 -n $NAMESPACE
    
    print_status "Waiting for services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3 -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3-jupyter -n $NAMESPACE
    
    print_status "All services started successfully!"
    show_urls
}

# Function to stop services
stop_services() {
    print_status "Stopping Stock Bot V3 services..."
    
    # Stop main application
    print_status "Stopping main application..."
    kubectl scale deployment stock-bot-v3 --replicas=0 -n $NAMESPACE
    
    # Stop Jupyter notebook
    print_status "Stopping Jupyter notebook..."
    kubectl scale deployment stock-bot-v3-jupyter --replicas=0 -n $NAMESPACE
    
    print_status "All services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting Stock Bot V3 services..."
    stop_services
    sleep 5
    start_services
}

# Function to show service status
show_status() {
    print_status "Stock Bot V3 Service Status:"
    echo ""
    
    echo -e "${BLUE}Main Application (Streamlit + Flask):${NC}"
    kubectl get pods -n $NAMESPACE -l $APP_LABEL
    echo ""
    
    echo -e "${BLUE}Jupyter Notebook:${NC}"
    kubectl get pods -n $NAMESPACE -l $JUPYTER_LABEL
    echo ""
    
    echo -e "${BLUE}Services:${NC}"
    kubectl get services -n $NAMESPACE
    echo ""
    
    echo -e "${BLUE}Deployments:${NC}"
    kubectl get deployments -n $NAMESPACE
}

# Function to show service URLs
show_urls() {
    print_status "Service URLs:"
    echo ""
    
    # Get LoadBalancer URLs
    MAIN_SERVICE=$(kubectl get service stock-bot-v3-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not available")
    JUPYTER_SERVICE=$(kubectl get service stock-bot-v3-jupyter-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not available")
    
    if [ "$MAIN_SERVICE" != "Not available" ]; then
        echo -e "${GREEN}Streamlit Web App:${NC} http://$MAIN_SERVICE"
        echo -e "${GREEN}Flask API:${NC} http://$MAIN_SERVICE:5000"
    else
        echo -e "${RED}Main Application:${NC} Not available"
    fi
    
    if [ "$JUPYTER_SERVICE" != "Not available" ]; then
        echo -e "${GREEN}Jupyter Notebook:${NC} http://$JUPYTER_SERVICE"
    else
        echo -e "${RED}Jupyter Notebook:${NC} Not available"
    fi
}

# Function to show logs
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_error "Please specify which service logs to show: main or jupyter"
        echo "Usage: $0 logs [main|jupyter]"
        exit 1
    fi
    
    case $service in
        "main")
            print_status "Showing main application logs..."
            kubectl logs -n $NAMESPACE -l $APP_LABEL --tail=50 -f
            ;;
        "jupyter")
            print_status "Showing Jupyter notebook logs..."
            kubectl logs -n $NAMESPACE -l $JUPYTER_LABEL --tail=50 -f
            ;;
        *)
            print_error "Invalid service. Use 'main' or 'jupyter'"
            exit 1
            ;;
    esac
}

# Function to clean up resources
clean_services() {
    print_warning "This will delete all Stock Bot V3 resources. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Stock Bot V3 resources..."
        
        # Delete deployments
        kubectl delete deployment stock-bot-v3 -n $NAMESPACE --ignore-not-found=true
        kubectl delete deployment stock-bot-v3-jupyter -n $NAMESPACE --ignore-not-found=true
        
        # Delete services
        kubectl delete service stock-bot-v3-service -n $NAMESPACE --ignore-not-found=true
        kubectl delete service stock-bot-v3-jupyter-service -n $NAMESPACE --ignore-not-found=true
        
        # Delete PVCs
        kubectl delete pvc stock-bot-v3-pvc -n $NAMESPACE --ignore-not-found=true
        kubectl delete pvc stock-bot-v3-jupyter-pvc -n $NAMESPACE --ignore-not-found=true
        
        # Delete secrets
        kubectl delete secret aws-secrets -n $NAMESPACE --ignore-not-found=true
        
        # Delete configmap
        kubectl delete configmap stock-bot-v3-config -n $NAMESPACE --ignore-not-found=true
        
        # Delete service account
        kubectl delete serviceaccount stock-bot-v3-sa -n $NAMESPACE --ignore-not-found=true
        
        print_status "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show help
show_help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services (main app + Jupyter)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show service status"
    echo "  urls      - Show service URLs"
    echo "  logs      - Show logs (usage: $0 logs [main|jupyter])"
    echo "  clean     - Clean up all resources"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 logs main"
    echo "  $0 logs jupyter"
}

# Main script logic
main() {
    print_header
    
    # Load AWS credentials from .env file if it exists
    if [ -f ".env" ]; then
        print_status "Loading AWS credentials from .env file..."
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
    fi
    
    # Check prerequisites
    check_kubectl
    check_namespace
    
    case ${1:-help} in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "urls")
            show_urls
            ;;
        "logs")
            show_logs $2
            ;;
        "clean")
            clean_services
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"