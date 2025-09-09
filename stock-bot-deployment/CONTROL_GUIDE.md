# Stock Bot V3 - Control Guide

This guide explains how to start, stop, and manage your Stock Bot V3 services on AWS EKS.

## Quick Start

The `control.sh` script provides easy management of your deployed services.

### Basic Commands

```bash
# Start all services
./control.sh start

# Stop all services  
./control.sh stop

# Restart all services
./control.sh restart

# Check service status
./control.sh status

# Get service URLs
./control.sh urls

# View logs
./control.sh logs main      # Main app logs
./control.sh logs jupyter   # Jupyter logs

# Clean up everything
./control.sh clean

# Show help
./control.sh help
```

## Service URLs

After starting services, you can access:

- **Streamlit Web App**: `http://[LOADBALANCER-IP]`
- **Flask API**: `http://[LOADBALANCER-IP]:5000`  
- **Jupyter Notebook**: `http://[JUPYTER-LOADBALANCER-IP]`

Use `./control.sh urls` to get the current URLs.

## What Each Service Does

### Main Application (Streamlit + Flask)
- **Streamlit**: Web interface for data analysis and Q&A
- **Flask API**: REST API endpoints for programmatic access
- **Features**: Yahoo Finance data fetching, file upload, AI analysis, FAISS search

### Jupyter Notebook
- **Purpose**: Interactive development and data analysis
- **Features**: Access to all Stock Bot V3 modules, data exploration, custom analysis

## Resource Management

### Starting Services
```bash
./control.sh start
```
- Scales up deployments to running state
- Waits for services to be ready
- Shows URLs when complete

### Stopping Services
```bash
./control.sh stop
```
- Scales down deployments to 0 replicas
- Stops all pods but preserves data
- Services can be restarted later

### Restarting Services
```bash
./control.sh restart
```
- Stops all services
- Waits 5 seconds
- Starts all services again

## Monitoring

### Check Status
```bash
./control.sh status
```
Shows:
- Pod status and health
- Service endpoints
- Deployment status

### View Logs
```bash
# Main application logs
./control.sh logs main

# Jupyter notebook logs  
./control.sh logs jupyter
```

## Cost Management

### Stop When Not Using
```bash
./control.sh stop
```
- Stops all pods (saves compute costs)
- Preserves data and configuration
- Easy to restart later

### Start When Needed
```bash
./control.sh start
```
- Restarts all services
- Takes 1-2 minutes to be ready
- All data and settings preserved

## Troubleshooting

### Services Won't Start
1. Check AWS credentials: `aws sts get-caller-identity`
2. Check kubectl connection: `kubectl get nodes`
3. Check namespace: `kubectl get namespace stock-bot-v3`

### Pod Issues
1. Check pod status: `./control.sh status`
2. Check pod logs: `./control.sh logs main` or `./control.sh logs jupyter`
3. Check pod events: `kubectl describe pod [POD-NAME] -n stock-bot-v3`

### Access Issues
1. Get current URLs: `./control.sh urls`
2. Test connectivity: `curl -I [URL]`
3. Check LoadBalancer status: `kubectl get service -n stock-bot-v3`

## Cleanup

### Remove Everything
```bash
./control.sh clean
```
**Warning**: This permanently deletes all resources including data!

### What Gets Deleted
- All deployments and pods
- All services and LoadBalancers
- All persistent volumes and data
- All secrets and configurations

## Examples

### Daily Workflow
```bash
# Start services in the morning
./control.sh start

# Check status
./control.sh status

# Get URLs
./control.sh urls

# Stop services at end of day
./control.sh stop
```

### Development Workflow
```bash
# Start services
./control.sh start

# Work with Jupyter notebook
# Access: http://[JUPYTER-URL]

# Test web interface
# Access: http://[MAIN-URL]

# Check logs if issues
./control.sh logs main

# Restart if needed
./control.sh restart
```

### Troubleshooting Workflow
```bash
# Check what's running
./control.sh status

# Check logs for errors
./control.sh logs main
./control.sh logs jupyter

# Restart services
./control.sh restart

# If still issues, check pod details
kubectl describe pod [POD-NAME] -n stock-bot-v3
```

## Notes

- Services take 1-2 minutes to start up
- Data is preserved when stopping/starting
- LoadBalancer URLs may change if services are recreated
- Use `./control.sh urls` to get current URLs
- Stop services when not in use to save costs
