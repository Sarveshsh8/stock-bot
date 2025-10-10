#!/bin/bash

# Deploy Stock Bot to EC2 with Public URL
# This creates a publicly accessible deployment

set -e

echo "=================================="
echo "Stock Bot - Public EC2 Deployment"
echo "=================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Please install it first."
    exit 1
fi

# Configuration
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
INSTANCE_TYPE="t3.medium"
KEY_NAME="stock-bot-key"
SECURITY_GROUP_NAME="stock-bot-sg"
AMI_ID="ami-0c55b159cbfafe1f0"  # Amazon Linux 2 (us-east-1)

echo "Configuration:"
echo "  Region: $REGION"
echo "  Instance Type: $INSTANCE_TYPE"
echo ""

# Step 1: Create Security Group
echo "Step 1: Creating Security Group..."
echo "------------------------------------"

SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for Stock Bot" \
    --region $REGION \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo "Security Group ID: $SG_ID"

# Allow HTTP (8501) from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 8501 already open"

# Allow SSH (22) from anywhere (for management)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 22 already open"

echo "✓ Security group configured"
echo ""

# Step 2: Create Key Pair (if not exists)
echo "Step 2: Setting up SSH Key..."
echo "------------------------------------"

if [ ! -f "$KEY_NAME.pem" ]; then
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > $KEY_NAME.pem
    chmod 400 $KEY_NAME.pem
    echo "✓ Created new key pair: $KEY_NAME.pem"
else
    echo "✓ Using existing key: $KEY_NAME.pem"
fi
echo ""

# Step 3: Create User Data Script
echo "Step 3: Preparing deployment script..."
echo "------------------------------------"

cat > user-data.sh << 'EOF'
#!/bin/bash

# Update system
yum update -y

# Install Docker
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
yum install -y git

# Clone repository
cd /home/ec2-user
git clone https://github.com/Sarveshsh8/stock-bot.git
cd stock-bot
git checkout stock-bot-v1

# Create .env file from environment variables
cat > .env << ENVEOF
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
S3_BUCKET_NAME=${S3_BUCKET_NAME}
USE_S3_INDEX=true
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
EMBEDDING_MODEL=all-MiniLM-L6-v2
ENVEOF

# Build and run
docker-compose up -d

# Setup auto-start on reboot
echo "cd /home/ec2-user/stock-bot && docker-compose up -d" >> /etc/rc.local
chmod +x /etc/rc.local

# Create status file
echo "Stock Bot deployed successfully at $(date)" > /home/ec2-user/deployment-status.txt
echo "Access the app at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501" >> /home/ec2-user/deployment-status.txt
EOF

echo "✓ Deployment script ready"
echo ""

# Step 4: Launch EC2 Instance
echo "Step 4: Launching EC2 Instance..."
echo "------------------------------------"

# Get latest Amazon Linux 2 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text \
    --region $REGION)

echo "Using AMI: $AMI_ID"

# Substitute environment variables in user-data script
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION S3_BUCKET_NAME
envsubst < user-data.sh > user-data-final.sh

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --user-data file://user-data-final.sh \
    --region $REGION \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Stock-Bot}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✓ Instance launched: $INSTANCE_ID"
echo ""

# Wait for instance to be running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=================================="
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "=================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo ""
echo "Access URLs:"
echo "  Stock Bot: http://$PUBLIC_IP:8501"
echo ""
echo "Share this URL with others:"
echo "  🔗 http://$PUBLIC_IP:8501"
echo ""
echo "SSH Access:"
echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "Note: It may take 5-10 minutes for the app to be ready"
echo "      (Docker installation + image build + index download)"
echo ""
echo "Check status:"
echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP 'cat deployment-status.txt'"
echo ""
echo "View logs:"
echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP 'cd stock-bot && docker-compose logs -f'"
echo ""
echo "=================================="

# Save deployment info
cat > deployment-info.txt << EOF
Stock Bot Deployment Information
=================================

Deployed: $(date)
Region: $REGION
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP

Access URL: http://$PUBLIC_IP:8501

SSH Command:
ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP

To stop the instance:
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION

To terminate the instance:
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION
EOF

echo "Deployment info saved to: deployment-info.txt"
echo ""

# Cleanup
rm -f user-data.sh user-data-final.sh

