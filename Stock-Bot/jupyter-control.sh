#!/bin/bash

# Jupyter Control Script for Stock Bot
# This script allows you to easily start, stop, and check the status of your Jupyter environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="stock-bot"
DEPLOYMENT_NAME="jupyter-custom-deps"
SERVICE_NAME="jupyter-custom-deps-service"

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

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Function to check if deployment exists
check_deployment() {
    if ! kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE &> /dev/null; then
        print_error "Deployment $DEPLOYMENT_NAME not found in namespace $NAMESPACE"
        print_status "Please run the deployment first using: kubectl apply -f k8s/jupyter-custom-deps.yaml"
        exit 1
    fi
}

# Function to start Jupyter
start_jupyter() {
    print_status "Starting Jupyter environment..."
    
    check_kubectl
    check_deployment
    
    # Scale up the deployment
    kubectl scale deployment $DEPLOYMENT_NAME --replicas=1 -n $NAMESPACE
    
    print_status "Waiting for Jupyter to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    # Get the service URL
    EXTERNAL_IP=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -z "$EXTERNAL_IP" ]; then
        print_warning "External IP not yet assigned. Waiting..."
        sleep 10
        EXTERNAL_IP=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        print_success "Jupyter is now running!"
        print_status "Access your Jupyter Lab at: https://$EXTERNAL_IP"
        print_status "Token: stock-bot-jupyter-2024"
    else
        print_error "Failed to get external IP. Check the service status."
        kubectl get svc $SERVICE_NAME -n $NAMESPACE
    fi
}

# Function to stop Jupyter
stop_jupyter() {
    print_status "Stopping Jupyter environment..."
    
    check_kubectl
    check_deployment
    
    # Scale down the deployment
    kubectl scale deployment $DEPLOYMENT_NAME --replicas=0 -n $NAMESPACE
    
    print_success "Jupyter has been stopped"
}

# Function to restart Jupyter
restart_jupyter() {
    print_status "Restarting Jupyter environment..."
    stop_jupyter
    sleep 5
    start_jupyter
}

# Function to check status
check_status() {
    print_status "Checking Jupyter status..."
    
    check_kubectl
    check_deployment
    
    # Get deployment status
    REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY_REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    if [ "$REPLICAS" = "0" ]; then
        print_warning "Jupyter is stopped (0 replicas)"
    elif [ "$READY_REPLICAS" = "1" ]; then
        print_success "Jupyter is running (1/1 replicas ready)"
        
        # Get the service URL
        EXTERNAL_IP=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        if [ -n "$EXTERNAL_IP" ]; then
            print_status "Access URL: https://$EXTERNAL_IP"
            print_status "Token: stock-bot-jupyter-2024"
        fi
    else
        print_warning "Jupyter is starting up ($READY_REPLICAS/$REPLICAS replicas ready)"
    fi
    
    # Show pod status
    echo
    print_status "Pod status:"
    kubectl get pods -n $NAMESPACE -l app=jupyter-custom-deps
}

# Function to get logs
get_logs() {
    print_status "Getting Jupyter logs..."
    
    check_kubectl
    check_deployment
    
    # Get the pod name
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=jupyter-custom-deps -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$POD_NAME" ]; then
        kubectl logs $POD_NAME -n $NAMESPACE -c jupyter --tail=50
    else
        print_error "No Jupyter pods found"
    fi
}

# Function to show help
show_help() {
    echo "Jupyter Control Script for Stock Bot"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start the Jupyter environment"
    echo "  stop      Stop the Jupyter environment"
    echo "  restart   Restart the Jupyter environment"
    echo "  status    Check the status of Jupyter"
    echo "  logs      Show Jupyter logs"
    echo "  url       Get the Jupyter URL"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start    # Start Jupyter"
    echo "  $0 stop     # Stop Jupyter"
    echo "  $0 status   # Check if Jupyter is running"
    echo "  $0 url      # Get the Jupyter URL"
}

# Function to get URL
get_url() {
    check_kubectl
    check_deployment
    
    EXTERNAL_IP=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo "https://$EXTERNAL_IP"
    else
        print_error "External IP not available. Jupyter might not be running."
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_jupyter
        ;;
    stop)
        stop_jupyter
        ;;
    restart)
        restart_jupyter
        ;;
    status)
        check_status
        ;;
    logs)
        get_logs
        ;;
    url)
        get_url
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
