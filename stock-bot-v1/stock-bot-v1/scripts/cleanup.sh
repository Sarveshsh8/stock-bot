#!/bin/bash

# Stock Bot EKS Cleanup Script
# This script cleans up the EKS cluster and AWS resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="stock-bot"
AWS_REGION="us-west-2"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
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

# Delete Kubernetes resources
delete_k8s_resources() {
    print_status "Deleting Kubernetes resources..."
    
    # Delete ingress first
    kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
    kubectl delete -f k8s/jupyter-ingress.yaml --ignore-not-found=true
    
    # Delete services
    kubectl delete -f k8s/service.yaml --ignore-not-found=true
    kubectl delete -f k8s/jupyter-service.yaml --ignore-not-found=true
    
    # Delete deployments
    kubectl delete -f k8s/deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/jupyter-deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/jupyter-custom-deployment.yaml --ignore-not-found=true
    
    # Delete persistent volumes
    kubectl delete -f k8s/persistent-volume.yaml --ignore-not-found=true
    kubectl delete -f k8s/jupyter-pvc.yaml --ignore-not-found=true
    
    # Delete secrets and configmap
    kubectl delete -f k8s/secrets.yaml --ignore-not-found=true
    kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
    
    # Delete namespace
    kubectl delete -f k8s/namespace.yaml --ignore-not-found=true
    
    print_success "Kubernetes resources deleted"
}

# Delete EKS cluster
delete_eks_cluster() {
    print_status "Deleting EKS cluster..."
    
    eksctl delete cluster --name $CLUSTER_NAME --region $AWS_REGION --wait
    
    print_success "EKS cluster deleted"
}

# Delete infrastructure with Terraform
delete_infrastructure() {
    print_status "Deleting AWS infrastructure with Terraform..."
    
    cd aws-infrastructure/terraform
    
    # Destroy infrastructure
    terraform destroy -auto-approve
    
    cd ../..
    
    print_success "Infrastructure deleted"
}

# Main cleanup function
main() {
    print_warning "This will delete all Stock Bot resources. Are you sure? (y/N)"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Cleanup cancelled"
        exit 0
    fi
    
    print_status "Starting Stock Bot cleanup..."
    
    delete_k8s_resources
    delete_eks_cluster
    delete_infrastructure
    
    print_success "Stock Bot cleanup completed successfully!"
}

# Run main function
main "$@"
