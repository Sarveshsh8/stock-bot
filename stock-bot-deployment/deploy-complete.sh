#!/bin/bash

# Stock Bot V3 - Complete Deployment Script
# Deploys both frontend/backend and Jupyter notebook on EKS

set -e

echo "🚀 Stock Bot V3 - Complete EKS Deployment"
echo "=========================================="

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Get deployment type
echo "Select deployment type:"
echo "1) Frontend + Backend only"
echo "2) Jupyter Notebook only"
echo "3) Complete system (Frontend + Backend + Jupyter)"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        DEPLOY_TYPE="frontend-backend"
        echo "📱 Deploying Frontend + Backend..."
        ;;
    2)
        DEPLOY_TYPE="jupyter"
        echo "📓 Deploying Jupyter Notebook..."
        ;;
    3)
        DEPLOY_TYPE="complete"
        echo "🎯 Deploying Complete System..."
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t stock-bot-v3:latest .

# Apply namespace
echo "📁 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap
echo "⚙️  Applying configuration..."
kubectl apply -f k8s/configmap.yaml

# Apply Secrets (user needs to update with actual credentials)
echo "🔐 Please update k8s/secrets.yaml with your actual AWS credentials before proceeding."
read -p "Have you updated the secrets file? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please update secrets and run again."
    exit 1
fi

kubectl apply -f k8s/secrets.yaml

# Apply PersistentVolume
echo "💾 Setting up persistent storage..."
kubectl apply -f k8s/persistent-volume.yaml

# Deploy based on choice
case $DEPLOY_TYPE in
    "frontend-backend")
        echo "🚀 Deploying Frontend + Backend..."
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        ;;
    "jupyter")
        echo "📓 Deploying Jupyter Notebook..."
        kubectl apply -f k8s/jupyter-pvc.yaml
        kubectl apply -f k8s/jupyter-deployment.yaml
        kubectl apply -f k8s/jupyter-service.yaml
        ;;
    "complete")
        echo "🎯 Deploying Complete System..."
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        kubectl apply -f k8s/jupyter-pvc.yaml
        kubectl apply -f k8s/jupyter-deployment.yaml
        kubectl apply -f k8s/jupyter-service.yaml
        ;;
esac

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3 -n stock-bot-v3 || true
kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3-jupyter -n stock-bot-v3 || true

# Get service URLs
echo "🌐 Getting service URLs..."
echo "=========================================="

if [[ "$DEPLOY_TYPE" == "frontend-backend" || "$DEPLOY_TYPE" == "complete" ]]; then
    echo "📱 Frontend + Backend Service:"
    kubectl get service stock-bot-v3-service -n stock-bot-v3
    echo ""
fi

if [[ "$DEPLOY_TYPE" == "jupyter" || "$DEPLOY_TYPE" == "complete" ]]; then
    echo "📓 Jupyter Notebook Service:"
    kubectl get service stock-bot-v3-jupyter-service -n stock-bot-v3
    echo ""
fi

# Show pod status
echo "📊 Pod Status:"
kubectl get pods -n stock-bot-v3

echo ""
echo "✅ Deployment completed!"
echo "=========================================="
echo "Next steps:"
echo "1. Wait for LoadBalancer to get external IP"
echo "2. Access services using the external IPs"
echo "3. Check logs: kubectl logs -f deployment/stock-bot-v3 -n stock-bot-v3"
echo "4. Check Jupyter logs: kubectl logs -f deployment/stock-bot-v3-jupyter -n stock-bot-v3"
