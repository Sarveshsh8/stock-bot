#!/bin/bash

# Stock Bot EKS Deployment Setup Script
# This script sets up the EKS cluster and deploys the Stock Bot application

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

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v eksctl &> /dev/null; then
        missing_tools+=("eksctl")
    fi
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_status "Please install the missing tools and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Configure AWS credentials
configure_aws() {
    print_status "Configuring AWS credentials..."
    
    # Load environment variables from .env file
    if [ -f ".env" ]; then
        print_status "Loading AWS credentials from .env file..."
        # Unset any existing AWS profile to avoid conflicts
        unset AWS_PROFILE
        unset AWS_SHARED_CREDENTIALS_FILE
        unset AWS_CONFIG_FILE
        
        # Load environment variables
        export $(grep -v '^#' .env | xargs)
        
        # Set AWS credentials as environment variables
        export AWS_ACCESS_KEY_ID
        export AWS_SECRET_ACCESS_KEY
        export AWS_DEFAULT_REGION
    fi
    
    # Set AWS region from .env or default
    if [ -z "$AWS_DEFAULT_REGION" ]; then
        export AWS_DEFAULT_REGION="us-east-1"
    fi
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not working. Please check your .env file or run 'aws configure'."
        exit 1
    fi
    
    print_success "AWS credentials configured from .env file"
    print_status "Using region: $AWS_DEFAULT_REGION"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying AWS infrastructure with Terraform..."
    
    cd aws-infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan the deployment with environment variables
    AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
    terraform plan -out=tfplan
    
    # Apply the plan with environment variables
    AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
    terraform apply tfplan
    
    # Get outputs
    ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
    S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name)
    
    cd ../..
    
    print_success "Infrastructure deployed successfully"
    print_status "ECR Repository: $ECR_REPO_URL"
    print_status "S3 Bucket: $S3_BUCKET_NAME"
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get ECR repository URL
    ECR_REPO_URL=$(cd aws-infrastructure/terraform && terraform output -raw ecr_repository_url)
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL
    
    # Build main application image
    docker build -t $PROJECT_NAME .
    
    # Tag main image
    docker tag $PROJECT_NAME:latest $ECR_REPO_URL:latest
    
    # Push main image
    docker push $ECR_REPO_URL:latest
    
    # Build Jupyter image
    docker build -f Dockerfile.jupyter -t $PROJECT_NAME-jupyter .
    
    # Tag Jupyter image
    docker tag $PROJECT_NAME-jupyter:latest $ECR_REPO_URL-jupyter:latest
    
    # Push Jupyter image
    docker push $ECR_REPO_URL-jupyter:latest
    
    print_success "Docker images built and pushed successfully"
}

# Update kubeconfig
update_kubeconfig() {
    print_status "Updating kubeconfig..."
    
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    print_success "Kubeconfig updated"
}

# Install AWS Load Balancer Controller
install_alb_controller() {
    print_status "Installing AWS Load Balancer Controller..."
    
    # Create IAM policy
    curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json
    
    # Create IAM policy
    aws iam create-policy \
        --policy-name AWSLoadBalancerControllerIAMPolicy \
        --policy-document file://iam_policy.json \
        --region $AWS_REGION || true
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Create IAM role
    eksctl create iamserviceaccount \
        --cluster=$CLUSTER_NAME \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name AmazonEKSLoadBalancerControllerRole \
        --attach-policy-arn=arn:aws:iam::$ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
        --approve \
        --region $AWS_REGION
    
    # Install controller
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=$CLUSTER_NAME \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller
    
    # Clean up
    rm iam_policy.json
    
    print_success "AWS Load Balancer Controller installed"
}

# Deploy application
deploy_application() {
    print_status "Deploying Stock Bot application..."
    
    # Get ECR repository URL and S3 bucket name
    ECR_REPO_URL=$(cd aws-infrastructure/terraform && terraform output -raw ecr_repository_url)
    S3_BUCKET_NAME=$(cd aws-infrastructure/terraform && terraform output -raw s3_bucket_name)
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Create ConfigMap
    kubectl apply -f k8s/configmap.yaml
    
    # Create secrets (you need to update the values)
    print_warning "Please update k8s/secrets.yaml with your actual AWS credentials and S3 bucket name"
    print_status "S3 Bucket Name: $S3_BUCKET_NAME"
    kubectl apply -f k8s/secrets.yaml
    
    # Create ECR secret for image pulling
    kubectl create secret docker-registry ecr-secret \
        --docker-server=$ECR_REPO_URL \
        --docker-username=AWS \
        --docker-password=$(aws ecr get-login-password --region $AWS_REGION) \
        --namespace=$NAMESPACE || true
    
    # Update deployment with ECR image
    sed "s|stock-bot:latest|$ECR_REPO_URL:latest|g" k8s/deployment.yaml | kubectl apply -f -
    
    # Apply other resources
    kubectl apply -f k8s/persistent-volume.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Deploy Jupyter Lab
    print_status "Deploying Jupyter Lab..."
    
    # Create Jupyter PVC
    kubectl apply -f k8s/jupyter-pvc.yaml
    
    # Update Jupyter deployment with ECR image
    ECR_REPO_URL=$(cd aws-infrastructure/terraform && terraform output -raw ecr_repository_url)
    sed "s|stock-bot-jupyter:latest|$ECR_REPO_URL-jupyter:latest|g" k8s/jupyter-custom-deployment.yaml | kubectl apply -f -
    
    # Apply Jupyter services and ingress
    kubectl apply -f k8s/jupyter-service.yaml
    kubectl apply -f k8s/jupyter-ingress.yaml
    
    print_success "Application and Jupyter Lab deployed successfully"
}

# Wait for deployment to be ready
wait_for_deployment() {
    print_status "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/stock-bot-app -n $NAMESPACE
    
    print_success "Deployment is ready"
}

# Get application URLs
get_urls() {
    print_status "Getting application URLs..."
    
    # Get LoadBalancer URLs
    STREAMLIT_URL=$(kubectl get service stock-bot-streamlit -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    FLASK_URL=$(kubectl get service stock-bot-flask -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    JUPYTER_URL=$(kubectl get service jupyter-lab-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -n "$STREAMLIT_URL" ]; then
        print_success "Streamlit App: http://$STREAMLIT_URL"
    fi
    
    if [ -n "$FLASK_URL" ]; then
        print_success "Flask API: http://$FLASK_URL"
    fi
    
    if [ -n "$JUPYTER_URL" ]; then
        print_success "Jupyter Lab: http://$JUPYTER_URL"
        print_status "Jupyter Token: stock-bot-jupyter-2024"
    fi
    
    # Get Ingress URL if configured
    INGRESS_URL=$(kubectl get ingress stock-bot-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    if [ -n "$INGRESS_URL" ]; then
        print_success "Ingress URL: https://$INGRESS_URL"
    fi
}

# Main deployment function
main() {
    print_status "Starting Stock Bot EKS deployment..."
    
    check_prerequisites
    configure_aws
    deploy_infrastructure
    build_and_push_images
    update_kubeconfig
    install_alb_controller
    deploy_application
    wait_for_deployment
    get_urls
    
    print_success "Stock Bot deployment completed successfully!"
    print_status "You can now access your application using the URLs above."
}

# Run main function
main "$@"
