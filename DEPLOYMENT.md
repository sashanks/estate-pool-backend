# Production Deployment Guide

This guide covers deploying the Neighborhood Due Diligence API to production environments.

## Deployment Options

### Option 1: Cloud Run (Google Cloud Platform) - Recommended

**Pros:**
- Serverless, auto-scaling
- Pay-per-use pricing
- Easy Firebase integration (same GCP project)
- Automatic HTTPS

**Steps:**

1. Install Google Cloud CLI:
```bash
curl https://sdk.cloud.google.com | bash
```

2. Authenticate:
```bash
gcloud auth login
gcloud config set project neighbourhood-4c5b6
```

3. Build and deploy:
```bash
gcloud run deploy neighborhood-api \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --timeout 600 \
  --set-env-vars OLLAMA_BASE_URL=http://ollama-server:11434 \
  --allow-unauthenticated
```

4. Configure environment variables in Cloud Run console:
   - FIREBASE_CREDENTIALS_PATH
   - OLLAMA_BASE_URL
   - CACHE_DIR (can use /tmp)
   - CACHE_TTL_SECONDS

**Note:** Cloud Run is stateless. For persistent cache, use Google Cloud Storage or Firestore.

---

### Option 2: Docker on VPS/EC2

**Requirements:**
- VPS with Docker and Docker Compose installed
- Ubuntu 20.04 LTS or similar
- 8GB+ RAM, 50GB storage
- Open ports: 80, 443, 8000

**Steps:**

1. SSH into your server:
```bash
ssh user@your-server-ip
```

2. Clone repository:
```bash
git clone https://github.com/yourorg/neighbourhood-api.git
cd neighbourhood-api/backend
```

3. Add credentials:
```bash
# Copy your firebase_credentials.json
# Create .env file with your configuration
```

4. Start with Docker Compose:
```bash
docker-compose -p neighbourhood up -d
```

5. Setup Nginx reverse proxy:
```bash
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/neighbourhood`:
```nginx
server {
    listen 80;
    server_name api.neighbourhood.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/neighbourhood /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. Setup SSL with Let's Encrypt:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.neighbourhood.com
```

---

### Option 3: Kubernetes (EKS/GKE/AKS)

**Requirements:**
- Kubernetes cluster
- kubectl configured
- Container registry (Docker Hub, ECR, GCR)

**Deploy:**

1. Build and push image:
```bash
docker build -t yourreg/neighbourhood-api:1.0.0 .
docker push yourreg/neighbourhood-api:1.0.0
```

2. Create k8s manifests (`k8s-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neighbourhood-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: neighbourhood-api
  template:
    metadata:
      labels:
        app: neighbourhood-api
    spec:
      containers:
      - name: api
        image: yourreg/neighbourhood-api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: OLLAMA_BASE_URL
          value: "http://ollama-service:11434"
        - name: CACHE_DIR
          value: "/tmp/cache"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: neighbourhood-api-service
spec:
  selector:
    app: neighbourhood-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

3. Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl get pods
kubectl logs -f deployment/neighbourhood-api
```

---

## Production Checklist

- [ ] **HTTPS/TLS:** All traffic encrypted
- [ ] **Database:** Firestore backups enabled
- [ ] **Caching:** Redis or managed cache for scaling
- [ ] **Logging:** Centralized logging (CloudLogging, ELK, Datadog)
- [ ] **Monitoring:** Uptime monitoring, error tracking (Sentry)
- [ ] **Rate Limiting:** Implemented to prevent abuse
- [ ] **Secrets:** Use secrets manager for credentials
- [ ] **CORS:** Properly configured for Flutter app
- [ ] **Database Indexing:** Firestore indexes optimized
- [ ] **Load Testing:** Verified performance under load
- [ ] **Disaster Recovery:** Backup and restore plan documented
- [ ] **API Versioning:** /api/v1 prefix for future compatibility

---

## Environment Variables for Production

Create `.env.production`:
```
FIREBASE_CREDENTIALS_PATH=/secrets/firebase_credentials.json
OLLAMA_BASE_URL=http://ollama-cluster-internal:11434
OLLAMA_MODEL=llama3.2
CACHE_DIR=/persistent-storage/cache
CACHE_TTL_SECONDS=604800  # 7 days
API_V1_PREFIX=/api/v1
```

---

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (AWS ELB, GCP Load Balancer, Nginx)
- Ensure cache is shared (Redis, Memcached)
- Database reads should scale automatically (Firestore)

### Vertical Scaling
- Increase CPU/RAM per instance
- Monitor with: `docker stats`
- Adjust Ollama parameters for throughput

### Caching Strategy for Scale
```python
# Use Redis for distributed caching
from redis import Redis

redis_client = Redis(host='redis-server', port=6379)

def get_cached(key):
    return redis_client.get(key)

def set_cache(key, value, ttl=86400):
    redis_client.setex(key, ttl, value)
```

---

## Monitoring & Alerting

### Key Metrics
- Request latency (p50, p95, p99)
- Error rate
- Cache hit ratio
- LLM response time
- Firebase quota usage

### Setup Monitoring

**Google Cloud Monitoring:**
```bash
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

**Datadog Integration:**
```bash
# Add Datadog agent to docker-compose.yml
datadog:
  image: datadog/agent:latest
  environment:
    - DD_API_KEY=your_key
    - DD_LOGS_ENABLED=true
```

---

## Troubleshooting in Production

### High Latency
- Check Ollama response time: `curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"test"}'`
- Review Firestore query performance
- Check Google Search API rate limits

### Out of Memory
- Reduce LLM batch size
- Use smaller model: `ollama pull mistral` (faster, less memory)
- Implement request queuing

### Firebase Quota Exceeded
- Implement more aggressive caching
- Use Firestore sharding
- Contact Firebase support for quota increase

---

## Disaster Recovery

### Backup Strategy

1. **Firestore Backups:**
```bash
gcloud firestore export gs://your-bucket/backup-$(date +%s)
```

2. **Database Migration:**
```bash
gcloud firestore export gs://your-bucket/export-dir
# On new database:
gcloud firestore import gs://your-bucket/export-dir
```

3. **Cache Clearing:**
```bash
rm -rf /path/to/cache/*
```

---

## Cost Optimization

| Service | Estimation | Tips |
|---------|-----------|------|
| Cloud Run | $0.00002400/req | Cache aggressively |
| Firestore | Pay-per-op | Add indexes, optimize queries |
| Ollama | Self-hosted (low cost) | Run on dedicated GPU instance |
| Storage | ~$0.020/GB | Archive old cache logs |

---

## Security in Production

1. **Secrets Management:**
```bash
# Use Google Secret Manager
gcloud secrets create firebase-creds --data-file=firebase_credentials.json

# In app:
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(name="projects/{}/secrets/firebase-creds/versions/latest")
```

2. **Network Security:**
   - VPC isolation
   - Firewall rules (only allow known IPs)
   - API Gateway for additional layer

3. **Audit Logging:**
```python
# Log all API calls
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url} from {request.client.host}")
    response = await call_next(request)
    return response
```

---

## Performance Benchmarks

Expected performance on production setup:

| Scenario | Response Time | Notes |
|----------|---------------|-------|
| Cache hit | 50-100ms | Fastest path |
| Firestore only | 200-300ms | With good indexes |
| Full pipeline | 3-10s | Includes LLM inference |
| Google Search | 500-1500ms | May timeout on rate limit |

---

## Contact & Support

For production issues:
- Check logs: `kubectl logs -f` or `docker logs`
- Monitor dashboards
- Contact Firebase/GCP support
- Review uptime monitoring alerts

---

**Last Updated:** January 2025
**Version:** 1.0.0-prod
