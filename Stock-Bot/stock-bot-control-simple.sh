#!/bin/bash

# Stock Bot Control Script - Simple Version
# This script allows you to easily start, stop, and check the status of all your Stock Bot applications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="stock-bot"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}[STOCK BOT]${NC} $1"
}

print_app() {
    echo -e "${CYAN}[$1]${NC} $2"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Function to get app deployment and service names
get_app_names() {
    case $1 in
        jupyter)
            echo "jupyter-custom-deps:jupyter-custom-deps-service"
            ;;
        streamlit)
            echo "stock-bot-streamlit:stock-bot-streamlit"
            ;;
        flask)
            echo "stock-bot-flask:stock-bot-flask"
            ;;
        *)
            print_error "Unknown application: $1"
            return 1
            ;;
    esac
}

# Function to start an application
start_app() {
    local app_name=$1
    local app_info=$(get_app_names $app_name)
    IFS=':' read -r deployment service <<< "$app_info"
    
    print_app $app_name "Starting $app_name..."
    
    # Check if deployment exists
    if ! kubectl get deployment $deployment -n $NAMESPACE &> /dev/null; then
        print_error "Deployment $deployment not found in namespace $NAMESPACE"
        return 1
    fi
    
    # Scale up the deployment
    kubectl scale deployment $deployment --replicas=1 -n $NAMESPACE
    
    print_app $app_name "Waiting for $app_name to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/$deployment -n $NAMESPACE
    
    # Get the service URL
    EXTERNAL_IP=$(kubectl get svc $service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -z "$EXTERNAL_IP" ]; then
        print_warning "External IP not yet assigned for $app_name. Waiting..."
        sleep 10
        EXTERNAL_IP=$(kubectl get svc $service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        print_success "$app_name is now running!"
        print_app $app_name "Access URL: https://$EXTERNAL_IP"
        if [ "$app_name" = "jupyter" ]; then
            print_app $app_name "Token: stock-bot-jupyter-2024"
        fi
    else
        print_error "Failed to get external IP for $app_name. Check the service status."
        kubectl get svc $service -n $NAMESPACE
    fi
}

# Function to stop an application
stop_app() {
    local app_name=$1
    local app_info=$(get_app_names $app_name)
    IFS=':' read -r deployment service <<< "$app_info"
    
    print_app $app_name "Stopping $app_name..."
    
    # Check if deployment exists
    if ! kubectl get deployment $deployment -n $NAMESPACE &> /dev/null; then
        print_error "Deployment $deployment not found in namespace $NAMESPACE"
        return 1
    fi
    
    # Scale down the deployment
    kubectl scale deployment $deployment --replicas=0 -n $NAMESPACE
    
    print_success "$app_name has been stopped"
}

# Function to restart an application
restart_app() {
    local app_name=$1
    print_app $app_name "Restarting $app_name..."
    stop_app $app_name
    sleep 5
    start_app $app_name
}

# Function to check status of an application
check_app_status() {
    local app_name=$1
    local app_info=$(get_app_names $app_name)
    IFS=':' read -r deployment service <<< "$app_info"
    
    print_app $app_name "Checking status..."
    
    # Check if deployment exists
    if ! kubectl get deployment $deployment -n $NAMESPACE &> /dev/null; then
        print_error "Deployment $deployment not found in namespace $NAMESPACE"
        return 1
    fi
    
    # Get deployment status
    REPLICAS=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY_REPLICAS=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    if [ "$REPLICAS" = "0" ]; then
        print_warning "$app_name is stopped (0 replicas)"
    elif [ "$READY_REPLICAS" = "1" ]; then
        print_success "$app_name is running (1/1 replicas ready)"
        
        # Get the service URL
        EXTERNAL_IP=$(kubectl get svc $service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        if [ -n "$EXTERNAL_IP" ]; then
            print_app $app_name "URL: https://$EXTERNAL_IP"
            if [ "$app_name" = "jupyter" ]; then
                print_app $app_name "Token: stock-bot-jupyter-2024"
            fi
        fi
    else
        print_warning "$app_name is starting up ($READY_REPLICAS/$REPLICAS replicas ready)"
    fi
}

# Function to get URL of an application
get_app_url() {
    local app_name=$1
    local app_info=$(get_app_names $app_name)
    IFS=':' read -r deployment service <<< "$app_info"
    
    EXTERNAL_IP=$(kubectl get svc $service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo "https://$EXTERNAL_IP"
    else
        print_error "External IP not available for $app_name. It might not be running."
        return 1
    fi
}

# Function to start all applications
start_all() {
    print_header "Starting all Stock Bot applications..."
    start_app "jupyter"
    echo
    start_app "streamlit"
    echo
    start_app "flask"
    echo
    print_success "All applications started!"
}

# Function to stop all applications
stop_all() {
    print_header "Stopping all Stock Bot applications..."
    stop_app "jupyter"
    echo
    stop_app "streamlit"
    echo
    stop_app "flask"
    echo
    print_success "All applications stopped!"
}

# Function to check status of all applications
check_all_status() {
    print_header "Checking status of all Stock Bot applications..."
    echo
    check_app_status "jupyter"
    echo
    check_app_status "streamlit"
    echo
    check_app_status "flask"
    echo
}

# Function to show all URLs
show_all_urls() {
    print_header "Stock Bot Application URLs:"
    echo
    print_app "JUPYTER" "Getting URL..."
    local jupyter_url=$(get_app_url "jupyter" 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_app "JUPYTER" "URL: $jupyter_url"
        print_app "JUPYTER" "Token: stock-bot-jupyter-2024"
    else
        print_app "JUPYTER" "Not running"
    fi
    echo
    
    print_app "STREAMLIT" "Getting URL..."
    local streamlit_url=$(get_app_url "streamlit" 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_app "STREAMLIT" "URL: $streamlit_url"
    else
        print_app "STREAMLIT" "Not running"
    fi
    echo
    
    print_app "FLASK" "Getting URL..."
    local flask_url=$(get_app_url "flask" 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_app "FLASK" "URL: $flask_url"
    else
        print_app "FLASK" "Not running"
    fi
    echo
}

# Function to show help
show_help() {
    echo "Stock Bot Control Script"
    echo
    echo "Usage: $0 [COMMAND] [APPLICATION]"
    echo
    echo "Commands:"
    echo "  start [app]     Start an application or all applications"
    echo "  stop [app]      Stop an application or all applications"
    echo "  restart [app]   Restart an application"
    echo "  status [app]    Check the status of an application or all applications"
    echo "  url [app]       Get the URL of an application"
    echo "  urls            Show all application URLs"
    echo "  help            Show this help message"
    echo
    echo "Applications:"
    echo "  jupyter         Jupyter Lab environment"
    echo "  streamlit       Streamlit web application"
    echo "  flask           Flask API backend"
    echo "  all             All applications (for start/stop/status commands)"
    echo
    echo "Examples:"
    echo "  $0 start jupyter        # Start Jupyter"
    echo "  $0 stop streamlit       # Stop Streamlit"
    echo "  $0 restart flask        # Restart Flask"
    echo "  $0 status all           # Check status of all apps"
    echo "  $0 url jupyter          # Get Jupyter URL"
    echo "  $0 urls                 # Show all URLs"
    echo "  $0 start all            # Start all applications"
    echo "  $0 stop all             # Stop all applications"
}

# Main script logic
check_kubectl

case "${1:-help}" in
    start)
        case "${2:-all}" in
            all)
                start_all
                ;;
            jupyter|streamlit|flask)
                start_app $2
                ;;
            *)
                print_error "Unknown application: $2"
                echo "Available applications: jupyter, streamlit, flask, all"
                exit 1
                ;;
        esac
        ;;
    stop)
        case "${2:-all}" in
            all)
                stop_all
                ;;
            jupyter|streamlit|flask)
                stop_app $2
                ;;
            *)
                print_error "Unknown application: $2"
                echo "Available applications: jupyter, streamlit, flask, all"
                exit 1
                ;;
        esac
        ;;
    restart)
        if [ -z "$2" ]; then
            print_error "Please specify an application to restart"
            echo "Available applications: jupyter, streamlit, flask"
            exit 1
        fi
        case "$2" in
            jupyter|streamlit|flask)
                restart_app $2
                ;;
            *)
                print_error "Unknown application: $2"
                echo "Available applications: jupyter, streamlit, flask"
                exit 1
                ;;
        esac
        ;;
    status)
        case "${2:-all}" in
            all)
                check_all_status
                ;;
            jupyter|streamlit|flask)
                check_app_status $2
                ;;
            *)
                print_error "Unknown application: $2"
                echo "Available applications: jupyter, streamlit, flask, all"
                exit 1
                ;;
        esac
        ;;
    url)
        if [ -z "$2" ]; then
            print_error "Please specify an application"
            echo "Available applications: jupyter, streamlit, flask"
            exit 1
        fi
        case "$2" in
            jupyter|streamlit|flask)
                get_app_url $2
                ;;
            *)
                print_error "Unknown application: $2"
                echo "Available applications: jupyter, streamlit, flask"
                exit 1
                ;;
        esac
        ;;
    urls)
        show_all_urls
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
