# Stock Bot V3 - Complete Deployment Guide

##  Deployment Scenarios

This guide covers two main deployment scenarios:

1. **Frontend + Backend Deployment** - Streamlit web interface with backend services
2. **Jupyter Notebook on EKS** - Interactive notebook environment in Kubernetes

##  Prerequisites

- **Kubernetes Cluster** (EKS recommended)
- **kubectl** configured and connected to your cluster
- **Docker** for building images
- **AWS Credentials** configured (for S3 and Bedrock)

##  Scenario 1: Frontend + Backend Deployment

### What This Deploys:
- **Streamlit Web Interface** (Port 8501)
- **Flask Backend API** (Port 5000)
- **LoadBalancer Service** for external access
- **Persistent Storage** for data
- **Health Checks** and monitoring

### Deployment Steps:

```bash
# 1. Build and deploy
./deploy-complete.sh
# Select option 1: Frontend + Backend only

# 2. Check status
./control-complete.sh status

# 3. Get service URLs
./control-complete.sh urls

# 4. Access the application
# Frontend: http://[EXTERNAL-IP]
# Backend API: http://[EXTERNAL-IP]:5000
```

### Features Available:
-  Interactive web dashboard
-  File upload interface
-  Data pipeline controls
-  Q&A system
-  Real-time monitoring

##  Scenario 2: Jupyter Notebook on EKS

### What This Deploys:
- **Jupyter Notebook Server** (Port 8888)
- **Persistent Storage** for notebooks and data
- **LoadBalancer Service** for external access
- **Full Stock Bot V3 Environment**

### Deployment Steps:

```bash
# 1. Build and deploy
./deploy-complete.sh
# Select option 2: Jupyter Notebook only

# 2. Check status
./control-complete.sh jupyter

# 3. Get service URL
./control-complete.sh urls

# 4. Access Jupyter
# Jupyter: http://[EXTERNAL-IP]
```

### Features Available:
-  Interactive notebook environment
-  All Stock Bot V3 modules available
-  Persistent notebook storage
-  Full development environment
-  Direct access to all components

##  Scenario 3: Complete System

### What This Deploys:
- **Both Frontend/Backend AND Jupyter**
- **Shared persistent storage**
- **Multiple LoadBalancer services**
- **Full production environment**

### Deployment Steps:

```bash
# 1. Build and deploy everything
./deploy-complete.sh
# Select option 3: Complete system

# 2. Check all services
./control-complete.sh status

# 3. Get all URLs
./control-complete.sh urls
```

##  Management Commands

### Control Script Usage:

```bash
# Check status of all deployments
./control-complete.sh status

# View logs from all services
./control-complete.sh logs

# Get service URLs
./control-complete.sh urls

# Restart all deployments
./control-complete.sh restart

# Stop all deployments
./control-complete.sh stop

# Start all deployments
./control-complete.sh start

# Clean up all resources
./control-complete.sh clean

# Check specific service
./control-complete.sh frontend
./control-complete.sh jupyter
```

##  Configuration

### Before Deployment:

1. **Update AWS Secrets** in `k8s/secrets.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-secrets
  namespace: stock-bot-v3
type: Opaque
data:
  aws-access-key-id: <base64-encoded-access-key>
  aws-secret-access-key: <base64-encoded-secret-key>
  s3-bucket-name: <base64-encoded-bucket-name>
```

2. **Update Configuration** in `config.yaml`:
```yaml
# Add your ETFs and stocks
etfs:
  - symbol: "SPY"
    name: "SPDR S&P 500 ETF Trust"
    category: "US Large Cap"

stocks:
  - symbol: "AAPL"
    name: "Apple Inc."
    category: "Technology"
```

##  Monitoring and Troubleshooting

### Check Pod Status:
```bash
kubectl get pods -n stock-bot-v3
```

### View Logs:
```bash
# Frontend/Backend logs
kubectl logs -f deployment/stock-bot-v3 -n stock-bot-v3

# Jupyter logs
kubectl logs -f deployment/stock-bot-v3-jupyter -n stock-bot-v3
```

### Check Services:
```bash
kubectl get services -n stock-bot-v3
```

### Access Pod Shell:
```bash
# Frontend/Backend pod
kubectl exec -it deployment/stock-bot-v3 -n stock-bot-v3 -- /bin/bash

# Jupyter pod
kubectl exec -it deployment/stock-bot-v3-jupyter -n stock-bot-v3 -- /bin/bash
```

##  Access URLs

After deployment, you'll get URLs like:

### Frontend + Backend:
- **Streamlit Interface**: `http://[EXTERNAL-IP]`
- **Flask API**: `http://[EXTERNAL-IP]:5000`

### Jupyter Notebook:
- **Jupyter Interface**: `http://[EXTERNAL-IP]`

### Complete System:
- **Streamlit**: `http://[EXTERNAL-IP]`
- **Jupyter**: `http://[EXTERNAL-IP]` (different port)
- **API**: `http://[EXTERNAL-IP]:5000`

##  Security Notes

- **AWS Credentials** are stored as Kubernetes secrets
- **LoadBalancer** services expose ports to the internet
- **Persistent volumes** maintain data across restarts
- **Health checks** ensure service availability

##  Quick Start

```bash
# 1. Clone and navigate to project
cd stock-bot-v3

# 2. Update secrets and config
# Edit k8s/secrets.yaml with your AWS credentials
# Edit config.yaml with your ETFs/stocks

# 3. Deploy complete system
./deploy-complete.sh
# Select option 3

# 4. Wait for deployment and get URLs
./control-complete.sh urls

# 5. Access your services!
```

##  Support

For issues or questions:
1. Check pod logs: `./control-complete.sh logs`
2. Verify configuration: `./control-complete.sh status`
3. Restart if needed: `./control-complete.sh restart`
4. Clean and redeploy: `./control-complete.sh clean`
