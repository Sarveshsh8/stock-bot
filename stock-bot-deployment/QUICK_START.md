# Stock Bot V3 - Quick Start Guide

##  One-Command Deployment

### Deploy Everything
```bash
./deploy-all.sh
```

This single command will:
-  Check/create EKS cluster
-  Build Docker image
-  Push to ECR
-  Install EBS CSI driver
-  Deploy all Kubernetes resources
-  Show you the URLs

### Clean Up Everything
```bash
./cleanup-all.sh
```

This will give you options to:
- Stop services only (saves ~$15-20/day)
- Delete everything including cluster (saves ~$30-35/day)
- Delete cluster only (saves ~$14-15/day)
- Check current costs

### Quick Cluster Deletion
```bash
./delete-cluster.sh
```

This will immediately delete the EKS cluster with confirmation.

##  What You Get

After running `./deploy-all.sh`, you'll have:

###  **Frontend + Backend (Streamlit + Flask API)**
- **URL**: `http://[loadbalancer-url]`
- **Features**: Web UI, API endpoints, data processing

###  **Jupyter Notebook**
- **URL**: `http://[jupyter-loadbalancer-url]`
- **Features**: Interactive analysis, data exploration

##  Cost Management

### Current Daily Costs:
- **EKS Control Plane**: ~$14-15/day
- **LoadBalancers**: ~$3-4/day each (2 running)
- **EC2 Nodes**: ~$8-10/day
- **Total**: ~$30-35/day

### To Stop Charges:
```bash
# Stop services (keeps cluster)
./cleanup-all.sh
# Choose option 1

# Delete cluster only
./delete-cluster.sh

# Or delete everything
./cleanup-all.sh
# Choose option 2
```

##  Management Commands

```bash
# Check status
./control.sh status

# Get URLs
./control.sh urls

# View logs
./control.sh logs

# Stop services
./control.sh stop
```

##  File Structure

```
stock-bot-deployment/
 deploy-all.sh          #  Main deployment script
 delete-cluster.sh      #  Quick cluster deletion
 cleanup-all.sh         #  Comprehensive cleanup options
 control.sh             #  Management script
 create_cluster.py      #  Cluster creation (used by deploy-all.sh)
 k8s/                   #  Kubernetes manifests
 src/                   #  Application source code
 requirements.txt       #  Python dependencies
```

##  Quick Commands Summary

| Action | Command |
|--------|---------|
| **Deploy Everything** | `./deploy-all.sh` |
| **Clean Up (Options)** | `./cleanup-all.sh` |
| **Delete Cluster Only** | `./delete-cluster.sh` |
| **Check Status** | `./control.sh status` |
| **Get URLs** | `./control.sh urls` |
| **View Logs** | `./control.sh logs` |
| **Stop Services** | `./control.sh stop` |

##  Troubleshooting

### If deployment fails:
1. Check AWS credentials are set
2. Ensure Docker is running
3. Verify kubectl is installed
4. Check AWS console for any errors

### If pods are stuck:
```bash
kubectl get pods -n stock-bot-v3
kubectl describe pod [pod-name] -n stock-bot-v3
```

### If LoadBalancers don't get external IPs:
- Wait 2-3 minutes for AWS to provision them
- Check AWS console for LoadBalancer status

##  That's It!

Just run `./deploy-all.sh` and you'll have a fully functional Stock Bot V3 system running on AWS EKS!
