---
name: devops-expert
description: DevOps expert. Use when working with Docker, CI/CD, infrastructure, Kubernetes, or deployment automation.
---

# DevOps Expert

Expert in DevOps practices, containerization, CI/CD pipelines, and cloud infrastructure.

## When to Use This Skill

- Docker and containerization
- CI/CD pipeline configuration
- Kubernetes deployment
- Infrastructure as code
- Monitoring and observability
- Cloud platform configuration

## Docker Best Practices

### Dockerfile Optimization
```dockerfile
# Use multi-stage builds
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir --prefix=/install poetry && \
    poetry install --no-dev --only main

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "app.main:app"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: vinbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: vinbot_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vinbot"]
      interval: 10s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Docker Commands
```bash
# Build and run
docker build -t vinbot:latest .
docker run -d -p 8000:8000 --env-file .env vinbot:latest

# Logs and debugging
docker logs -f vinbot
docker exec -it vinbot sh
docker stats vinbot

# Cleanup
docker system prune -af
docker volume prune -f

# Multi-stage build
docker build --target builder -t vinbot:builder .
```

## Kubernetes (K8s)

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vinbot
  labels:
    app: vinbot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vinbot
  template:
    metadata:
      labels:
        app: vinbot
    spec:
      containers:
      - name: app
        image: vinbot:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: vinbot-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: vinbot-svc
spec:
  selector:
    app: vinbot
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress (NGINX)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vinbot-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  rules:
  - host: vinbot.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vinbot-svc
            port:
              number: 80
```

### ConfigMap & Secrets
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vinbot-config
data:
  LOG_LEVEL: "INFO"
  TRADING_STRATEGY: "Auto"
---
apiVersion: v1
kind: Secret
metadata:
  name: vinbot-secrets
type: Opaque
stringData:
  BINANCE_API_KEY: "your-key"
  BINANCE_SECRET_KEY: "your-secret"
  TELEGRAM_BOT_TOKEN: "your-token"
```

## CI/CD Pipelines

### GitHub Actions
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev

      - name: Lint
        run: |
          poetry run ruff check .
          poetry run mypy .

      - name: Test
        run: poetry run pytest --cov

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to K8s
        run: |
          echo "${{ secrets.KUBECONFIG }}" > kubeconfig
          kubectl apply -f k8s/
          kubectl set image deployment/vinbot app=ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### GitLab CI
```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install poetry
    - poetry install
    - poetry run pytest

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/vinbot app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

## Monitoring & Observability

### Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vinbot'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

```yaml
# docker-compose.yml additions
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Logging with Loki
```yaml
  loki:
    image: grafana/loki:2.9
    volumes:
      - ./monitoring/loki/loki.yml:/etc/loki/loki.yml
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:2.9
    volumes:
      - ./logs:/var/log
      - ./monitoring/loki/promtail.yml:/etc/promtail/promtail.yml
```

### Health Checks
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    # Check DB, Redis, Binance connection
    checks = {
        "db": await check_db(),
        "binance": await check_binance()
    }
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    return {"status": "not_ready", "checks": checks}, 503
```

## Infrastructure as Code

### Terraform Example
```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_ecr_repository" "vinbot" {
  name = "vinbot"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecs_cluster" "trading" {
  name = "vinbot-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_service" "vinbot" {
  name            = "vinbot"
  cluster         = aws_ecs_cluster.trading.id
  task_definition = aws_ecs_task_definition.vinbot.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.vinbot.id]
  }
}
```

## Security Best Practices

### Dockerfile Security
```dockerfile
# Never run as root
RUN addgroup -g 1000 -S appgroup && adduser -u 1000 -S appuser -G appgroup
USER appuser

# Read-only filesystem (where possible)
# SECURITY: Note this prevents writing logs to filesystem
# tmpfs can be used for temporary writes

# Scan for vulnerabilities
# docker scout cves vinbot:latest
```

### Secrets Management
```bash
# Don't commit secrets to git
# Use env variables or secret management

# Docker secrets (Swarm)
echo "mysecret" | docker secret create db_password -

# Kubernetes secrets
kubectl create secret generic vinbot-secrets \
  --from-literal=BINANCE_API_KEY=$BINANCE_API_KEY
```

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump -U vinbot -h localhost vinbot_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U vinbot -h localhost vinbot_db < backup_20240101.sql
```

### Automated Backups (Cron)
```bash
# crontab
0 2 * * * pg_dump -U vinbot vinbot_db > /backups/vinbot_$(date +\%Y\%m\%d).sql
0 3 * * * find /backups -type f -mtime +30 -delete
```

## Troubleshooting

### Docker
```bash
# View logs
docker logs vinbot
docker logs --tail 100 -f vinbot

# Inspect
docker inspect vinbot
docker stats vinbot

# Network
docker network ls
docker network inspect bridge

# Volumes
docker volume ls
docker volume inspect vinbot_data
```

### Kubernetes
```bash
# Pods
kubectl get pods
kubectl describe pod vinbot-xxx
kubectl logs vinbot-xxx

# Debug
kubectl exec -it vinbot-xxx -- sh

# Events
kubectl get events --sort-by='.lastTimestamp'

# Resources
kubectl top nodes
kubectl top pods
```

## Common Tools

| Category | Tools |
|----------|-------|
| Container | Docker, Podman, Buildah |
| Orchestration | Kubernetes, Docker Swarm |
| CI/CD | GitHub Actions, GitLab CI, Jenkins |
| IaC | Terraform, Pulumi, Ansible |
| Monitoring | Prometheus, Grafana, Loki |
| Logging | ELK Stack, Loki, CloudWatch |
| Cloud | AWS, GCP, Azure |

## When Helping

- Ask about infrastructure (local, cloud, K8s)
- Consider Docker Compose for local development
- Use multi-stage builds for smaller images
- Always include health checks
- Use secrets management, never commit secrets
- Enable monitoring from the start