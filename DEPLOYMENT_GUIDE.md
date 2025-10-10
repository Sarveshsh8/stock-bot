# AWS Deployment Guide

Complete guide to deploy Stock Bot on AWS with S3 FAISS index storage.

## Prerequisites

1. AWS Account with:
   - Bedrock Nova Pro access
   - S3 bucket access
   - EC2/ECS access (for deployment)

2. Local setup:
   - Docker installed
   - AWS CLI configured
   - FAISS index built locally

## Quick Start

### 1. Create S3 Bucket

```bash
# Create bucket for FAISS index
aws s3 mb s3://your-stock-bot-index --region us-east-1
```

### 2. Upload FAISS Index to S3

```bash
# Upload your local index
python3 s3_faiss_manager.py upload your-stock-bot-index faiss_index_all
```

### 3. Update Environment Variables

Add to `.env`:
```env
# S3 Configuration
S3_BUCKET_NAME=your-stock-bot-index
USE_S3_INDEX=true
```

### 4. Deploy

```bash
./deploy_to_aws.sh
```

## Deployment Options

### Option 1: Docker (Local Testing)

Test the deployment locally:

```bash
# Build image
docker build -t stock-bot .

# Run container
docker run -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e S3_BUCKET_NAME=your-stock-bot-index \
  -e USE_S3_INDEX=true \
  stock-bot
```

Access at: http://localhost:8501

### Option 2: AWS EC2

**Launch EC2 Instance:**

1. Go to EC2 Console
2. Launch Instance:
   - AMI: Amazon Linux 2
   - Instance Type: t3.medium (minimum)
   - Security Group: Allow port 8501
   - Storage: 30 GB

3. Connect via SSH:
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

4. Install Docker:
```bash
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
```

5. Clone and run:
```bash
git clone https://github.com/Sarveshsh8/stock-bot.git
cd stock-bot
git checkout stock-bot-v1

# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET_NAME=your-bucket
export USE_S3_INDEX=true

# Run
docker build -t stock-bot .
docker run -d -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e S3_BUCKET_NAME \
  -e USE_S3_INDEX \
  --restart unless-stopped \
  stock-bot
```

Access at: `http://your-ec2-ip:8501`

### Option 3: AWS ECS (Fargate)

**1. Push to ECR:**

```bash
# Create ECR repository
aws ecr create-repository --repository-name stock-bot

# Get login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t stock-bot .
docker tag stock-bot:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/stock-bot:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/stock-bot:latest
```

**2. Create Task Definition:**

```json
{
  "family": "stock-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "stock-bot",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/stock-bot:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "S3_BUCKET_NAME", "value": "your-bucket"},
        {"name": "USE_S3_INDEX", "value": "true"}
      ],
      "secrets": [
        {"name": "AWS_ACCESS_KEY_ID", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

**3. Create ECS Service:**

- Use Fargate
- Create Application Load Balancer
- Configure health checks

### Option 4: AWS App Runner

1. Go to App Runner Console
2. Create Service:
   - Source: GitHub repository
   - Repository: `Sarveshsh8/stock-bot`
   - Branch: `stock-bot-v1`
   - Build: Python
   - Port: 8501
   - Start command: `streamlit run app_aws_deployment.py`

3. Add Environment Variables:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET_NAME`
   - `USE_S3_INDEX=true`

4. Deploy

## S3 FAISS Manager

### Upload Index

```bash
python3 s3_faiss_manager.py upload your-bucket faiss_index_all
```

### Download Index

```bash
python3 s3_faiss_manager.py download your-bucket
```

### Check if Index Exists

```bash
python3 s3_faiss_manager.py check your-bucket
```

## Environment Variables

### Required for Deployment:

```env
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0

# S3 for FAISS Index
S3_BUCKET_NAME=your-stock-bot-index
USE_S3_INDEX=true

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Cost Estimate

### S3 Storage
- FAISS Index: ~500 MB - $0.01/month
- Negligible cost

### EC2 (t3.medium)
- Instance: $0.0416/hour = ~$30/month
- Data transfer: ~$0.09/GB

### ECS Fargate
- 1 vCPU, 2 GB RAM: ~$35/month
- Auto-scaling available

### Nova Pro Usage
- Per query: ~$0.01
- 100 queries/day: ~$30/month

**Total**: ~$60-70/month (EC2/ECS + Nova)

## Monitoring

### CloudWatch Logs

Enable logs for debugging:

```bash
# View logs
aws logs tail /aws/ecs/stock-bot --follow
```

### Application Health

Check health endpoint:
```bash
curl http://your-app-url/_stcore/health
```

## Troubleshooting

### Index Download Fails

```bash
# Check S3 access
aws s3 ls s3://your-bucket/

# Check IAM permissions
aws iam get-user
```

### Memory Issues

Increase instance size:
- EC2: Use t3.large instead of t3.medium
- ECS: Increase memory to 4096 MB

### Slow First Load

Normal - downloading index from S3 takes 1-2 minutes on first run.

## Security Best Practices

1. **Use AWS Secrets Manager** for credentials
2. **Enable VPC** for ECS/EC2
3. **Use IAM roles** instead of access keys when possible
4. **Enable HTTPS** with ALB + ACM certificate
5. **Set up WAF** for production

## Updating the Application

```bash
# Update code
git pull origin stock-bot-v1

# Rebuild and redeploy
docker build -t stock-bot .
docker push YOUR_ECR_URL

# Update ECS service (auto-deploys new version)
aws ecs update-service --cluster your-cluster --service stock-bot --force-new-deployment
```

## Support

- Check logs: `docker logs container_id`
- Test locally first: `docker run -it stock-bot /bin/bash`
- Verify S3 access: `python3 s3_faiss_manager.py check your-bucket`

---

**Ready to Deploy!** 🚀

Start with Docker testing, then move to EC2 or ECS for production.

