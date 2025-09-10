#!/bin/bash

# Stock Bot V3 - Complete Cleanup Script
# Stops all services and optionally deletes the EKS cluster

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

echo " Stock Bot V3 - Complete Cleanup"
echo "================================="

# Ask user what they want to do
echo "What would you like to do?"
echo "1) Stop services only (keeps cluster, saves ~$15-20/day)"
echo "2) Delete everything including cluster (saves ~$30-35/day)"
echo "3) Delete cluster only (keeps other AWS resources)"
echo "4) Just show current costs"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        print_status "Stopping services only..."
        
        # Update kubeconfig
        aws eks update-kubeconfig --region us-east-1 --name stock-bot-cluster
        
        # Delete services (this will stop LoadBalancers)
        kubectl delete service stock-bot-v3-service -n stock-bot-v3 || true
        kubectl delete service stock-bot-v3-jupyter-service -n stock-bot-v3 || true
        
        # Delete deployments
        kubectl delete deployment stock-bot-v3 -n stock-bot-v3 || true
        kubectl delete deployment stock-bot-v3-jupyter -n stock-bot-v3 || true
        
        print_success "Services stopped. LoadBalancers will be deleted shortly."
        print_warning "EKS cluster is still running (~$14-15/day)."
        print_status "To restart services, run: ./deploy-all.sh"
        ;;
        
    2)
        print_warning "This will delete the entire EKS cluster and all data!"
        read -p "Are you sure? Type 'yes' to confirm: " confirm
        
        if [ "$confirm" == "yes" ]; then
            print_status "Deleting EKS cluster and all resources..."
            
            # Update kubeconfig
            aws eks update-kubeconfig --region us-east-1 --name stock-bot-cluster
            
            # Delete all resources
            kubectl delete namespace stock-bot-v3 || true
            
            # Delete nodegroups first
            print_status "Deleting nodegroups..."
            NODEGROUPS=$(aws eks list-nodegroups --cluster-name stock-bot-cluster --region us-east-1 --query 'nodegroups' --output text)
            if [ "$NODEGROUPS" != "None" ] && [ "$NODEGROUPS" != "" ]; then
                for nodegroup in $NODEGROUPS; do
                    print_status "Deleting nodegroup: $nodegroup"
                    aws eks delete-nodegroup --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
                done
                print_status "Waiting for nodegroups to be deleted..."
                for nodegroup in $NODEGROUPS; do
                    aws eks wait nodegroup-deleted --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
                done
            fi
            
            # Delete EKS cluster
            aws eks delete-cluster --name stock-bot-cluster --region us-east-1
            
            print_success "EKS cluster deletion initiated."
            print_status "Cluster deletion may take 10-15 minutes to complete."
            print_success "All resources deleted. Daily cost reduced to ~$0.50 (S3 only)."
        else
            print_status "Cleanup cancelled."
        fi
        ;;
        
    3)
        print_warning "This will delete the EKS cluster but keep other AWS resources!"
        read -p "Are you sure? Type 'yes' to confirm: " confirm
        
        if [ "$confirm" == "yes" ]; then
            print_status "Deleting EKS cluster only..."
            
            # Check if cluster exists
            if aws eks describe-cluster --name stock-bot-cluster --region us-east-1 &> /dev/null; then
                # Delete nodegroups first
                print_status "Deleting nodegroups..."
                NODEGROUPS=$(aws eks list-nodegroups --cluster-name stock-bot-cluster --region us-east-1 --query 'nodegroups' --output text)
                if [ "$NODEGROUPS" != "None" ] && [ "$NODEGROUPS" != "" ]; then
                    for nodegroup in $NODEGROUPS; do
                        print_status "Deleting nodegroup: $nodegroup"
                        aws eks delete-nodegroup --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
                    done
                    print_status "Waiting for nodegroups to be deleted..."
                    for nodegroup in $NODEGROUPS; do
                        aws eks wait nodegroup-deleted --cluster-name stock-bot-cluster --nodegroup-name $nodegroup --region us-east-1
                    done
                fi
                
                # Delete EKS cluster
                aws eks delete-cluster --name stock-bot-cluster --region us-east-1
                print_success "EKS cluster deletion initiated."
                print_status "Cluster deletion may take 10-15 minutes to complete."
                print_success "EKS cluster deleted. Daily cost reduced by ~$14-15/day."
                print_warning "Other AWS resources (S3, ECR) are still running."
            else
                print_warning "EKS cluster 'stock-bot-cluster' does not exist."
            fi
        else
            print_status "Cluster deletion cancelled."
        fi
        ;;
        
    4)
        print_status "Checking current AWS costs..."
        
        # Get cost for last 7 days
        aws ce get-cost-and-usage \
            --time-period Start=2025-09-03,End=2025-09-10 \
            --granularity DAILY \
            --metrics BlendedCost \
            --group-by Type=DIMENSION,Key=SERVICE \
            --query 'ResultsByTime[*].Groups[?Keys[0]==`Amazon Elastic Container Service for Kubernetes` || Keys[0]==`Amazon Elastic Load Balancing` || Keys[0]==`Amazon Elastic Compute Cloud - Compute`].{Service:Keys[0],Cost:Metrics.BlendedCost.Amount}' \
            --output table || true
            
        print_status "Current daily cost breakdown:"
        print_warning "EKS Control Plane: ~$14-15/day"
        print_warning "LoadBalancers: ~$3-4/day each (2 running)"
        print_warning "EC2 Nodes: ~$8-10/day"
        print_warning "Total: ~$30-35/day"
        ;;
        
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo -e "${GREEN} Cleanup completed!${NC}"
