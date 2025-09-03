# Stock-Bot Docker Deployment Guide

## 🐳 **Overview**

This guide covers how to containerize and deploy the Stock-Bot application using Docker. The application includes both a Streamlit web interface and a Flask API for financial data analysis.

## 📋 **Prerequisites**

- Docker Desktop installed and running
- Python 3.11+ (for local development)
- AWS credentials configured (for S3 access)
- At least 2GB of available RAM

## 🏗️ **Docker Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock-Bot Container                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   Streamlit     │    │   Flask API     │               │
│  │   (Port 8501)   │    │   (Port 5001)   │               │
│  └─────────────────┘    └─────────────────┘               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   FAISS Index   │    │   Nova Pro      │               │
│  │   Builder       │    │   Client        │               │
│  └─────────────────┘    └─────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start**

### 1. **Build and Test Docker Image**

```bash
# Make script executable (if not already)
chmod +x build_docker.sh

# Build and test the Docker image
./build_docker.sh
```

This script will:
- Check if Docker is running
- Clean up previous builds
- Build the Docker image
- Start a test container
- Verify both services are healthy

### 2. **Using Docker Compose**

```bash
# Start services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. **Manual Docker Commands**

```bash
# Build image
docker build -t stock-bot:latest .

# Run container
docker run -d \
  --name stock-bot \
  -p 8501:8501 \
  -p 5001:5001 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/indices:/app/indices \
  -v $(pwd)/logs:/app/logs \
  stock-bot:latest

# View logs
docker logs -f stock-bot

# Stop container
docker stop stock-bot
docker rm stock-bot
```

## ⚙️ **Configuration**

### Environment Variables

Create a `.env` file in the project root:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=your_bucket_name_here

# Optional: Custom ports
STREAMLIT_SERVER_PORT=8501
FLASK_PORT=5001
```

### Volume Mounts

The container uses the following volume mounts:

- `./data:/app/data` - Financial data files
- `./indices:/app/indices` - FAISS index files
- `./logs:/app/logs` - Application logs

## 🔍 **Health Checks**

### Streamlit Health Check
```bash
curl http://localhost:8501/_stcore/health
```

### Flask API Health Check
```bash
curl http://localhost:5001/
```

## 📊 **Monitoring**

### Container Status
```bash
# Check container status
docker ps

# View resource usage
docker stats stock-bot

# View container logs
docker logs -f stock-bot
```

### Service Logs
```bash
# Streamlit logs
tail -f logs/streamlit.log

# Flask logs
tail -f logs/flask.log
```

## 🛠️ **Troubleshooting**

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the ports
   lsof -i :8501
   lsof -i :5001
   
   # Kill processes if needed
   sudo kill -9 <PID>
   ```

2. **Container Won't Start**
   ```bash
   # Check container logs
   docker logs stock-bot
   
   # Check if .env file exists
   ls -la .env
   ```

3. **Services Not Responding**
   ```bash
   # Check container health
   docker exec stock-bot curl -f http://localhost:8501/_stcore/health
   
   # Restart container
   docker restart stock-bot
   ```

4. **Memory Issues**
   ```bash
   # Check container resource usage
   docker stats stock-bot
   
   # Increase Docker memory limit in Docker Desktop
   ```

### Debug Mode

Run container in interactive mode for debugging:

```bash
docker run -it \
  --name stock-bot-debug \
  -p 8501:8501 \
  -p 5001:5001 \
  --env-file .env \
  stock-bot:latest /bin/bash
```

## 📁 **File Structure**

```
Stock-Bot/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose configuration
├── .dockerignore             # Files to exclude from build
├── start_docker.py           # Container startup script
├── build_docker.sh           # Build and test script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── data/                     # Financial data (mounted)
├── indices/                  # FAISS indices (mounted)
├── logs/                     # Application logs (mounted)
└── src/                      # Application source code
```

## 🔒 **Security Considerations**

- Container runs as non-root user (`appuser`)
- Environment variables are loaded from `.env` file
- Sensitive data should not be baked into the image
- Use Docker secrets for production deployments

## 📈 **Performance Optimization**

- Multi-stage builds for smaller images
- Layer caching for faster builds
- Health checks for better monitoring
- Resource limits to prevent resource exhaustion

## 🚀 **Next Steps**

After successful Docker deployment:

1. **Test all functionality** - Ensure both Streamlit and Flask work
2. **Load test** - Test with multiple concurrent users
3. **Monitor performance** - Track resource usage and response times
4. **Prepare for EKS** - When ready, use the k8s/ manifests for EKS deployment

## 📞 **Support**

If you encounter issues:

1. Check the troubleshooting section above
2. Review container logs: `docker logs stock-bot`
3. Verify environment configuration
4. Ensure all required files are present

---

**Happy Containerizing! 🐳**
