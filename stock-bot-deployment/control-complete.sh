#!/bin/bash

# Stock Bot V3 - Complete Control Script
# Manages both frontend/backend and Jupyter deployments

set -e

NAMESPACE="stock-bot-v3"

show_help() {
    echo "Stock Bot V3 - Complete Control Script"
    echo "======================================"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status     - Show status of all deployments"
    echo "  logs       - Show logs from all services"
    echo "  urls       - Show service URLs"
    echo "  restart    - Restart all deployments"
    echo "  stop       - Stop all deployments"
    echo "  start      - Start all deployments"
    echo "  clean      - Clean up all resources"
    echo "  frontend   - Show frontend/backend status only"
    echo "  jupyter    - Show Jupyter status only"
    echo "  help       - Show this help message"
}

show_status() {
    echo "📊 Stock Bot V3 - Deployment Status"
    echo "===================================="
    
    echo "🏗️  Namespace:"
    kubectl get namespace $NAMESPACE 2>/dev/null || echo "❌ Namespace not found"
    echo ""
    
    echo "🚀 Deployments:"
    kubectl get deployments -n $NAMESPACE 2>/dev/null || echo "❌ No deployments found"
    echo ""
    
    echo "🌐 Services:"
    kubectl get services -n $NAMESPACE 2>/dev/null || echo "❌ No services found"
    echo ""
    
    echo "📦 Pods:"
    kubectl get pods -n $NAMESPACE 2>/dev/null || echo "❌ No pods found"
    echo ""
    
    echo "💾 Persistent Volumes:"
    kubectl get pvc -n $NAMESPACE 2>/dev/null || echo "❌ No PVCs found"
}

show_logs() {
    echo "📋 Stock Bot V3 - Service Logs"
    echo "==============================="
    
    echo "🖥️  Frontend/Backend Logs:"
    kubectl logs -f deployment/stock-bot-v3 -n $NAMESPACE --tail=50 || echo "❌ Frontend/Backend not running"
    echo ""
    
    echo "📓 Jupyter Logs:"
    kubectl logs -f deployment/stock-bot-v3-jupyter -n $NAMESPACE --tail=50 || echo "❌ Jupyter not running"
}

show_urls() {
    echo "🌐 Stock Bot V3 - Service URLs"
    echo "==============================="
    
    echo "📱 Frontend/Backend Service:"
    kubectl get service stock-bot-v3-service -n $NAMESPACE 2>/dev/null || echo "❌ Frontend/Backend service not found"
    echo ""
    
    echo "📓 Jupyter Notebook Service:"
    kubectl get service stock-bot-v3-jupyter-service -n $NAMESPACE 2>/dev/null || echo "❌ Jupyter service not found"
    echo ""
    
    echo "💡 Access Instructions:"
    echo "- Frontend: http://[EXTERNAL-IP] (Streamlit interface)"
    echo "- Backend API: http://[EXTERNAL-IP]:5000 (Flask API)"
    echo "- Jupyter: http://[EXTERNAL-IP] (Jupyter notebook)"
}

restart_deployments() {
    echo "🔄 Restarting Stock Bot V3 Deployments..."
    echo "=========================================="
    
    echo "🖥️  Restarting Frontend/Backend..."
    kubectl rollout restart deployment/stock-bot-v3 -n $NAMESPACE || echo "❌ Frontend/Backend not found"
    
    echo "📓 Restarting Jupyter..."
    kubectl rollout restart deployment/stock-bot-v3-jupyter -n $NAMESPACE || echo "❌ Jupyter not found"
    
    echo "⏳ Waiting for deployments to be ready..."
    kubectl rollout status deployment/stock-bot-v3 -n $NAMESPACE --timeout=300s || true
    kubectl rollout status deployment/stock-bot-v3-jupyter -n $NAMESPACE --timeout=300s || true
    
    echo "✅ Restart completed!"
}

stop_deployments() {
    echo "⏹️  Stopping Stock Bot V3 Deployments..."
    echo "========================================"
    
    echo "🖥️  Stopping Frontend/Backend..."
    kubectl scale deployment stock-bot-v3 --replicas=0 -n $NAMESPACE || echo "❌ Frontend/Backend not found"
    
    echo "📓 Stopping Jupyter..."
    kubectl scale deployment stock-bot-v3-jupyter --replicas=0 -n $NAMESPACE || echo "❌ Jupyter not found"
    
    echo "✅ All deployments stopped!"
}

start_deployments() {
    echo "▶️  Starting Stock Bot V3 Deployments..."
    echo "======================================="
    
    echo "🖥️  Starting Frontend/Backend..."
    kubectl scale deployment stock-bot-v3 --replicas=2 -n $NAMESPACE || echo "❌ Frontend/Backend not found"
    
    echo "📓 Starting Jupyter..."
    kubectl scale deployment stock-bot-v3-jupyter --replicas=1 -n $NAMESPACE || echo "❌ Jupyter not found"
    
    echo "⏳ Waiting for deployments to be ready..."
    kubectl rollout status deployment/stock-bot-v3 -n $NAMESPACE --timeout=300s || true
    kubectl rollout status deployment/stock-bot-v3-jupyter -n $NAMESPACE --timeout=300s || true
    
    echo "✅ All deployments started!"
}

clean_resources() {
    echo "🧹 Cleaning up Stock Bot V3 Resources..."
    echo "========================================"
    
    read -p "⚠️  This will delete ALL resources. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cleanup cancelled."
        exit 1
    fi
    
    echo "🗑️  Deleting deployments..."
    kubectl delete deployment stock-bot-v3 -n $NAMESPACE || true
    kubectl delete deployment stock-bot-v3-jupyter -n $NAMESPACE || true
    
    echo "🗑️  Deleting services..."
    kubectl delete service stock-bot-v3-service -n $NAMESPACE || true
    kubectl delete service stock-bot-v3-jupyter-service -n $NAMESPACE || true
    
    echo "🗑️  Deleting PVCs..."
    kubectl delete pvc stock-bot-v3-pvc -n $NAMESPACE || true
    kubectl delete pvc stock-bot-v3-jupyter-pvc -n $NAMESPACE || true
    
    echo "🗑️  Deleting ConfigMap and Secrets..."
    kubectl delete configmap stock-bot-v3-config -n $NAMESPACE || true
    kubectl delete secret aws-secrets -n $NAMESPACE || true
    
    echo "🗑️  Deleting namespace..."
    kubectl delete namespace $NAMESPACE || true
    
    echo "✅ Cleanup completed!"
}

show_frontend_status() {
    echo "📱 Frontend/Backend Status"
    echo "=========================="
    kubectl get deployment stock-bot-v3 -n $NAMESPACE 2>/dev/null || echo "❌ Frontend/Backend not deployed"
    kubectl get service stock-bot-v3-service -n $NAMESPACE 2>/dev/null || echo "❌ Frontend/Backend service not found"
    kubectl get pods -l app=stock-bot-v3 -n $NAMESPACE 2>/dev/null || echo "❌ Frontend/Backend pods not found"
}

show_jupyter_status() {
    echo "📓 Jupyter Notebook Status"
    echo "=========================="
    kubectl get deployment stock-bot-v3-jupyter -n $NAMESPACE 2>/dev/null || echo "❌ Jupyter not deployed"
    kubectl get service stock-bot-v3-jupyter-service -n $NAMESPACE 2>/dev/null || echo "❌ Jupyter service not found"
    kubectl get pods -l app=stock-bot-v3-jupyter -n $NAMESPACE 2>/dev/null || echo "❌ Jupyter pods not found"
}

# Main script logic
case "${1:-help}" in
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    urls)
        show_urls
        ;;
    restart)
        restart_deployments
        ;;
    stop)
        stop_deployments
        ;;
    start)
        start_deployments
        ;;
    clean)
        clean_resources
        ;;
    frontend)
        show_frontend_status
        ;;
    jupyter)
        show_jupyter_status
        ;;
    help|*)
        show_help
        ;;
esac
