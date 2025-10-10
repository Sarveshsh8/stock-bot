#!/bin/bash

# AWS Deployment Script for Stock Bot
# This script helps deploy the Stock Bot to AWS

set -e

echo "=================================="
echo "Stock Bot - AWS Deployment"
echo "=================================="
echo ""

# Configuration
APP_NAME="stock-bot"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME}"

# Step 1: Upload FAISS Index to S3
echo "Step 1: Uploading FAISS Index to S3"
echo "------------------------------------"

if [ -d "faiss_index_all" ]; then
    echo "Found local FAISS index"
    
    if [ -z "$S3_BUCKET" ]; then
        echo "Error: S3_BUCKET_NAME not set in environment"
        echo "Please set: export S3_BUCKET_NAME=your-bucket-name"
        exit 1
    fi
    
    echo "Uploading to S3 bucket: $S3_BUCKET"
    python3 s3_faiss_manager.py upload "$S3_BUCKET" "faiss_index_all"
    echo "✓ Index uploaded to S3"
else
    echo "Warning: No local FAISS index found"
    echo "The index will be built on first run (this may take time)"
fi

echo ""
echo "Step 2: Choose Deployment Method"
echo "------------------------------------"
echo "1. Docker (local testing)"
echo "2. AWS EC2"
echo "3. AWS ECS (Fargate)"
echo "4. AWS App Runner"
echo ""
read -p "Select deployment method (1-4): " DEPLOY_METHOD

case $DEPLOY_METHOD in
    1)
        echo ""
        echo "Building Docker image..."
        docker build -t $APP_NAME .
        
        echo ""
        echo "Running Docker container..."
        docker run -p 8501:8501 \
            -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
            -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
            -e AWS_DEFAULT_REGION="$REGION" \
            -e S3_BUCKET_NAME="$S3_BUCKET" \
            -e USE_S3_INDEX="true" \
            $APP_NAME
        ;;
    
    2)
        echo ""
        echo "EC2 Deployment Instructions:"
        echo "1. Launch an EC2 instance (t3.medium or larger recommended)"
        echo "2. SSH into the instance"
        echo "3. Install Docker:"
        echo "   sudo yum update -y"
        echo "   sudo yum install -y docker"
        echo "   sudo service docker start"
        echo "4. Clone your repository"
        echo "5. Run: ./deploy_to_aws.sh and select option 1"
        ;;
    
    3)
        echo ""
        echo "ECS Deployment Steps:"
        echo "1. Push Docker image to ECR"
        echo "2. Create ECS task definition"
        echo "3. Create ECS service"
        echo ""
        echo "Would you like to proceed? (y/n)"
        read -p "> " PROCEED
        
        if [ "$PROCEED" = "y" ]; then
            # Create ECR repository
            aws ecr create-repository --repository-name $APP_NAME --region $REGION || true
            
            # Get ECR URL
            ECR_URL=$(aws ecr describe-repositories --repository-names $APP_NAME --region $REGION --query 'repositories[0].repositoryUri' --output text)
            
            # Login to ECR
            aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL
            
            # Build and push
            docker build -t $APP_NAME .
            docker tag $APP_NAME:latest $ECR_URL:latest
            docker push $ECR_URL:latest
            
            echo "✓ Docker image pushed to ECR: $ECR_URL"
            echo ""
            echo "Next: Create ECS Task Definition and Service in AWS Console"
        fi
        ;;
    
    4)
        echo ""
        echo "App Runner Deployment:"
        echo "1. Push code to GitHub"
        echo "2. Go to AWS App Runner console"
        echo "3. Create service from source code"
        echo "4. Select your GitHub repository"
        echo "5. Configure build settings (Python, port 8501)"
        echo "6. Add environment variables"
        ;;
    
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo "Deployment process completed!"
echo "=================================="

