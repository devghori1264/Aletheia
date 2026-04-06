# Deployment Guide

This guide covers deploying Aletheia in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployments](#cloud-deployments)
6. [Configuration Reference](#configuration-reference)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| CPU | 4 cores | 8 cores | 16+ cores |
| RAM | 8 GB | 16 GB | 32+ GB |
| GPU | - | NVIDIA GTX 1080 | NVIDIA A100 |
| Storage | 50 GB SSD | 200 GB SSD | 500+ GB NVMe |

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- NVIDIA Driver 535+ (for GPU support)
- NVIDIA Container Toolkit (for GPU support)

---

## Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/devghori1264/aletheia.git
cd aletheia
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit .env with your settings
nano .env
```

**Essential .env settings:**

```bash
# Security (REQUIRED - change these!)
SECRET_KEY=your-generated-secret-key
ALETHEIA_ENVIRONMENT=production
DJANGO_DEBUG=false

# Database
DATABASE_URL=postgres://aletheia:password@postgres:5432/aletheia

# Redis
REDIS_URL=redis://redis:6379/0

# File storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=aletheia-media

# ML Settings
ML_DEVICE=cuda  # or 'cpu'
ML_PRECISION=fp16
```

### 3. Launch Services

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Check health
curl http://localhost:8000/api/v1/health/
```

### 4. Initialize Database

```bash
# Run migrations
docker compose exec api python manage.py migrate

# Create superuser
docker compose exec api python manage.py createsuperuser

# Load initial data (optional)
docker compose exec api python manage.py loaddata initial_data
```

### 5. Access Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| Flower (Celery monitoring) | http://localhost:5555 |
| API Docs | http://localhost:8000/api/docs |

---

## Production Deployment

### Security Hardening

1. **TLS/SSL Configuration**

```bash
# Generate certificates (use Let's Encrypt for production)
certbot certonly --standalone -d api.aletheia.io
```

2. **Nginx Reverse Proxy**

```nginx
# /etc/nginx/sites-available/aletheia
server {
    listen 80;
    server_name api.aletheia.io;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.aletheia.io;

    ssl_certificate /etc/letsencrypt/live/api.aletheia.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.aletheia.io/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # File upload size
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/aletheia/static/;
    }

    location /media/ {
        alias /var/www/aletheia/media/;
    }
}
```

3. **Firewall Rules**

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable
```

### Database Configuration

**PostgreSQL optimization for production:**

```sql
-- /etc/postgresql/16/main/postgresql.conf

# Memory
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

# Connections
max_connections = 200

# WAL
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB

# Query planning
random_page_cost = 1.1
effective_io_concurrency = 200
```

**Connection pooling with PgBouncer:**

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
aletheia = host=localhost port=5432 dbname=aletheia

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 50
```

### Scaling Workers

```bash
# Scale Celery workers
docker compose up -d --scale worker=4

# Or with docker swarm
docker stack deploy -c docker-compose.prod.yml aletheia
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3.x
- NVIDIA GPU Operator (for GPU nodes)

### 1. Create Namespace

```bash
kubectl create namespace aletheia
```

### 2. Configure Secrets

```bash
# Create secrets
kubectl create secret generic aletheia-secrets \
  --namespace aletheia \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=DATABASE_URL='postgres://user:pass@postgres:5432/aletheia' \
  --from-literal=REDIS_URL='redis://redis:6379/0'
```

### 3. Deploy with Helm

```bash
# Add Aletheia Helm chart
helm repo add aletheia https://charts.aletheia.io
helm repo update

# Install
helm install aletheia aletheia/aletheia \
  --namespace aletheia \
  --values values.yaml
```

**values.yaml:**

```yaml
# values.yaml
replicaCount:
  api: 3
  worker: 4

image:
  repository: ghcr.io/your-org/aletheia
  tag: "1.0.0"

resources:
  api:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "2"
      memory: "4Gi"
  
  worker:
    requests:
      cpu: "2"
      memory: "8Gi"
      nvidia.com/gpu: "1"
    limits:
      cpu: "4"
      memory: "16Gi"
      nvidia.com/gpu: "1"

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.aletheia.io
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: aletheia-tls
      hosts:
        - api.aletheia.io

postgresql:
  enabled: true
  auth:
    postgresPassword: "your-password"
    database: aletheia

redis:
  enabled: true
  architecture: standalone

persistence:
  enabled: true
  storageClass: "gp3"
  size: 100Gi
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n aletheia

# Check services
kubectl get svc -n aletheia

# View logs
kubectl logs -f deployment/aletheia-api -n aletheia
```

### GPU Node Configuration

```yaml
# gpu-node-pool.yaml
apiVersion: v1
kind: Node
metadata:
  labels:
    accelerator: nvidia-tesla-a100
spec:
  taints:
    - key: nvidia.com/gpu
      value: "true"
      effect: NoSchedule
```

---

## Cloud Deployments

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster \
  --name aletheia \
  --region us-west-2 \
  --node-type p3.2xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10

# Install NVIDIA plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Deploy Aletheia
helm install aletheia aletheia/aletheia -f values-aws.yaml
```

### Google Cloud GKE

```bash
# Create GKE cluster with GPU nodes
gcloud container clusters create aletheia \
  --zone us-central1-a \
  --accelerator type=nvidia-tesla-a100,count=1 \
  --machine-type n1-standard-8

# Install NVIDIA drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

# Deploy Aletheia
helm install aletheia aletheia/aletheia -f values-gcp.yaml
```

### Azure AKS

```bash
# Create AKS cluster
az aks create \
  --resource-group aletheia-rg \
  --name aletheia-cluster \
  --node-vm-size Standard_NC6 \
  --node-count 3

# Deploy Aletheia
helm install aletheia aletheia/aletheia -f values-azure.yaml
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALETHEIA_ENVIRONMENT` | Environment (development/production/testing) | development |
| `SECRET_KEY` | Django secret key | REQUIRED |
| `DJANGO_DEBUG` | Debug mode | false |
| `DATABASE_URL` | PostgreSQL connection URL | REQUIRED |
| `REDIS_URL` | Redis connection URL | REQUIRED |
| `ML_DEVICE` | ML device (cuda/cpu) | cuda |
| `ML_PRECISION` | Model precision (fp16/fp32) | fp16 |
| `ML_BATCH_SIZE` | Inference batch size | 8 |
| `CELERY_CONCURRENCY` | Worker concurrency | 4 |
| `MAX_UPLOAD_SIZE_MB` | Max upload size | 500 |
| `LOG_LEVEL` | Logging level | INFO |
| `SENTRY_DSN` | Sentry error tracking DSN | - |
| `CORS_ALLOWED_ORIGINS` | CORS origins (comma-separated) | * |

### Resource Limits

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| API | 500m | 2 | 1Gi | 4Gi |
| Worker (CPU) | 1 | 4 | 4Gi | 8Gi |
| Worker (GPU) | 2 | 4 | 8Gi | 16Gi |
| Redis | 100m | 500m | 256Mi | 1Gi |
| PostgreSQL | 500m | 2 | 1Gi | 4Gi |

---

## Troubleshooting

### Common Issues

#### 1. GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check container toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Verify CUDA in container
docker compose exec worker python -c "import torch; print(torch.cuda.is_available())"
```

#### 2. Out of Memory Errors

```bash
# Reduce batch size
export ML_BATCH_SIZE=4

# Enable FP16
export ML_PRECISION=fp16

# Restart workers
docker compose restart worker
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec api python manage.py dbshell

# Check connection pool
docker compose exec api python -c "from django.db import connection; print(connection.ensure_connection())"
```

#### 4. Celery Tasks Not Running

```bash
# Check worker status
docker compose exec worker celery -A aletheia inspect active

# Check queue
docker compose exec worker celery -A aletheia inspect reserved

# Purge stuck tasks
docker compose exec worker celery -A aletheia purge
```

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health/

# Database health
docker compose exec postgres pg_isready

# Redis health
docker compose exec redis redis-cli ping

# Worker health
docker compose exec worker celery -A aletheia inspect ping
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# With timestamps
docker compose logs -f --timestamps

# Last 100 lines
docker compose logs --tail=100 worker
```

---

## Backup and Recovery

### Database Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U aletheia aletheia > backup.sql

# Automated backup (cron)
0 0 * * * docker compose exec -T postgres pg_dump -U aletheia aletheia | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz
```

### Database Restore

```bash
# Restore from backup
docker compose exec -T postgres psql -U aletheia aletheia < backup.sql
```

### Media Files Backup

```bash
# Sync to S3
aws s3 sync ./media s3://aletheia-backups/media/

# Restore from S3
aws s3 sync s3://aletheia-backups/media/ ./media
```

---

## Monitoring Setup

### Prometheus Metrics

Add to docker-compose.yml:

```yaml
prometheus:
  image: prom/prometheus:v2.47.0
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### Grafana Dashboards

```yaml
grafana:
  image: grafana/grafana:10.1.0
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana-data:/var/lib/grafana
```

Import the Aletheia dashboard from `docs/monitoring/grafana-dashboard.json`.
