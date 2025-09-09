#!/bin/bash

# Stock Bot V3 - Deployment Script
# Deploys the unified financial analysis platform to Kubernetes

set -e

echo " Stock Bot V3 - Deployment Script"
echo "=================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo " kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo " Docker is not installed. Please install Docker first."
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -t stock-bot-v3:latest .

# Apply Kubernetes manifests
echo "🔧 Applying Kubernetes manifests..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# Apply Secrets (using existing secrets file)
echo "🔐 Applying secrets..."
kubectl apply -f k8s/secrets.yaml

# Apply PersistentVolumeClaim
kubectl apply -f k8s/persistent-volume.yaml

# Apply Deployment
kubectl apply -f k8s/deployment.yaml

# Apply Service
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3 -n stock-bot-v3

# Get service information
echo "🌐 Getting service information..."
kubectl get service stock-bot-v3-service -n stock-bot-v3

# Get LoadBalancer URL
echo "🔗 Getting LoadBalancer URL..."
EXTERNAL_IP=$(kubectl get service stock-bot-v3-service -n stock-bot-v3 -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get service stock-bot-v3-service -n stock-bot-v3 -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ -n "$EXTERNAL_IP" ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Streamlit App: http://$EXTERNAL_IP"
    echo "🔌 Flask API: http://$EXTERNAL_IP:5000"
else
    echo "⚠️  LoadBalancer IP not available yet. Check with:"
    echo "   kubectl get service stock-bot-v3-service -n stock-bot-v3"
fi

echo "📊 Check deployment status with:"
echo "   kubectl get pods -n stock-bot-v3"
echo "   kubectl logs -f deployment/stock-bot-v3 -n stock-bot-v3"
