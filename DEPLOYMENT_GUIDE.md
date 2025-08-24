# 🚀 Real Estate RAG Chat System - Complete Deployment Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [Database Setup](#database-setup)
6. [Environment Configuration](#environment-configuration)
7. [Security Configuration](#security-configuration)
8. [Monitoring & Logging](#monitoring--logging)
9. [Testing & Validation](#testing--validation)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

The Real Estate RAG Chat System is a sophisticated AI-powered chat application with the following enhanced features:

### **Core Features**
- **Role-based AI Personalities**: Distinct personas for clients, agents, employees, and admins
- **Milestone Detection**: Automatic celebration of achievements (new listings, deals closed, etc.)
- **African Agent Recognition**: Cultural celebration for African agents
- **Admin Analytics Panel**: Real-time user interaction monitoring
- **File Upload System**: Secure document processing
- **Chat Persistence**: Session management across requests
- **Dubai Market Intelligence**: Specialized knowledge base

### **Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │   PostgreSQL    │
│   (Port 3000)   │◄──►│   (Port 8001)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    ChromaDB     │
                       │   (Port 8000)   │
                       └─────────────────┘
```

---

## 🔧 Prerequisites

### **System Requirements**
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+ / Windows 10+
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 10GB free space
- **CPU**: 2+ cores (4+ recommended)

### **Software Requirements**
- **Python**: 3.9+ ([Download](https://www.python.org/downloads/))
- **Node.js**: 18+ ([Download](https://nodejs.org/))
- **Docker**: 20.10+ ([Download](https://www.docker.com/))
- **Git**: Latest version ([Download](https://git-scm.com/))

### **API Keys Required**
- **Google Gemini API**: [Get API Key](https://makersuite.google.com/app/apikey)
- **Domain & SSL**: For production deployment

---

## 🛠️ Local Development Setup

### **1. Clone Repository**
```bash
git clone <your-repo-url>
cd real-estate-rag-app
```

### **2. Environment Setup**
```bash
# Create environment file
cp env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# API Keys
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://admin:password123@localhost:5432/real_estate_db
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security (for production)
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### **3. Backend Setup**
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python main.py
```

### **4. Frontend Setup**
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### **5. Database Setup (Docker)**
```bash
# Start PostgreSQL and ChromaDB
docker-compose up postgres chromadb -d

# Wait for services to start (30 seconds)
sleep 30

# Run data ingestion
cd scripts
python ingest_data.py
```

### **6. Verify Installation**
```bash
# Test backend health
curl http://localhost:8001/health

# Test frontend
# Open http://localhost:3000 in browser
```

---

## 🚀 Production Deployment

### **Option 1: Docker Deployment (Recommended)**

#### **1. Production Environment File**
```bash
# Create production environment
cp env.example .env.production

# Edit production settings
nano .env.production
```

**Production Environment Variables:**
```bash
# API Keys
GOOGLE_API_KEY=your_production_google_api_key

# Database Configuration
DATABASE_URL=postgresql://prod_user:secure_password@prod_db_host:5432/real_estate_prod
CHROMA_HOST=prod_chroma_host
CHROMA_PORT=8000

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Security
SECRET_KEY=your_very_secure_secret_key_here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL Configuration
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

#### **2. Docker Compose Production**
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up --build -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### **3. Production Docker Compose File**
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
      - "443:443"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    depends_on:
      - postgres
      - chromadb
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: real_estate_prod
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  chroma_data:
```

### **Option 2: Cloud Deployment (AWS/GCP/Azure)**

#### **AWS Deployment**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS
aws configure

# Deploy using AWS ECS
aws ecs create-cluster --cluster-name real-estate-rag
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster real-estate-rag --service-name real-estate-service --task-definition real-estate-rag:1
```

#### **Google Cloud Deployment**
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Deploy to Google Cloud Run
gcloud run deploy real-estate-rag-backend --source ./backend --platform managed --region us-central1
gcloud run deploy real-estate-rag-frontend --source ./frontend --platform managed --region us-central1
```

---

## 🗄️ Database Setup

### **PostgreSQL Setup**

#### **1. Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew install postgresql
brew services start postgresql
```

#### **2. Database Configuration**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE real_estate_db;
CREATE USER admin WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE real_estate_db TO admin;
\q
```

#### **3. Schema Setup**
```bash
# Run database initialization
cd scripts
python setup_database.py

# Verify tables
psql -h localhost -U admin -d real_estate_db -c "\dt"
```

### **ChromaDB Setup**

#### **1. Install ChromaDB**
```bash
# Using pip
pip install chromadb

# Using Docker
docker run -p 8000:8000 chromadb/chroma:latest
```

#### **2. Initialize Collections**
```bash
# Run ChromaDB setup
cd scripts
python setup_chromadb.py
```

---

## 🔐 Security Configuration

### **1. SSL/TLS Setup**
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Configure Nginx SSL
sudo nano /etc/nginx/sites-available/real-estate-rag
```

**Nginx SSL Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **2. Firewall Configuration**
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **3. API Security**
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update environment variables
SECRET_KEY=your_generated_secret_key
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=3600
```

---

## 📊 Monitoring & Logging

### **1. Application Logging**
```bash
# Configure logging in backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### **2. System Monitoring**
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs
```

### **3. Application Monitoring**
```bash
# Health check endpoint
curl http://localhost:8001/health

# Admin analytics
curl http://localhost:8001/admin/analytics
```

---

## 🧪 Testing & Validation

### **1. Run Test Suite**
```bash
# Run comprehensive tests
python test_enhanced_features.py

# Check test results
cat enhanced_test_results_*.json
```

### **2. Load Testing**
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Run load test
ab -n 1000 -c 10 http://localhost:8001/health
```

### **3. API Testing**
```bash
# Test chat endpoint
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "role": "client", "session_id": "test123"}'

# Test file upload
curl -X POST http://localhost:8001/upload-file \
  -F "file=@test_file.txt"
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U admin -d real_estate_db -c "SELECT 1;"

# Reset database
sudo -u postgres dropdb real_estate_db
sudo -u postgres createdb real_estate_db
```

#### **2. API Key Issues**
```bash
# Verify Google API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

#### **3. Port Conflicts**
```bash
# Check port usage
sudo netstat -tulpn | grep :8001
sudo netstat -tulpn | grep :3000

# Kill conflicting processes
sudo kill -9 <PID>
```

#### **4. Docker Issues**
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Rebuild containers
docker-compose down
docker-compose up --build
```

### **Log Analysis**
```bash
# View application logs
tail -f app.log

# View Docker logs
docker-compose logs -f backend

# View system logs
sudo journalctl -u postgresql -f
```

---

## 📞 Support & Maintenance

### **Regular Maintenance Tasks**
```bash
# Daily
- Check system health: curl http://localhost:8001/health
- Monitor logs: tail -f app.log
- Verify database connections

# Weekly
- Update dependencies: pip install -r requirements.txt --upgrade
- Backup database: pg_dump real_estate_db > backup.sql
- Review error logs

# Monthly
- Security updates: sudo apt update && sudo apt upgrade
- Performance review: Check admin analytics
- SSL certificate renewal: sudo certbot renew
```

### **Backup Strategy**
```bash
# Database backup
pg_dump real_estate_db > backup_$(date +%Y%m%d).sql

# File uploads backup
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# Configuration backup
cp .env .env.backup.$(date +%Y%m%d)
```

### **Emergency Procedures**
```bash
# System restart
sudo systemctl restart postgresql
docker-compose restart

# Rollback to previous version
git checkout <previous_commit>
docker-compose up --build

# Restore from backup
psql real_estate_db < backup_20250101.sql
```

---

## 🎯 Next Steps

### **Immediate Actions**
1. ✅ Set up local development environment
2. ✅ Configure production environment
3. ✅ Deploy to staging environment
4. ✅ Run comprehensive testing
5. ✅ Deploy to production

### **Future Enhancements**
- [ ] User authentication system
- [ ] Multi-tenant architecture
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] API rate limiting
- [ ] Automated backups
- [ ] CI/CD pipeline

---

**Deployment Guide Version**: 1.0  
**Last Updated**: January 2025  
**System Version**: 1.2.0  
**Status**: Production Ready ✅