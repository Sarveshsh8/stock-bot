#!/bin/bash

# Stock Bot V3 - Complete All-in-One Deployment Script
# Creates EKS cluster, builds image, pushes to ECR, and deploys everything

set -e

echo " Stock Bot V3 - Complete All-in-One Deployment"
echo "=============================================="

# Set AWS credentials
export AWS_ACCESS_KEY_ID=AKIAUJRTKQNULWFWRMNV
export AWS_SECRET_ACCESS_KEY=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
export AWS_DEFAULT_REGION=us-east-1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
print_status "Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

print_success "All prerequisites are installed."

# Step 1: Check if EKS cluster exists
print_status "Checking for existing EKS cluster..."
if aws eks describe-cluster --name stock-bot-cluster --region us-east-1 &> /dev/null; then
    CLUSTER_STATUS=$(aws eks describe-cluster --name stock-bot-cluster --region us-east-1 --query 'cluster.status' --output text)
    if [ "$CLUSTER_STATUS" == "ACTIVE" ]; then
        print_success "EKS cluster 'stock-bot-cluster' already exists and is active."
    else
        print_warning "EKS cluster exists but is in status: $CLUSTER_STATUS"
        print_status "Waiting for cluster to become active..."
        aws eks wait cluster-active --name stock-bot-cluster --region us-east-1
        print_success "Cluster is now active."
    fi
else
    print_status "EKS cluster does not exist. Creating cluster..."
    
    # Create cluster using Python script (more reliable than AWS CLI)
    python3 create_cluster.py
    
    if [ $? -eq 0 ]; then
        print_success "EKS cluster created successfully."
    else
        print_error "Failed to create EKS cluster."
        exit 1
    fi
fi

# Step 2: Update kubeconfig
print_status "Updating kubeconfig..."
aws eks update-kubeconfig --region us-east-1 --name stock-bot-cluster
print_success "Kubeconfig updated."

# Step 3: Build Docker image
print_status "Building Docker image..."
docker build --platform linux/amd64 -t stock-bot-v3:latest .

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully."
else
    print_error "Failed to build Docker image."
    exit 1
fi

# Step 4: Tag and push to ECR
print_status "Tagging image for ECR..."
docker tag stock-bot-v3:latest 295386645352.dkr.ecr.us-east-1.amazonaws.com/stock-bot-v3:latest

print_status "Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 295386645352.dkr.ecr.us-east-1.amazonaws.com

print_status "Pushing image to ECR..."
docker push 295386645352.dkr.ecr.us-east-1.amazonaws.com/stock-bot-v3:latest

print_success "Docker image pushed to ECR successfully."

# Step 5: Install EBS CSI driver if not already installed
print_status "Checking EBS CSI driver..."
if ! aws eks describe-addon --cluster-name stock-bot-cluster --addon-name aws-ebs-csi-driver --region us-east-1 &> /dev/null; then
    print_status "Installing EBS CSI driver..."
    aws eks create-addon --cluster-name stock-bot-cluster --addon-name aws-ebs-csi-driver --region us-east-1
    print_status "Waiting for EBS CSI driver to be active..."
    aws eks wait addon-active --cluster-name stock-bot-cluster --addon-name aws-ebs-csi-driver --region us-east-1
    print_success "EBS CSI driver installed successfully."
else
    print_success "EBS CSI driver already installed."
fi

# Step 6: Deploy Kubernetes resources
print_status "Deploying Kubernetes resources..."

# Create namespace
kubectl apply -f k8s/namespace.yaml
print_success "Namespace created."

# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml
print_success "ConfigMap applied."

# Create secrets
kubectl create secret generic aws-secrets -n stock-bot-v3 \
    --from-literal=aws-access-key-id=AKIAUJRTKQNULWFWRMNV \
    --from-literal=aws-secret-access-key=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 \
    --from-literal=aws-default-region=us-east-1 \
    --from-literal=s3-bucket-name=stock-analysis-bot \
    --dry-run=client -o yaml | kubectl apply -f -
print_success "Secrets created."

# Create service account
kubectl apply -f k8s/service-account.yaml
print_success "Service account created."

# Apply persistent volumes
kubectl apply -f k8s/persistent-volume.yaml
kubectl apply -f k8s/jupyter-pvc.yaml
print_success "Persistent volumes created."

# Deploy main application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
print_success "Main application deployed."

# Deploy Jupyter notebook
kubectl apply -f k8s/jupyter-deployment.yaml
kubectl apply -f k8s/jupyter-service.yaml
print_success "Jupyter notebook deployed."

# Step 7: Wait for deployments to be ready
print_status "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3 -n stock-bot-v3 || true
kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-v3-jupyter -n stock-bot-v3 || true

# Step 8: Get service URLs
print_status "Getting service URLs..."
echo "=========================================="
echo ""

# Get LoadBalancer URLs
FRONTEND_URL=$(kubectl get service stock-bot-v3-service -n stock-bot-v3 -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
JUPYTER_URL=$(kubectl get service stock-bot-v3-jupyter-service -n stock-bot-v3 -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo -e "${GREEN} Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE} Frontend + Backend (Streamlit + Flask API):${NC}"
echo "   URL: http://$FRONTEND_URL"
echo "   Ports: 80 (Streamlit), 5000 (Flask API)"
echo ""
echo -e "${BLUE} Jupyter Notebook:${NC}"
echo "   URL: http://$JUPYTER_URL"
echo "   Port: 80"
echo ""
echo -e "${BLUE} Pod Status:${NC}"
kubectl get pods -n stock-bot-v3
echo ""
echo -e "${BLUE} Service Status:${NC}"
kubectl get services -n stock-bot-v3
echo ""
echo "=========================================="
echo -e "${YELLOW} Management Commands:${NC}"
echo "   Check status: ./control.sh status"
echo "   Get URLs: ./control.sh urls"
echo "   View logs: ./control.sh logs"
echo "   Stop services: ./control.sh stop"
echo ""
echo -e "${RED}  Cost Management:${NC}"
echo "   Current daily cost: ~$30-35/day"
echo "   To stop charges: ./control.sh stop"
echo "   To delete cluster: aws eks delete-cluster --name stock-bot-cluster"
echo ""
echo -e "${GREEN} Stock Bot V3 is now fully deployed and running!${NC}"
