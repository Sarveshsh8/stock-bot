# Simple EC2 Deployment Guide (No Docker)

Deploy Stock Bot to EC2 with just Python and Streamlit - no Docker required!

## Quick Deploy (1 Command)

```bash
./deploy_ec2_simple.sh
```

That's it! The script will:
1. Create EC2 instance
2. Install Python + dependencies
3. Clone your code from GitHub
4. Start Streamlit service
5. Give you a shareable URL

**Time**: 5-10 minutes  
**Result**: Public URL like `http://54.123.45.67:8501`

---

## Prerequisites

1. **AWS CLI** configured:
```bash
aws configure
# Enter your AWS credentials
```

2. **Environment Variables**:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET_NAME=stock-bot-algoseek
export AWS_DEFAULT_REGION=us-east-1
```

---

## Manual Deployment Steps

If you prefer manual setup:

### 1. Launch EC2 Instance

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key \
  --security-group-ids sg-xxx

# Open port 8501 in security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0
```

### 2. Connect to Instance

```bash
ssh -i your-key.pem ec2-user@YOUR_IP
```

### 3. Install Dependencies

```bash
# Update system
sudo yum update -y

# Install Python 3.10
sudo yum install -y python3.10 python3.10-pip git

# Set as default
sudo alternatives --set python3 /usr/bin/python3.10
```

### 4. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Sarveshsh8/stock-bot.git
cd stock-bot
git checkout stock-bot-v1

# Install dependencies
pip3 install --user -r requirements.txt
```

### 5. Create .env File

```bash
cat > .env << EOF
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=stock-bot-algoseek
USE_S3_INDEX=true
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
EMBEDDING_MODEL=all-MiniLM-L6-v2
EOF
```

### 6. Create Systemd Service (Auto-Start)

```bash
sudo tee /etc/systemd/system/stock-bot.service > /dev/null << EOF
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
EOF
```

### 7. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-bot
sudo systemctl start stock-bot
```

### 8. Check Status

```bash
sudo systemctl status stock-bot
```

---

## Access Your Bot

Your bot will be available at:
```
http://YOUR_EC2_PUBLIC_IP:8501
```

Find your IP:
```bash
curl http://checkip.amazonaws.com
```

Or in AWS Console:
```bash
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
```

---

## Service Management

### Check Status
```bash
sudo systemctl status stock-bot
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u stock-bot -f

# Last 100 lines
sudo journalctl -u stock-bot -n 100
```

### Restart Service
```bash
sudo systemctl restart stock-bot
```

### Stop Service
```bash
sudo systemctl stop stock-bot
```

### Start Service
```bash
sudo systemctl start stock-bot
```

---

## Update Your Code

To deploy updates:

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@YOUR_IP

# Pull latest code
cd stock-bot
git pull origin stock-bot-v1

# Restart service
sudo systemctl restart stock-bot
```

---

## Troubleshooting

### Check if service is running
```bash
sudo systemctl status stock-bot
```

### Check if port is open
```bash
sudo netstat -tulpn | grep 8501
```

### Test Streamlit manually
```bash
cd /home/ec2-user/stock-bot
~/.local/bin/streamlit run app_aws_deployment.py --server.port=8501
```

### Check AWS credentials
```bash
cat .env
python3 -c "from config_aws import setup_aws_credentials; setup_aws_credentials()"
```

### Check S3 access
```bash
python3 s3_faiss_manager.py check stock-bot-algoseek
```

### View full logs
```bash
sudo journalctl -u stock-bot --since "1 hour ago"
```

---

## Cost Estimate

### t3.medium instance
- **Hourly**: $0.0416/hour
- **Monthly** (24/7): ~$30/month
- **Daily** (8 hours): ~$1/month

### Data Transfer
- S3 download (first time): ~$0.01
- Outbound traffic: ~$0.09/GB

### Nova Pro API
- Per query: ~$0.01
- 100 queries/day: ~$30/month

**Total**: ~$60-70/month for 24/7 operation

---

## Security Recommendations

### 1. Restrict IP Access

Instead of allowing 0.0.0.0/0, allow only your IP:

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 8501 \
  --cidr YOUR_IP/32
```

### 2. Use IAM Roles

Instead of hardcoding AWS credentials, attach an IAM role to the EC2 instance:

```bash
# Create role with Bedrock + S3 permissions
# Attach to instance
# Remove credentials from .env
```

### 3. Use HTTPS

Set up nginx with SSL:

```bash
sudo yum install -y nginx
# Configure reverse proxy with SSL
```

### 4. Enable CloudWatch Monitoring

```bash
# Install CloudWatch agent
sudo yum install -y amazon-cloudwatch-agent
```

---

## Sharing Your Bot

Once deployed, share this message:

```
Check out my Stock Bot!

URL: http://YOUR_IP:8501

Features:
- AI-powered stock analysis
- 8,987 stocks in knowledge base
- Real-time market data
- Powered by AWS Nova Pro

Try asking:
"What are the top tech stocks?"
"Tell me about AAPL"
"Compare GOOGL and MSFT"
```

---

## Stopping/Starting Instance

### Stop (to save costs when not in use)
```bash
aws ec2 stop-instances --instance-ids i-xxx --region us-east-1
```

Your IP will change when you restart!

### Start
```bash
aws ec2 start-instances --instance-ids i-xxx --region us-east-1

# Get new IP
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### Terminate (delete completely)
```bash
aws ec2 terminate-instances --instance-ids i-xxx --region us-east-1
```

---

## Advantages Over Docker

✅ Simpler deployment  
✅ Faster startup time  
✅ Less memory usage  
✅ Easier to debug  
✅ Direct log access  
✅ Systemd auto-restart  

---

## Next Steps

After deployment:

1. **Test the bot**: Open the URL and ask some questions
2. **Check logs**: Make sure there are no errors
3. **Monitor costs**: Set up AWS billing alerts
4. **Secure it**: Restrict IP access if needed
5. **Share**: Give the URL to your team/clients

---

**Ready to Deploy!** 🚀

Just run:
```bash
./deploy_ec2_simple.sh
```

Get your shareable URL in 10 minutes!

