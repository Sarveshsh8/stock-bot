#!/bin/bash

# Simple EC2 Deployment - No Docker Required
# Deploys Stock Bot directly with Python + Streamlit

set -e

echo "========================================="
echo "Stock Bot - Simple EC2 Deployment"
echo "No Docker Required"
echo "========================================="
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
S3_BUCKET="${S3_BUCKET_NAME:-stock-bot-algoseek}"

echo "Configuration:"
echo "  Region: $REGION"
echo "  Instance: $INSTANCE_TYPE"
echo "  S3 Bucket: $S3_BUCKET"
echo ""

# Step 1: Create Security Group
echo "Step 1: Setting up Security Group..."
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

# Allow Streamlit port (8501)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 8501 already open"

# Allow SSH
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 22 already open"

echo "✓ Security group configured"
echo ""

# Step 2: Create Key Pair
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

# Step 3: Create deployment script for EC2
echo "Step 3: Creating deployment script..."
echo "------------------------------------"

cat > setup_stock_bot.sh << 'SETUP_EOF'
#!/bin/bash
set -e

echo "Installing Stock Bot on EC2..."

# Update system
sudo yum update -y

# Install Python 3.10
sudo yum install -y python3.10 python3.10-pip git

# Set Python 3.10 as default
sudo alternatives --set python3 /usr/bin/python3.10

# Clone repository
cd /home/ec2-user
if [ -d "stock-bot" ]; then
    cd stock-bot
    git pull origin stock-bot-v1
else
    git clone https://github.com/Sarveshsh8/stock-bot.git
    cd stock-bot
    git checkout stock-bot-v1
fi

# Install Python dependencies
echo "Installing dependencies..."
pip3 install --user -r requirements.txt

# Create .env file with AWS credentials
cat > .env << 'ENV_EOF'
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
S3_BUCKET_NAME=${S3_BUCKET_NAME}
USE_S3_INDEX=true
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
EMBEDDING_MODEL=all-MiniLM-L6-v2
ENV_EOF

# Create systemd service for auto-start
sudo tee /etc/systemd/system/stock-bot.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Stock Bot Streamlit App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/stock-bot
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ec2-user/.local/bin/streamlit run app_aws_deployment.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable stock-bot
sudo systemctl start stock-bot

echo "✓ Stock Bot service started!"
echo ""
echo "Status:"
sudo systemctl status stock-bot --no-pager | head -20

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo "========================================="
echo "✓ DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Access your Stock Bot at:"
echo "  http://$PUBLIC_IP:8501"
echo ""
echo "Share this URL with others!"
echo ""
SETUP_EOF

chmod +x setup_stock_bot.sh

# Substitute environment variables
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION S3_BUCKET_NAME
envsubst < setup_stock_bot.sh > setup_stock_bot_final.sh
chmod +x setup_stock_bot_final.sh

echo "✓ Deployment script created"
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

# Create user data script
cat > user-data.txt << 'USERDATA_EOF'
#!/bin/bash
cd /home/ec2-user
cat > /home/ec2-user/install.log 2>&1 << 'LOG_EOF'
Installing Stock Bot...
LOG_EOF
USERDATA_EOF

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
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

echo "✓ Instance running at: $PUBLIC_IP"
echo ""

# Wait for SSH to be ready
echo "Waiting for SSH to be ready (this may take 1-2 minutes)..."
sleep 30

MAX_RETRIES=10
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i $KEY_NAME.pem ec2-user@$PUBLIC_IP "echo SSH Ready" 2>/dev/null; then
        echo "✓ SSH connection established"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "  Retry $RETRY/$MAX_RETRIES..."
    sleep 10
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "✗ Could not connect via SSH. Try manually:"
    echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
    exit 1
fi

echo ""

# Step 5: Deploy Stock Bot
echo "Step 5: Deploying Stock Bot..."
echo "------------------------------------"

# Copy deployment script
scp -o StrictHostKeyChecking=no -i $KEY_NAME.pem setup_stock_bot_final.sh ec2-user@$PUBLIC_IP:/home/ec2-user/

# Run deployment
ssh -o StrictHostKeyChecking=no -i $KEY_NAME.pem ec2-user@$PUBLIC_IP "bash /home/ec2-user/setup_stock_bot_final.sh"

echo ""
echo "========================================="
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "========================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Region: $REGION"
echo ""
echo "🔗 ACCESS YOUR STOCK BOT:"
echo "  http://$PUBLIC_IP:8501"
echo ""
echo "Share this URL with anyone!"
echo ""
echo "SSH Access:"
echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "Useful Commands:"
echo "  Check status:  sudo systemctl status stock-bot"
echo "  View logs:     sudo journalctl -u stock-bot -f"
echo "  Restart:       sudo systemctl restart stock-bot"
echo "  Stop:          sudo systemctl stop stock-bot"
echo ""
echo "To stop the EC2 instance:"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "To terminate the EC2 instance:"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "========================================="

# Save deployment info
cat > deployment-info.txt << EOF
Stock Bot Deployment Information
=================================

Deployed: $(date)
Region: $REGION
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
S3 Bucket: $S3_BUCKET

🔗 ACCESS URL: http://$PUBLIC_IP:8501

SSH Command:
ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP

Service Commands:
sudo systemctl status stock-bot    # Check status
sudo systemctl restart stock-bot   # Restart
sudo journalctl -u stock-bot -f    # View logs

AWS Commands:
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION        # Stop
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION       # Start
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION   # Terminate
EOF

echo "✓ Deployment info saved to: deployment-info.txt"
echo ""

# Cleanup
rm -f user-data.txt setup_stock_bot.sh setup_stock_bot_final.sh

