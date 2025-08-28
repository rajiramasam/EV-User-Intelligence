# 🚀 EV User Intelligence Platform - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the EV User Intelligence Platform to production using Snowflake as the primary database.

## 🏗️ Architecture Overview

```
Frontend (React) → Backend (FastAPI) → Snowflake Database
                     ↓
              JWT Authentication
              Rate Limiting
              CORS Protection
              Sentry Monitoring
```

## 📋 Prerequisites

### 1. Snowflake Account
- Active Snowflake account with admin privileges
- Warehouse, database, and schema created
- User with appropriate permissions

### 2. Environment Setup
- Python 3.8+ installed
- Node.js 16+ installed
- Git for version control

### 3. API Keys
- OpenChargeMap API key (optional, for additional station data)
- Sentry DSN (optional, for error monitoring)
- OpenRouter API key (for AI chatbot features)

## 🔧 Environment Configuration

### 1. Backend Environment Variables
Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
SNOWFLAKE_ACCOUNT=your_snowflake_account
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_WAREHOUSE=your_warehouse_name
SNOWFLAKE_DATABASE=your_database_name
SNOWFLAKE_SCHEMA=your_schema_name

# JWT Configuration
JWT_SECRET_KEY=your_very_secure_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Security
PASSWORD_SALT=your_very_secure_password_salt_here

# Sentry Configuration (Optional)
SENTRY_DSN=your_sentry_dsn_here

# OpenRouter API Configuration (for AI Chatbot)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Open Charge Map API
OCM_API_KEY=your_openchargemap_api_key

# ML Model Path
RECOMMENDATION_MODEL_PATH=models/recommendation_model.pkl
```

### 2. Frontend Environment Variables
Create a `.env` file in the `frontend/` directory:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=production
```

## 🗄️ Database Setup

### 1. Initialize Snowflake Database
Run the production database setup script:

```bash
cd backend
python setup_production_db.py
```

This script will:
- Create all necessary tables
- Insert sample station data
- Set up proper indexes and constraints

### 2. Verify Database Connection
Test the connection:

```bash
cd backend
python -c "
from db.snowflake_connector import SnowflakeManager
manager = SnowflakeManager()
print('✅ Snowflake connection successful')
print(f'Stations count: {manager.get_station_count()}')
"
```

## 🚀 Backend Deployment

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Production Dependencies
Add these to `requirements.txt` for production:

```txt
# Production dependencies
gunicorn==20.1.0
uvicorn[standard]==0.18.3
python-multipart==0.0.5
```

### 3. Start Production Server
```bash
# Development
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Environment-Specific Configuration
Update `backend/app.py` for production:

```python
# Production CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🌐 Frontend Deployment

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Build Production Version
```bash
npm run build
```

### 3. Serve Production Build
```bash
# Using serve (install globally: npm install -g serve)
serve -s build -l 3000

# Using nginx (recommended for production)
# Copy build folder to nginx html directory
```

## 🔒 Security Configuration

### 1. JWT Security
- Use a strong, random JWT secret key
- Set appropriate token expiration times
- Enable secure cookies in production

### 2. Password Security
- Update `PASSWORD_SALT` in environment variables
- Consider using bcrypt instead of SHA-256 for production
- Implement password complexity requirements

### 3. CORS Configuration
- Restrict CORS origins to production domains
- Disable credentials for unauthorized domains

### 4. Rate Limiting
- Adjust rate limits based on production load
- Monitor rate limit violations

## 📊 Monitoring & Logging

### 1. Sentry Integration
- Set up Sentry project for error tracking
- Configure appropriate alerting rules

### 2. Application Logging
- Configure structured logging
- Set up log aggregation (ELK stack, etc.)

### 3. Performance Monitoring
- Monitor API response times
- Track database query performance
- Set up alerts for slow responses

## 🚀 Deployment Options

### Option 1: Traditional VPS/Cloud Server
```bash
# 1. Set up server (Ubuntu 20.04+ recommended)
# 2. Install Python, Node.js, nginx
# 3. Clone repository
# 4. Set up environment variables
# 5. Run database setup
# 6. Start backend service
# 7. Build and serve frontend
# 8. Configure nginx reverse proxy
```

### Option 2: Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      # ... other env vars
    depends_on:
      - snowflake
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
```

### Option 3: Cloud Platform Deployment
- **AWS**: Use ECS/Fargate for backend, S3 + CloudFront for frontend
- **Google Cloud**: Use Cloud Run for backend, Firebase Hosting for frontend
- **Azure**: Use App Service for backend, Static Web Apps for frontend

## 🔍 Testing Production Deployment

### 1. Health Checks
```bash
# Test backend health
curl http://yourdomain.com/health

# Test database connection
curl http://yourdomain.com/stations/count
```

### 2. Authentication Flow
```bash
# Test user registration
curl -X POST http://yourdomain.com/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","first_name":"Test","last_name":"User","vehicle_type":"tesla"}'

# Test user login
curl -X POST http://yourdomain.com/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### 3. API Endpoints
```bash
# Test stations endpoint
curl http://yourdomain.com/stations/

# Test nearby stations
curl "http://yourdomain.com/stations/nearby?lat=40.7128&lon=-74.0060&radius=10"
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Snowflake credentials
   - Verify network connectivity
   - Check firewall rules

2. **JWT Token Issues**
   - Verify JWT_SECRET_KEY is set
   - Check token expiration settings
   - Verify secure cookie settings

3. **CORS Errors**
   - Check CORS configuration
   - Verify frontend URL in backend CORS settings
   - Check browser console for specific errors

4. **Rate Limiting**
   - Adjust rate limit settings
   - Monitor rate limit violations
   - Check if legitimate users are being blocked

## 📈 Performance Optimization

### 1. Database Optimization
- Add appropriate indexes
- Optimize query performance
- Use connection pooling

### 2. API Optimization
- Implement response caching
- Use pagination for large datasets
- Optimize database queries

### 3. Frontend Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement lazy loading

## 🔄 Maintenance & Updates

### 1. Regular Tasks
- Monitor database performance
- Review error logs
- Update dependencies
- Backup database

### 2. Scaling Considerations
- Monitor resource usage
- Plan for horizontal scaling
- Implement load balancing if needed

## 📞 Support

For production deployment support:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual components
4. Review this deployment guide

## 🎯 Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure automated backups
3. Implement CI/CD pipeline
4. Set up staging environment
5. Plan for scaling and optimization

---

**🚀 Your EV User Intelligence Platform is now production-ready!**

Remember to:
- Regularly monitor system health
- Keep dependencies updated
- Monitor security advisories
- Test backup and recovery procedures
- Document any custom configurations
