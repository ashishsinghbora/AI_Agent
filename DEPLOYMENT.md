# Deployment Guide

## Deployment Options

### Option 1: Local Native Installation (Recommended for Development)

Best for: Single user, local machine, development

#### Prerequisites
- Fedora Linux (or compatible)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- Python 3.10+
- Node.js 16+

#### Installation Steps

```bash
# 1. Navigate to project directory
cd /home/ashu/RnD/research_agent

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Start application
./start-all.sh
```

#### Manage with systemd (Optional)

Create `/etc/systemd/system/research-agent.service`:

```ini
[Unit]
Description=Research Student AI Agent
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=ashu
WorkingDirectory=/home/ashu/RnD/research_agent
ExecStart=/home/ashu/RnD/research_agent/start-all.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable research-agent
sudo systemctl start research-agent
sudo systemctl status research-agent
```

---

### Option 2: Docker Deployment

Best for: Isolation, consistent environments, easy scaling

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 6GB RAM
- 15GB disk space

#### Installation

```bash
# 1. Navigate to project
cd /home/ashu/RnD/research_agent

# 2. Build images
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Check status
docker-compose ps
```

#### Manage Docker Deployment

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v

# Restart
docker-compose restart
```

#### Docker Configuration

File: `.env.docker`

```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_PRIMARY_MODEL=deepseek-r1:7b
OLLAMA_FALLBACK_MODEL=gemma2:2b
RESEARCH_NOTES_PATH=/data/research_notes
CHROMA_PERSIST_DIR=/data/chroma
```

#### Docker Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect research_agent_ollama-data

# Backup volume
docker run --rm -v research_agent_ollama-data:/data \
  -v /backup:/backup \
  alpine tar czf /backup/ollama-backup.tar.gz -C /data .
```

---

### Option 3: Cloud Deployment (Advanced)

#### AWS EC2

1. **Create EC2 Instance**
   - AMI: Fedora 38+
   - Instance Type: t3.medium (4GB RAM)
   - Storage: 20GB EBS

2. **SSH and Setup**
   ```bash
   ssh -i key.pem ec2-user@instance-ip
   sudo dnf update -y
   git clone <repo> research_agent
   cd research_agent
   ./setup.sh
   ```

3. **Open Security Group**
   - Port 3000 (Frontend)
   - Port 8000 (Backend)
   - Port 11434 (Ollama)

4. **Make Public** (Optional)
   ```bash
   # Update frontend .env
   REACT_APP_API_BASE_URL=http://<instance-ip>:8000
   ```

#### Digital Ocean App Platform

1. Create `app.yaml`:
   ```yaml
   name: research-agent
   
   services:
   - name: backend
     build:
       dockerfile_path: Dockerfile.backend
     http_port: 8000
     envs:
     - key: OLLAMA_BASE_URL
       value: http://ollama:11434
   
   - name: frontend
     build:
       dockerfile_path: frontend/Dockerfile
     http_port: 3000
   
   - name: ollama
     image: ollama/ollama:latest
     ports:
     - number: 11434
   ```

2. Deploy:
   ```bash
   doctl apps create --spec app.yaml
   ```

---

### Option 4: Kubernetes Deployment (Production)

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-agent-backend

spec:
  replicas: 1
  selector:
    matchLabels:
      app: research-agent-backend
  
  template:
    metadata:
      labels:
        app: research-agent-backend
    
    spec:
      containers:
      - name: backend
        image: research-agent:backend-latest
        ports:
        - containerPort: 8000
        env:
        - name: OLLAMA_BASE_URL
          value: http://ollama-service:11434
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service

spec:
  type: LoadBalancer
  selector:
    app: research-agent-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

Deploy:
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f pod/research-agent-backend-xxx
```

---

## Post-Deployment Configuration

### 1. Ollama Model Management

```bash
# List models
ollama list

# Pull additional models
ollama pull mistral:latest
ollama pull llama2:latest

# Check model size
ollama show deepseek-r1:7b
```

### 2. Backup & Recovery

```bash
# Backup ChromaDB
tar czf backup-chroma.tar.gz /tmp/chroma/

# Backup Research Notes
tar czf backup-research.tar.gz /home/ashu/research_notes/

# Restore
tar xzf backup-chroma.tar.gz -C /tmp/
tar xzf backup-research.tar.gz -C /home/ashu/
```

### 3. Monitoring

Monitor system resources:
```bash
# Watch CPU/Memory
htop

# Check Ollama service
sudo systemctl status ollama

# View logs
journalctl -u ollama -f
```

### 4. Troubleshooting Deployment

**Issue: Port already in use**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Issue: Out of disk space**
```bash
# Clean Docker
docker system prune -a

# Check disk usage
df -h
du -sh /tmp/chroma/
```

**Issue: High memory usage**
```bash
# Check running processes
ps aux | grep ollama

# Restart Ollama
sudo systemctl restart ollama
```

---

## Performance Tuning

### For Low-End PC

```bash
# Edit /etc/default/ollama
OLLAMA_NUM_PARALLEL=1          # Single parallel request
OLLAMA_NUM_GPU=0               # Disable GPU (CPU only)
OLLAMA_KEEP_ALIVE=5m           # Model cache timeout
OLLAMA_MAX_LOADED_MODELS=1     # Only 1 model in RAM
```

### For High-Performance Server

```bash
# Edit /etc/default/ollama
OLLAMA_NUM_PARALLEL=4          # Multiple requests
OLLAMA_NUM_GPU=4               # Use all GPU cores
OLLAMA_KEEP_ALIVE=30m          # Longer cache
OLLAMA_MAX_LOADED_MODELS=2     # Keep 2 models ready
```

---

## Security Hardening

### 1. Enable HTTPS

Use nginx reverse proxy:

```nginx
upstream backend {
  server localhost:8000;
}

upstream frontend {
  server localhost:3000;
}

server {
  listen 443 ssl http2;
  server_name research.example.com;

  ssl_certificate /etc/letsencrypt/live/research.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/research.example.com/privkey.pem;

  location /api/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  location / {
    proxy_pass http://frontend;
    proxy_set_header Host $host;
  }
}
```

### 2. Add Authentication

Edit `backend/main.py`:

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/api/research")
async def research(
    credentials: HTTPAuthCredentials = Depends(security),
    query_data: ResearchQuery = None
):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # ... rest of function
```

### 3. Restrict API Access

```bash
# UFW firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 443/tcp # HTTPS
sudo ufw allow 80/tcp  # HTTP
sudo ufw enable

# iptables rules
sudo iptables -A INPUT -p tcp --dport 11434 -j DROP  # Block Ollama port
```

---

## Scaling Strategies

### Horizontal Scaling

1. **Multiple Backend Instances**
   - Use load balancer (nginx, HAProxy)
   - Shared database for sessions
   - Distributed cache (Redis)

2. **Separate Ollama Server**
   - Dedicated machine for models
   - Share via docker network
   - Scale models independently

### Vertical Scaling

1. **More Memory**
   - Increase VM/machine RAM
   - Cache more models
   - Larger batch sizes

2. **GPU Support**
   - Install CUDA/cuDNN
   - Configure Ollama for GPU
   - Dramatic speed improvement

---

## Monitoring & Logging

### Setup ELK Stack (Optional)

```yaml
# docker-compose additions
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
```

### Application Monitoring

```python
from prometheus_client import Counter, Histogram, start_http_server

request_count = Counter('research_requests_total', 'Total research requests')
request_duration = Histogram('research_duration_seconds', 'Research duration')

@app.post("/api/research")
async def research(query_data: ResearchQuery):
    request_count.inc()
    with request_duration.time():
        # ... research logic
```

---

## Maintenance Schedule

### Daily
- Monitor disk usage
- Check error logs
- Verify services running

### Weekly
- Backup research notes
- Backup ChromaDB
- Review system stats

### Monthly
- Update dependencies
- Clean old sessions
- Security patches

### Quarterly
- Full system backup
- Performance analysis
- Capacity planning

---

## Troubleshooting Deployment Issues

| Issue | Solution |
|-------|----------|
| Models won't download | Check internet, disk space, Ollama running |
| High memory usage | Restart Ollama, check `keep_alive` setting |
| Slow responses | Add more RAM, use GPU, reduce batch size |
| Connection refused | Check ports open, firewall rules |
| Research timeout | Check network, increase timeout in `.env` |

---

## Support & Help

1. Check logs first
2. Review troubleshooting guides
3. Check API documentation
4. Verify system requirements
5. Test with curl/Postman

---

**Deployment Guide v1.0 - Jan 2024**
