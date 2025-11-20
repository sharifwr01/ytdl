# 🚀 Deployment Guide

এই guide আপনাকে production environment এ bot deploy করতে সাহায্য করবে।

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [VPS Setup](#vps-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Backup Strategy](#backup-strategy)
- [Security Hardening](#security-hardening)

## Prerequisites

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 22.04 LTS (recommended)
- **Bandwidth**: 100Mbps

### Recommended Requirements
- **CPU**: 4 cores
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Bandwidth**: 1Gbps

## VPS Setup

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y curl wget git vim ufw

# Create user
sudo adduser botuser
sudo usermod -aG sudo botuser

# Switch to new user
su - botuser
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using webhook)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

## Docker Deployment

### 1. Clone Repository

```bash
# Create app directory
sudo mkdir -p /opt/yt-telegram-bot
sudo chown $USER:$USER /opt/yt-telegram-bot
cd /opt/yt-telegram-bot

# Clone repository
git clone https://github.com/yourusername/yt-telegram-bot.git .
```

### 2. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Essential Configuration:**
```env
# Telegram
TELEGRAM_TOKEN=your_actual_bot_token

# Database
DB_URL=postgresql+asyncpg://ytbot:your_strong_password@postgres:5432/ytbot
DB_PASSWORD=your_strong_password

# Redis
REDIS_URL=redis://redis:6379

# Limits
MAX_FILE_MB=50
RATE_LIMIT_PER_USER_PER_DAY=20

# Admin
ADMIN_USER_IDS=your_telegram_id

# Storage (choose one)
STORAGE_BACKEND=local  # or gdrive, s3
```

### 3. Start Services

```bash
# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f bot

# Check status
docker-compose ps
```

### 4. Setup SSL (for webhook mode)

```bash
# Install Certbot
sudo apt install -y certbot

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
sudo chown $USER:$USER ./ssl/*

# Enable webhook mode
docker-compose --profile webhook up -d
```

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client
```

### 2. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: yt-bot
```

```bash
kubectl apply -f namespace.yaml
```

### 3. Create Secrets

```bash
# Create secrets
kubectl create secret generic yt-bot-secrets \
  --from-literal=telegram-token=YOUR_TOKEN \
  --from-literal=db-password=YOUR_PASSWORD \
  -n yt-bot
```

### 4. Deploy Database

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: yt-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: ytbot
        - name: POSTGRES_USER
          value: ytbot
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: yt-bot-secrets
              key: db-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: yt-bot
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
```

### 5. Deploy Bot

```yaml
# bot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yt-bot
  namespace: yt-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: yt-bot
  template:
    metadata:
      labels:
        app: yt-bot
    spec:
      containers:
      - name: bot
        image: yourusername/yt-telegram-bot:latest
        env:
        - name: TELEGRAM_TOKEN
          valueFrom:
            secretKeyRef:
              name: yt-bot-secrets
              key: telegram-token
        - name: DB_URL
          value: postgresql+asyncpg://ytbot:$(DB_PASSWORD)@postgres:5432/ytbot
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

```bash
# Apply deployments
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f bot-deployment.yaml

# Check status
kubectl get pods -n yt-bot
kubectl logs -f deployment/yt-bot -n yt-bot
```

## Monitoring Setup

### 1. Prometheus + Grafana

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'yt-bot'
    static_configs:
      - targets: ['bot:8000']
```

### 2. Logging with ELK Stack

```yaml
# logging/docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

## Backup Strategy

### 1. Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker exec postgres pg_dump -U ytbot ytbot > "$BACKUP_DIR/backup_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### 2. Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/yt-telegram-bot/backup.sh
```

### 3. Restore from Backup

```bash
# Uncompress
gunzip backup_20240101_020000.sql.gz

# Restore
docker exec -i postgres psql -U ytbot ytbot < backup_20240101_020000.sql
```

## Security Hardening

### 1. SSH Security

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Disable root login
PermitRootLogin no

# Disable password authentication
PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### 2. Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Start service
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Docker Security

```bash
# Run as non-root user
USER botuser

# Read-only root filesystem
docker run --read-only ...

# Resource limits
docker run --memory="2g" --cpus="2" ...
```

## Maintenance

### 1. Update Bot

```bash
cd /opt/yt-telegram-bot

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

### 2. Clean Up

```bash
# Remove old images
docker image prune -a

# Remove old volumes
docker volume prune

# Clean tmp files
docker exec bot rm -rf /tmp/yt_bot/*
```

### 3. Monitor Resources

```bash
# Check disk usage
df -h

# Check memory
free -h

# Check Docker stats
docker stats

# Check logs size
du -sh /opt/yt-telegram-bot/logs
```

## Troubleshooting

### Bot Not Starting

```bash
# Check logs
docker-compose logs bot

# Check environment
docker-compose config

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose logs postgres

# Test connection
docker exec -it postgres psql -U ytbot -d ytbot

# Reset database
docker-compose down -v
docker-compose up -d
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Limit memory
# Edit docker-compose.yml
services:
  bot:
    deploy:
      resources:
        limits:
          memory: 2G

# Restart
docker-compose up -d
```

## Performance Optimization

### 1. Redis Configuration

```bash
# Edit redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 2. PostgreSQL Tuning

```sql
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
```

### 3. Worker Optimization

```env
# .env
MAX_CONCURRENT_DOWNLOADS=5
WORKER_COUNT=4
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  bot:
    deploy:
      replicas: 3
      
  # Load balancer
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
```

### Vertical Scaling

```bash
# Increase resources
docker-compose down
# Edit docker-compose.yml resources
docker-compose up -d
```

---

**Need Help?** Open an issue or contact support@example.com