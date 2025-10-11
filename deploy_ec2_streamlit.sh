#!/usr/bin/env bash

set -euo pipefail

# Simple EC2 deploy script for the Stock Bot Streamlit app
#
# Usage:
#   ./deploy_ec2_streamlit.sh \
#     --host ec2-xx-xx-xx-xx.compute-1.amazonaws.com \
#     --user ubuntu \
#     --key /path/to/key.pem \
#     --repo https://github.com/Sarveshsh8/stock-bot.git \
#     --branch main \
#     --env-file .env \
#     --port 8501 \
#     [--setup-nginx] [--server-name stockbot.example.com]
#
# Notes:
# - Opens the app at http://<host>:<port> by default.
# - If --setup-nginx and --server-name are provided, configures Nginx reverse proxy on port 80
#   so the app is reachable at http://<server-name> (remember to point DNS A/AAAA to the EC2 public IP).

HOST=""
USER="ubuntu"
KEY=""
REPO="https://github.com/Sarveshsh8/stock-bot.git"
BRANCH="main"
ENV_FILE=".env"
PORT="8501"
SETUP_NGINX="false"
SERVER_NAME=""
APP_DIR="~/stock-bot"
VENV_DIR="~/sb-venv312"
PYTHON_VERSION="3.12"

# Optional AWS provisioning
CREATE_INSTANCE="false"
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.small"
AMI_ID="" # if empty we try to resolve Ubuntu 22.04 latest via SSM
KEY_NAME=""  # existing AWS key pair name (required when creating instance unless --import-key)
IMPORT_KEY_FILE_PUB=""  # a local .pub file to import as AWS key pair (sets KEY_NAME automatically)
SG_NAME="stock-bot-sg"

# Repo authentication / alternative local upload
GIT_TOKEN=""
LOCAL_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2;;
    --user) USER="$2"; shift 2;;
    --key) KEY="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --env-file) ENV_FILE="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --setup-nginx) SETUP_NGINX="true"; shift 1;;
    --server-name) SERVER_NAME="$2"; shift 2;;
    --python) PYTHON_VERSION="$2"; shift 2;;
    --create-instance) CREATE_INSTANCE="true"; shift 1;;
    --aws-region) AWS_REGION="$2"; shift 2;;
    --instance-type) INSTANCE_TYPE="$2"; shift 2;;
    --ami-id) AMI_ID="$2"; shift 2;;
    --key-name) KEY_NAME="$2"; shift 2;;
    --import-key) IMPORT_KEY_FILE_PUB="$2"; shift 2;;
    --sg-name) SG_NAME="$2"; shift 2;;
    --git-token) GIT_TOKEN="$2"; shift 2;;
    --local-path) LOCAL_PATH="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ "$CREATE_INSTANCE" == "false" ]]; then
  if [[ -z "$HOST" || -z "$KEY" ]]; then
    echo "Required: --host and --key (or use --create-instance with AWS CLI configured)"
    exit 1
  fi
fi

SSH=(ssh -o StrictHostKeyChecking=no -i "$KEY" "$USER@$HOST")
SCP=(scp -o StrictHostKeyChecking=no -i "$KEY")

if [[ "$CREATE_INSTANCE" == "true" ]]; then
  echo "[0/6] Provisioning EC2 instance in $AWS_REGION (Ubuntu 22.04, Python $PYTHON_VERSION) ..."
  if ! command -v aws >/dev/null 2>&1; then
    echo "AWS CLI not found. Install and configure it first (aws configure)."; exit 1
  fi
  # Resolve AMI if not provided
  if [[ -z "$AMI_ID" ]]; then
    AMI_ID=$(aws ssm get-parameters --names "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id" --region "$AWS_REGION" --query 'Parameters[0].Value' --output text)
  fi
  # Import key pair if requested
  if [[ -n "$IMPORT_KEY_FILE_PUB" ]]; then
    KEY_NAME="stock-bot-key-$(date +%s)"
    aws ec2 import-key-pair --region "$AWS_REGION" --key-name "$KEY_NAME" --public-key-material "$(cat "$IMPORT_KEY_FILE_PUB" | base64)" >/dev/null
    echo "  Imported key pair: $KEY_NAME"
  fi
  if [[ -z "$KEY_NAME" ]]; then
    echo "Provide --key-name <aws key pair> or --import-key /path/to/id_rsa.pub when using --create-instance."; exit 1
  fi
  # Create or find security group
  SG_ID=$(aws ec2 describe-security-groups --region "$AWS_REGION" --group-names "$SG_NAME" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || true)
  if [[ "$SG_ID" == "None" || -z "$SG_ID" ]]; then
    SG_ID=$(aws ec2 create-security-group --region "$AWS_REGION" --group-name "$SG_NAME" --description "Stock Bot SG" --query 'GroupId' --output text)
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --ip-permissions \
      IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description="SSH"}]' \
      IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges='[{CidrIp=0.0.0.0/0,Description="HTTP"}]' \
      IpProtocol=tcp,FromPort=$PORT,ToPort=$PORT,IpRanges='[{CidrIp=0.0.0.0/0,Description="Streamlit"}]' >/dev/null
  fi
  # Launch instance
  INSTANCE_ID=$(aws ec2 run-instances --region "$AWS_REGION" --image-id "$AMI_ID" --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" --security-group-ids "$SG_ID" --query 'Instances[0].InstanceId' --output text)
  echo "  Instance ID: $INSTANCE_ID (waiting for running state)"
  aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"
  HOST=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicDnsName' --output text)
  echo "  Public DNS: $HOST"
  USER="ubuntu"
  # Expect that the local private key corresponding to KEY_NAME is available in --key
  if [[ -z "$KEY" ]]; then
    echo "Provide --key /path/to/private-key.pem for SSH to the new instance."; exit 1
  fi
  SSH=(ssh -o StrictHostKeyChecking=no -i "$KEY" "$USER@$HOST")
  SCP=(scp -o StrictHostKeyChecking=no -i "$KEY")
fi

echo "[1/6] Preparing instance packages..."
"${SSH[@]}" "set -e; sudo apt-get update -y; sudo apt-get install -y software-properties-common git curl nginx; \
  sudo add-apt-repository ppa:deadsnakes/ppa -y || true; sudo apt-get update -y; \
  sudo apt-get install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python3-pip"

echo "[2/6] Creating directories and fetching code..."
"${SSH[@]}" "set -e; mkdir -p $APP_DIR"

if [[ -n "$LOCAL_PATH" ]]; then
  echo "  Uploading local source from $LOCAL_PATH ..."
  TMP_TAR=$(mktemp /tmp/stockbot-src-XXXXXX.tgz)
  # Exclude large/unnecessary files from upload to accelerate deployment
  tar -czf "$TMP_TAR" \
    --exclude='.git' \
    --exclude='*.zip' \
    --exclude='*.tar.gz' \
    --exclude='*.tgz' \
    --exclude='*.csv' \
    --exclude='faiss_index*' \
    --exclude='stock_dataset' \
    --exclude='node_modules' \
    --exclude='.venv*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    -C "$LOCAL_PATH" .
  "${SCP[@]}" "$TMP_TAR" "$USER@$HOST:$APP_DIR/repo.tgz"
  rm -f "$TMP_TAR"
  "${SSH[@]}" "set -e; mkdir -p $APP_DIR/repo; tar -xzf $APP_DIR/repo.tgz -C $APP_DIR/repo; rm -f $APP_DIR/repo.tgz"
else
  REPO_URL="$REPO"
  if [[ -n "$GIT_TOKEN" && "$REPO" == https://* ]]; then
    REPO_URL="https://$GIT_TOKEN@${REPO#https://}"
  fi
  "${SSH[@]}" "set -e; cd $APP_DIR; if [ ! -d repo/.git ]; then git clone '$REPO_URL' repo; fi; cd repo; git fetch --all || true; git checkout '$BRANCH' || true; git pull --ff-only origin '$BRANCH' || true"
fi

echo "[3/6] Uploading .env (if present locally)..."
if [[ -f "$ENV_FILE" ]]; then
  "${SCP[@]}" "$ENV_FILE" "$USER@$HOST:$APP_DIR/repo/.env"
else
  echo "  Skipping .env upload (file not found: $ENV_FILE)"
fi

echo "[4/6] Creating Python venv and installing requirements..."
"${SSH[@]}" "set -e; python$PYTHON_VERSION -m venv $VENV_DIR; source $VENV_DIR/bin/activate; python -m pip install --upgrade pip; cd $APP_DIR/repo; if [ -f requirements_aws.txt ]; then pip install -r requirements_aws.txt; else pip install -r requirements.txt; fi"

echo "[5/6] Launching Streamlit app on port $PORT..."
"${SSH[@]}" "set -e; sudo fuser -k $PORT/tcp || true; cd $APP_DIR/repo; source $VENV_DIR/bin/activate; nohup streamlit run app_aws_deployment.py --server.port $PORT --server.address 0.0.0.0 > $APP_DIR/streamlit.out 2>&1 & echo \$! > $APP_DIR/streamlit.pid"

if [[ "$SETUP_NGINX" == "true" ]]; then
  if [[ -z "$SERVER_NAME" ]]; then
    echo "--setup-nginx requires --server-name <domain>"
    exit 1
  fi
  echo "[6/6] Configuring Nginx reverse proxy for $SERVER_NAME -> localhost:$PORT"
  NGINX_CONF="/etc/nginx/sites-available/stock-bot.conf"
  "${SSH[@]}" "set -e; echo 'server {\n    listen 80;\n    server_name $SERVER_NAME;\n    location / {\n        proxy_pass http://127.0.0.1:$PORT;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto \$scheme;\n    }\n}' | sudo tee $NGINX_CONF > /dev/null; sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/stock-bot.conf; sudo nginx -t; sudo systemctl restart nginx"
else
  echo "[6/6] Nginx not requested; app will be available on the Streamlit port."
fi

PUBLIC_URL="http://$HOST:$PORT"
if [[ "$SETUP_NGINX" == "true" ]]; then
  PUBLIC_URL="http://$SERVER_NAME"
fi

echo "\nDeployment complete."
echo "URL: $PUBLIC_URL"
echo "Logs: ssh -i $KEY $USER@$HOST 'tail -f $APP_DIR/streamlit.out'"
echo "Stop app: ssh -i $KEY $USER@$HOST 'kill \$(cat $APP_DIR/streamlit.pid) || true'"
echo "Restart app: rerun this script."


