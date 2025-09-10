#!/bin/bash

# Stock Bot V3 - Quick Cluster Deletion Script
# Deletes the EKS cluster and all associated resources

set -e

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

echo "  Stock Bot V3 - Quick Cluster Deletion"
echo "========================================"

# Check if cluster exists
print_status "Checking if EKS cluster exists..."
if ! aws eks describe-cluster --name stock-bot-cluster --region us-east-1 &> /dev/null; then
    print_warning "EKS cluster 'stock-bot-cluster' does not exist."
    print_status "Nothing to delete."
    exit 0
fi

# Get cluster status
CLUSTER_STATUS=$(aws eks describe-cluster --name stock-bot-cluster --region us-east-1 --query 'cluster.status' --output text)
print_status "Cluster status: $CLUSTER_STATUS"

if [ "$CLUSTER_STATUS" == "DELETING" ]; then
    print_warning "Cluster is already being deleted."
    exit 0
fi

# Show current costs
print_warning "Current daily costs:"
print_warning "  EKS Control Plane: ~$14-15/day"
print_warning "  LoadBalancers: ~$3-4/day each"
print_warning "  EC2 Nodes: ~$8-10/day"
print_warning "  Total: ~$30-35/day"
echo ""

# Confirmation
print_warning "This will delete the EKS cluster and ALL associated resources!"
print_warning "This action cannot be undone!"
echo ""
read -p "Type 'DELETE' to confirm cluster deletion: " confirm

if [ "$confirm" != "DELETE" ]; then
    print_status "Cluster deletion cancelled."
    exit 0
fi

# Delete nodegroups first
print_status "Checking for nodegroups..."
NODEGROUPS=$(aws eks list-nodegroups --cluster-name stock-bot-cluster --region us-east-1 --query 'nodegroups' --output text)

if [ "$NODEGROUPS" != "None" ] && [ "$NODEGROUPS" != "" ]; then
    print_status "Found nodegroups: $NODEGROUPS"
    for nodegroup in $NODEGROUPS; do
        print_status "Deleting nodegroup: $nodegroup"
        aws eks delete-nodegroup --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
    done
    
    print_status "Waiting for nodegroups to be deleted..."
    for nodegroup in $NODEGROUPS; do
        aws eks wait nodegroup-deleted --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
    done
    print_success "All nodegroups deleted."
else
    print_status "No nodegroups found."
fi

# Delete cluster
print_status "Deleting EKS cluster 'stock-bot-cluster'..."
aws eks delete-cluster --name stock-bot-cluster --region us-east-1

print_success "EKS cluster deletion initiated!"
print_status "Cluster deletion may take 10-15 minutes to complete."
print_status "You can monitor the deletion in the AWS console."

# Show what's left
echo ""
print_success " Cluster deletion started!"
print_status "Remaining AWS resources (minimal cost):"
print_status "  - S3 buckets: ~$0.50/month"
print_status "  - ECR repositories: ~$0.10/month"
print_status "  - VPC: Free (no resources)"

echo ""
print_status "To completely recreate the system later, run:"
print_status "  ./deploy-all.sh"
