# Start using Docker Compose (recommended)

docker-compose up -d

# Or start manually

docker run -d --name stock-bot
  -p 8501:8501
  -p 5001:5001
  -v $(pwd)/data:/app/data
  -v $(pwd)/logs:/app/logs
  -v $(pwd)/indices:/app/indices
  stock-bot


# Stop using Docker Compose

docker-compose down

# Or stop manually

docker stop stock-bot
docker rm stock-bot



# Check running containers

docker ps

# Check logs

docker logs stock-bot

# Check container status

docker stats stock-bot



# Force rebuild (ignores cache)

docker build --no-cache -t stock-bot .

# Or rebuild with a new tag

docker build -t stock-bot:latest .

# Remove old image and rebuild

docker rmi stock-bot
docker build -t stock-bot .


# Build and start everything

./build_docker.sh && docker-compose up -d

# Stop everything

docker-compose down

# View logs

docker-compose logs -f
