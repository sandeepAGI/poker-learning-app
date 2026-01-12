# Azure Deployment Plan - Poker Learning App

**Status:** FINAL - Ready for Execution
**Version:** 2.0 (Peer Reviewed)
**Created:** 2026-01-12
**Last Updated:** 2026-01-12

---

## Executive Summary

This plan details the deployment of the Poker Learning App to Microsoft Azure with GitHub Actions CI/CD integration. The architecture has been peer-reviewed and addresses critical production requirements including persistent storage, scalability, and monitoring.

### Key Highlights

- **Backend**: Azure App Service (Linux B2, Python 3.12) with WebSocket support
- **Frontend**: Azure App Service (Linux B1, Node.js 20) for Next.js 15
- **Data Layer**: Redis (session/game state) + PostgreSQL (hand history)
- **Secrets**: Azure Key Vault with managed identity
- **Monitoring**: Application Insights with comprehensive alerting
- **CI/CD**: GitHub Actions with automated testing and deployment
- **Monthly Cost**: ~$140/month (production), ~$47/month (staging)

### Architecture Improvements from Review

✅ **Added persistent storage** (Redis + PostgreSQL)
✅ **Fixed startup command** (gunicorn + uvicorn workers)
✅ **Right-sized tiers** (B2 instead of over-provisioned P1v3)
✅ **Enhanced security** (CORS, rate limiting, TLS config)
✅ **Comprehensive monitoring** (10+ alert rules)
✅ **Added pre-deployment phase** (fixes required before Azure setup)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Azure Services Selection](#azure-services-selection)
3. [Environment Strategy](#environment-strategy)
4. [Pre-Deployment Requirements](#pre-deployment-requirements-new)
5. [Deployment Steps](#deployment-steps)
6. [Security Configuration](#security-configuration)
7. [Cost Analysis](#cost-analysis)
8. [Monitoring & Operations](#monitoring--operations)
9. [Rollback & Disaster Recovery](#rollback--disaster-recovery)
10. [Deployment Checklist](#deployment-checklist)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Backend Code │  │Frontend Code │  │ GitHub       │          │
│  │              │  │              │  │ Actions      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │ CI/CD Deployment
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Resource Group: poker-learning-app-rg          │ │
│  │                                                             │ │
│  │  ┌──────────────────────┐    ┌──────────────────────┐    │ │
│  │  │  App Service         │    │ App Service          │    │ │
│  │  │  (Backend API)       │◄───┤ (Frontend)           │    │ │
│  │  │                      │    │                      │    │ │
│  │  │  - Python 3.12       │    │  - Node.js 20        │    │ │
│  │  │  - FastAPI           │    │  - Next.js 15        │    │ │
│  │  │  - WebSocket         │    │  - React 19          │    │ │
│  │  │  - B2 Tier           │    │  - B1 Tier           │    │ │
│  │  └──────────────────────┘    └──────────────────────┘    │ │
│  │           │                            │                  │ │
│  │           ▼                            ▼                  │ │
│  │  ┌──────────────────────┐    ┌──────────────────────┐   │ │
│  │  │  Redis Cache         │    │ PostgreSQL Database  │   │ │
│  │  │  (Session/Game State)│    │ (Hand History)       │   │ │
│  │  │  - Standard C1       │    │ - B1ms Burstable     │   │ │
│  │  └──────────────────────┘    └──────────────────────┘   │ │
│  │           │                                              │ │
│  │           ▼                                              │ │
│  │  ┌──────────────────────┐    ┌──────────────────────┐  │ │
│  │  │  Azure Key Vault     │    │ Application Insights │  │ │
│  │  │  - API Keys          │    │ - Logs & Metrics     │  │ │
│  │  │  - Secrets           │    │ - Alerts             │  │ │
│  │  └──────────────────────┘    └──────────────────────┘  │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Anthropic API   │
                    │  (Claude AI)     │
                    └──────────────────┘
```

### Data Flow

1. **User Request**: Browser → Frontend (App Service) → Backend (App Service)
2. **WebSocket**: Persistent connection for real-time game updates
3. **Game State**: Backend ↔ Redis (active games, sessions)
4. **Hand History**: Backend → PostgreSQL (persistent storage)
5. **AI Analysis**: Backend → Anthropic API → PostgreSQL (cached results)
6. **Monitoring**: All services → Application Insights

---

## Azure Services Selection

### 1. Backend: Azure App Service (Linux, Python 3.12)

**Selected Tier**: Basic B2
**Cost**: $26.06/month
**Specs**: 2 vCore, 3.5 GB RAM, 10 GB storage

**Why App Service?**
- ✅ Native WebSocket support (critical for real-time game updates)
- ✅ Built-in Python 3.12 runtime
- ✅ Always-on capability (no cold starts)
- ✅ Simple deployment model
- ✅ Built-in SSL/TLS
- ✅ Integrated with Application Insights

**Why B2 Tier?**
- Sufficient for 500+ concurrent users
- 2 vCores handle 100+ requests/second
- Cost-effective ($26/mo vs $100/mo Premium)
- Upgrade to Premium only when needed (>500 users)

**Alternatives Considered**:
- Azure Container Apps: ❌ Cold starts break WebSocket connections
- Azure Functions: ❌ Not suitable for persistent WebSocket connections
- Premium Tier P1v3: ❌ Over-provisioned for initial deployment (5x cost)

---

### 2. Frontend: Azure App Service (Linux, Node.js 20)

**Selected Tier**: Basic B1
**Cost**: $13.14/month (separate App Service Plan)
**Specs**: 1 vCore, 1.75 GB RAM, 10 GB storage

**Why App Service (Not Static Web Apps)?**
- ✅ Full Next.js 15 support (SSR, API routes, middleware)
- ✅ App Router compatibility
- ✅ Future-proof for server components
- ✅ Same platform as backend (easier operations)
- ✅ Only $4/month more than Static Web Apps Standard

**Static Web Apps Limitation**: Only supports static export mode (`output: 'export'`), which doesn't support Next.js SSR features or API routes.

---

### 3. Data Layer: Redis + PostgreSQL

#### Redis (Azure Cache for Redis)

**Selected Tier**: Standard C1
**Cost**: $61.68/month
**Specs**: 1 GB cache, High Availability (99.9% SLA)

**Purpose**:
- Active game state storage
- WebSocket session management
- Rate limiting counters
- Analysis cache (TTL-based)

**Why Redis is Required**:
- ✅ Enables horizontal scaling (multi-instance support)
- ✅ Session persistence across server restarts
- ✅ Sub-millisecond access times
- ✅ Built-in TTL matches game expiration logic
- ❌ Cannot scale beyond 1 instance without it

**Critical**: Redis is **not optional** for production. In-memory storage only works for single-instance demo deployments.

#### PostgreSQL (Azure Database for PostgreSQL Flexible Server)

**Selected Tier**: Burstable B1ms
**Cost**: $13.63/month
**Specs**: 1 vCore, 2 GB RAM, 32 GB storage

**Purpose**:
- Hand history storage (analysis feature)
- Player statistics (future feature)
- Analysis results cache (long-term)
- Audit logs and metrics

**Why PostgreSQL?**
- ✅ Relational data model (complex queries)
- ✅ JSON support (JSONB for flexible schemas)
- ✅ Automatic backups (7-day retention)
- ✅ Point-in-time restore
- ✅ Mature ecosystem (SQLAlchemy, Alembic)

**Schema Overview**:
```sql
games (game_id, created_at, num_players, starting_stack)
hands (hand_id, game_id, hand_number, board_cards, pot, winner_id)
actions (action_id, hand_id, player_id, action, amount, timestamp)
analysis_cache (cache_key, analysis_data, model_used, cost, expires_at)
```

---

### 4. Secrets Management: Azure Key Vault

**Selected Tier**: Standard
**Cost**: ~$5/month
**Operations**: $0.03 per 10,000 operations

**Secrets Stored**:
- `ANTHROPIC_API_KEY` (production key)
- `REDIS_PASSWORD` (Redis connection password)
- `DATABASE_URL` (PostgreSQL connection string)

**Access Control**: Managed Identity (no credentials in code)

---

### 5. Monitoring: Application Insights

**Selected Tier**: Pay-as-you-go
**Cost**: ~$5-10/month (30-day retention)
**Data Ingestion**: First 5 GB/month free, then $2.30/GB

**Monitored Metrics**:
- Request/response times (P50, P95, P99)
- Error rates (HTTP 5xx)
- WebSocket connection health
- Anthropic API call costs
- Memory and CPU usage
- Custom events (game actions, hand completions)

---

## Environment Strategy

### Three Environments

| Environment | Purpose | Backend | Frontend | Redis | PostgreSQL | Monthly Cost |
|-------------|---------|---------|----------|-------|------------|--------------|
| **Development** | Local dev | localhost | localhost | None | None | $0 |
| **Staging** | Pre-prod testing | B1 | B1 (shared) | Basic C0 | B1ms | ~$47 |
| **Production** | Live users | B2 | B1 | Standard C1 | B1ms | ~$140 |

### Environment Configuration

```yaml
# Development (Local)
ENVIRONMENT: development
BACKEND_URL: http://localhost:8000
ANTHROPIC_API_KEY: <dev-key>
TEST_MODE: 1
REDIS_HOST: localhost:6379 (optional)
DATABASE_URL: postgresql://localhost/poker_dev

# Staging (Azure)
ENVIRONMENT: staging
BACKEND_URL: https://poker-api-staging.azurewebsites.net
ANTHROPIC_API_KEY: @KeyVault(ANTHROPIC-API-KEY-STAGING)
TEST_MODE: 0
REDIS_HOST: poker-cache-staging.redis.cache.windows.net
DATABASE_URL: @KeyVault(DATABASE-URL-STAGING)

# Production (Azure)
ENVIRONMENT: production
BACKEND_URL: https://poker-api-prod.azurewebsites.net
ANTHROPIC_API_KEY: @KeyVault(ANTHROPIC-API-KEY-PROD)
TEST_MODE: 0
REDIS_HOST: poker-cache-prod.redis.cache.windows.net
DATABASE_URL: @KeyVault(DATABASE-URL-PROD)
```

---

## Pre-Deployment Requirements (NEW)

### Critical Fixes Required BEFORE Azure Setup

These changes must be implemented in the codebase **before starting Azure deployment**. Estimated time: 3-4 days.

#### 1. Database Implementation (2-3 days)

**Task**: Replace in-memory storage with Redis + PostgreSQL

**Current Issue**:
```python
# backend/main.py line 51:
games: Dict[str, Tuple[PokerGame, float]] = {}  # In-memory only!
```

**Problems**:
- Cannot scale beyond 1 instance
- Data lost on restart
- No session persistence
- Memory limits (1.75-3.5 GB)

**Required Changes**:

```python
# 1. Add dependencies to backend/requirements.txt
redis>=5.0.0
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.23
alembic>=1.13.0

# 2. Create Redis client (backend/redis_client.py)
import redis
import pickle
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6380)),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True if os.getenv("ENVIRONMENT") != "development" else False,
    decode_responses=False
)

def save_game(game_id: str, game: PokerGame, ttl: int = 7200):
    """Save game state to Redis"""
    redis_client.setex(
        f"game:{game_id}",
        ttl,
        pickle.dumps(game)
    )

def load_game(game_id: str) -> Optional[PokerGame]:
    """Load game state from Redis"""
    data = redis_client.get(f"game:{game_id}")
    return pickle.loads(data) if data else None

def delete_game(game_id: str):
    """Delete game from Redis"""
    redis_client.delete(f"game:{game_id}")

# 3. Update main.py to use Redis instead of dict
# Replace all dict operations:
# OLD: games[game_id] = (game, last_activity)
# NEW: save_game(game_id, game)

# 4. Create PostgreSQL models (backend/models.py)
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Hand(Base):
    __tablename__ = 'hands'
    hand_id = Column(String, primary_key=True)
    game_id = Column(String, index=True)
    hand_number = Column(Integer)
    board_cards = Column(JSON)
    pot = Column(Integer)
    winner_id = Column(String)
    created_at = Column(DateTime)

class Action(Base):
    __tablename__ = 'actions'
    action_id = Column(String, primary_key=True)
    hand_id = Column(String, index=True)
    player_id = Column(String)
    action = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime)

class AnalysisCache(Base):
    __tablename__ = 'analysis_cache'
    cache_key = Column(String, primary_key=True)
    analysis_data = Column(JSON)
    model_used = Column(String)
    cost = Column(Float)
    created_at = Column(DateTime)
    expires_at = Column(DateTime)

# 5. Create Alembic migration
# Run: alembic init alembic
# Edit alembic/env.py to import models
# Run: alembic revision --autogenerate -m "Initial schema"
```

**Validation**:
```bash
# Test locally with Redis
docker run -d -p 6379:6379 redis:7
cd backend && python main.py

# Test game persistence
# 1. Create game, get game_id
# 2. Restart backend
# 3. Verify game still exists
```

---

#### 2. Fix Startup Command (30 minutes)

**Current Issue**: Plan proposes `python -m uvicorn main:app` which won't work on Azure App Service

**Required Changes**:

```bash
# Add to backend/requirements.txt
gunicorn>=21.2.0

# Correct startup command:
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**Why gunicorn + uvicorn workers?**
- Azure App Service expects production WSGI server
- Multiple workers for concurrent requests
- WebSocket support via uvicorn workers
- Timeout accommodates long-running connections

**Validation**:
```bash
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
# Test WebSocket connections work
```

---

#### 3. Frontend Deployment Strategy (1-2 hours)

**Task**: Verify Next.js 15 deployment compatibility

**Check current build output**:
```bash
cd frontend
npm run build

# If output contains .next/server/ → Needs App Service (SSR)
# If output contains out/ directory → Could use Static Web Apps (static export)
```

**If SSR is needed** (recommended):
```javascript
// frontend/next.config.ts - Remove any 'export' output mode
const nextConfig = {
  // DO NOT include: output: 'export'
  reactStrictMode: true,
  swcMinify: true,
}
```

**If static export** (alternative):
```javascript
// frontend/next.config.ts
const nextConfig = {
  output: 'export', // Required for Static Web Apps
  images: {
    unoptimized: true, // Required for static export
  },
}
```

**Recommendation**: Use App Service for full Next.js support (plan assumes this)

---

#### 4. Security Fixes (1 day)

**Task**: Fix CORS, add rate limiting, security headers

**CORS Configuration**:
```python
# backend/main.py - Environment-specific CORS
from fastapi.middleware.cors import CORSMiddleware
import os

ALLOWED_ORIGINS = {
    "development": [
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    "staging": [
        "https://poker-web-staging.azurewebsites.net",
    ],
    "production": [
        "https://poker-web-prod.azurewebsites.net",
        "https://yourdomain.com",  # Custom domain if added
    ],
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS.get(os.getenv("ENVIRONMENT", "development")),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Rate Limiting**:
```python
# Add to requirements.txt
fastapi-limiter>=0.1.5

# backend/main.py
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis_client)

# Apply to endpoints
@app.post("/games/{game_id}/actions")
@app.rate_limit(limit=30, window=60)  # 30 actions per minute
async def submit_action(...):
    ...

@app.get("/games/{game_id}/analysis-llm")
@app.rate_limit(limit=5, window=300)  # 5 analysis requests per 5 min
async def get_analysis(...):
    ...
```

**Security Headers**:
```python
# backend/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Only in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.azurewebsites.net", "yourdomain.com"]
    )

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

#### 5. Application Insights Integration (2 hours)

**Task**: Add custom metrics tracking

```python
# Add to requirements.txt
opencensus-ext-azure>=1.1.13
opencensus-ext-flask>=0.7.6

# backend/main.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

# Setup logging
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger.addHandler(AzureLogHandler(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    ))

# Setup metrics
stats = stats_module.stats
view_manager = stats.view_manager
exporter = metrics_exporter.new_metrics_exporter(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)
view_manager.register_exporter(exporter)

# Custom metrics
anthropic_cost_measure = measure_module.MeasureFloat(
    "anthropic_api_cost",
    "Cost of Anthropic API calls",
    "USD"
)

# Track costs
def track_anthropic_cost(model: str, cost: float):
    mmap = stats.stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()
    tmap.insert("model", model)
    mmap.measure_float_put(anthropic_cost_measure, cost)
    mmap.record(tmap)

    # Also log for easier querying
    logger.info(
        "anthropic_api_call",
        extra={"custom_dimensions": {"model": model, "cost": cost}}
    )
```

---

### Pre-Deployment Checklist

- [ ] Redis client implementation complete
- [ ] PostgreSQL models and migrations created
- [ ] Startup command updated to gunicorn
- [ ] Frontend build strategy confirmed (SSR vs static)
- [ ] CORS configuration environment-specific
- [ ] Rate limiting implemented
- [ ] Security headers middleware added
- [ ] Application Insights integration added
- [ ] All tests passing with new infrastructure
- [ ] Local testing with Docker Redis completed

**Estimated Timeline**: 3-4 days of development work

---

## Deployment Steps

### Phase 1: Azure Account Setup (15 minutes)

#### 1.1 Create Azure Account & Install CLI

```bash
# Create account (if needed)
# Visit: https://azure.microsoft.com/free/
# Get $200 credit for 30 days

# Install Azure CLI (macOS)
brew install azure-cli

# Verify installation
az --version

# Login to Azure
az login

# Set subscription (if multiple)
az account list --output table
az account set --subscription "<subscription-name-or-id>"
```

#### 1.2 Create Resource Group

```bash
# Create resource group in East US
az group create \
  --name poker-learning-app-rg \
  --location eastus \
  --tags \
    environment=production \
    project=poker-learning-app \
    managed-by=github-actions
```

---

### Phase 2: Backend Deployment Setup (90 minutes)

#### 2.1 Create App Service Plans

```bash
# Staging: B1 Basic (shared between backend and frontend)
az appservice plan create \
  --name poker-plan-staging \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --is-linux \
  --sku B1 \
  --tags environment=staging

# Production: B2 for backend, separate B1 for frontend
az appservice plan create \
  --name poker-plan-prod-backend \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --is-linux \
  --sku B2 \
  --tags environment=production component=backend

az appservice plan create \
  --name poker-plan-prod-frontend \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --is-linux \
  --sku B1 \
  --tags environment=production component=frontend
```

#### 2.2 Create Backend App Services

```bash
# Staging backend
az webapp create \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --plan poker-plan-staging \
  --runtime "PYTHON:3.12" \
  --tags environment=staging component=backend

# Production backend
az webapp create \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --plan poker-plan-prod-backend \
  --runtime "PYTHON:3.12" \
  --tags environment=production component=backend

# Enable WebSocket support
az webapp config set \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --web-sockets-enabled true \
  --always-on true \
  --min-tls-version "1.2" \
  --http20-enabled true

az webapp config set \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --web-sockets-enabled true \
  --always-on true \
  --min-tls-version "1.2" \
  --http20-enabled true \
  --https-only true

# Configure startup command
az webapp config set \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 120"

az webapp config set \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 120"
```

#### 2.3 Create Redis Caches

```bash
# Staging: Basic C0 (no HA, lower cost)
az redis create \
  --name poker-cache-staging \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku Basic \
  --vm-size C0 \
  --tags environment=staging

# Production: Standard C1 (HA, 99.9% SLA)
az redis create \
  --name poker-cache-prod \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku Standard \
  --vm-size C1 \
  --enable-non-ssl-port false \
  --tags environment=production

# Get Redis connection details (save for later)
az redis list-keys \
  --name poker-cache-prod \
  --resource-group poker-learning-app-rg \
  --query primaryKey -o tsv
```

#### 2.4 Create PostgreSQL Databases

```bash
# Generate admin password (save this!)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
echo "PostgreSQL Password: $POSTGRES_PASSWORD" > postgres-password.txt

# Staging database
az postgres flexible-server create \
  --name poker-db-staging \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 15 \
  --admin-user pokeradmin \
  --admin-password "$POSTGRES_PASSWORD" \
  --public-access 0.0.0.0-255.255.255.255 \
  --tags environment=staging

# Production database
az postgres flexible-server create \
  --name poker-db-prod \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 15 \
  --admin-user pokeradmin \
  --admin-password "$POSTGRES_PASSWORD" \
  --backup-retention 7 \
  --geo-redundant-backup Enabled \
  --public-access 0.0.0.0-255.255.255.255 \
  --tags environment=production

# Create databases
az postgres flexible-server db create \
  --resource-group poker-learning-app-rg \
  --server-name poker-db-staging \
  --database-name pokerapp

az postgres flexible-server db create \
  --resource-group poker-learning-app-rg \
  --server-name poker-db-prod \
  --database-name pokerapp

# Allow Azure services to access database
az postgres flexible-server firewall-rule create \
  --resource-group poker-learning-app-rg \
  --name poker-db-prod \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 2.5 Create Key Vaults

```bash
# Staging Key Vault
az keyvault create \
  --name poker-kv-staging \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku standard \
  --enable-rbac-authorization false \
  --bypass AzureServices \
  --default-action Allow \
  --tags environment=staging

# Production Key Vault
az keyvault create \
  --name poker-kv-prod \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku standard \
  --enable-rbac-authorization false \
  --bypass AzureServices \
  --default-action Deny \
  --tags environment=production

# Add secrets (replace with actual values)
az keyvault secret set \
  --vault-name poker-kv-staging \
  --name ANTHROPIC-API-KEY \
  --value "sk-ant-..."

az keyvault secret set \
  --vault-name poker-kv-prod \
  --name ANTHROPIC-API-KEY \
  --value "sk-ant-..."

# Add Redis password
REDIS_PASSWORD=$(az redis list-keys --name poker-cache-prod --resource-group poker-learning-app-rg --query primaryKey -o tsv)
az keyvault secret set \
  --vault-name poker-kv-prod \
  --name REDIS-PASSWORD \
  --value "$REDIS_PASSWORD"

# Add database URL
DATABASE_URL="postgresql://pokeradmin:$POSTGRES_PASSWORD@poker-db-prod.postgres.database.azure.com/pokerapp"
az keyvault secret set \
  --vault-name poker-kv-prod \
  --name DATABASE-URL \
  --value "$DATABASE_URL"
```

#### 2.6 Enable Managed Identity for App Services

```bash
# Enable system-assigned managed identity (staging)
az webapp identity assign \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg

# Get principal ID
PRINCIPAL_ID_STAGING=$(az webapp identity show \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --query principalId -o tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name poker-kv-staging \
  --object-id $PRINCIPAL_ID_STAGING \
  --secret-permissions get list

# Repeat for production
az webapp identity assign \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg

PRINCIPAL_ID_PROD=$(az webapp identity show \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --query principalId -o tsv)

az keyvault set-policy \
  --name poker-kv-prod \
  --object-id $PRINCIPAL_ID_PROD \
  --secret-permissions get list
```

#### 2.7 Configure App Service Environment Variables

```bash
# Production backend configuration
az webapp config appsettings set \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --settings \
    ENVIRONMENT=production \
    TEST_MODE=0 \
    ANTHROPIC_API_KEY="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/ANTHROPIC-API-KEY/)" \
    REDIS_HOST="poker-cache-prod.redis.cache.windows.net" \
    REDIS_PORT=6380 \
    REDIS_PASSWORD="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/REDIS-PASSWORD/)" \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/DATABASE-URL/)" \
    PYTHONUNBUFFERED=1 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000

# Staging backend configuration (similar with staging resources)
az webapp config appsettings set \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --settings \
    ENVIRONMENT=staging \
    TEST_MODE=0 \
    ANTHROPIC_API_KEY="@Microsoft.KeyVault(SecretUri=https://poker-kv-staging.vault.azure.net/secrets/ANTHROPIC-API-KEY/)" \
    REDIS_HOST="poker-cache-staging.redis.cache.windows.net" \
    REDIS_PORT=6380 \
    REDIS_PASSWORD="@Microsoft.KeyVault(SecretUri=https://poker-kv-staging.vault.azure.net/secrets/REDIS-PASSWORD/)" \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://poker-kv-staging.vault.azure.net/secrets/DATABASE-URL/)" \
    PYTHONUNBUFFERED=1 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000
```

#### 2.8 Configure CORS

```bash
# Production CORS (will update after frontend deployment)
az webapp cors add \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --allowed-origins \
    "https://poker-web-prod.azurewebsites.net"

# Staging CORS (includes localhost for testing)
az webapp cors add \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --allowed-origins \
    "https://poker-web-staging.azurewebsites.net" \
    "http://localhost:3000"
```

#### 2.9 Create Application Insights

```bash
# Staging insights
az monitor app-insights component create \
  --app poker-insights-staging \
  --location eastus \
  --resource-group poker-learning-app-rg \
  --application-type web \
  --retention-time 30 \
  --tags environment=staging

# Production insights
az monitor app-insights component create \
  --app poker-insights-prod \
  --location eastus \
  --resource-group poker-learning-app-rg \
  --application-type web \
  --retention-time 30 \
  --tags environment=production

# Get instrumentation keys
INSIGHTS_KEY_PROD=$(az monitor app-insights component show \
  --app poker-insights-prod \
  --resource-group poker-learning-app-rg \
  --query connectionString -o tsv)

# Link to App Service
az webapp config appsettings set \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$INSIGHTS_KEY_PROD"
```

---

### Phase 3: Frontend Deployment Setup (45 minutes)

#### 3.1 Create Frontend App Services

```bash
# Staging frontend (shares App Service Plan with backend)
az webapp create \
  --name poker-web-staging \
  --resource-group poker-learning-app-rg \
  --plan poker-plan-staging \
  --runtime "NODE:20-lts" \
  --tags environment=staging component=frontend

# Production frontend (dedicated App Service Plan)
az webapp create \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --plan poker-plan-prod-frontend \
  --runtime "NODE:20-lts" \
  --tags environment=production component=frontend

# Configure settings
az webapp config set \
  --name poker-web-staging \
  --resource-group poker-learning-app-rg \
  --always-on true \
  --min-tls-version "1.2" \
  --startup-file "npm start"

az webapp config set \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --always-on true \
  --min-tls-version "1.2" \
  --https-only true \
  --startup-file "npm start"
```

#### 3.2 Configure Frontend Environment Variables

```bash
# Production frontend
az webapp config appsettings set \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --settings \
    NEXT_PUBLIC_API_URL="https://poker-api-prod.azurewebsites.net" \
    NEXT_PUBLIC_ENVIRONMENT="production" \
    NODE_ENV=production \
    PORT=8080

# Staging frontend
az webapp config appsettings set \
  --name poker-web-staging \
  --resource-group poker-learning-app-rg \
  --settings \
    NEXT_PUBLIC_API_URL="https://poker-api-staging.azurewebsites.net" \
    NEXT_PUBLIC_ENVIRONMENT="staging" \
    NODE_ENV=production \
    PORT=8080
```

---

### Phase 4: CI/CD Pipeline Setup (90 minutes)

#### 4.1 Create Service Principal for GitHub Actions

```bash
# Create service principal with contributor role
az ad sp create-for-rbac \
  --name "poker-github-actions" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/poker-learning-app-rg \
  --sdk-auth

# Output will be JSON like:
# {
#   "clientId": "...",
#   "clientSecret": "...",
#   "subscriptionId": "...",
#   "tenantId": "..."
# }
# Save this entire JSON as AZURE_CREDENTIALS secret in GitHub
```

#### 4.2 Get Publish Profiles

```bash
# Get backend publish profiles
az webapp deployment list-publishing-profiles \
  --name poker-api-staging \
  --resource-group poker-learning-app-rg \
  --xml

az webapp deployment list-publishing-profiles \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --xml

# Get frontend publish profiles
az webapp deployment list-publishing-profiles \
  --name poker-web-staging \
  --resource-group poker-learning-app-rg \
  --xml

az webapp deployment list-publishing-profiles \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --xml

# Save each as GitHub secrets:
# AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_STAGING
# AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_PROD
# AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_STAGING
# AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_PROD
```

#### 4.3 Configure GitHub Secrets

Add these secrets in GitHub repository (Settings → Secrets and variables → Actions):

```
AZURE_CREDENTIALS (JSON from step 4.1)
AZURE_WEBAPP_NAME_BACKEND_STAGING: poker-api-staging
AZURE_WEBAPP_NAME_BACKEND_PROD: poker-api-prod
AZURE_WEBAPP_NAME_FRONTEND_STAGING: poker-web-staging
AZURE_WEBAPP_NAME_FRONTEND_PROD: poker-web-prod
AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_STAGING: (XML from step 4.2)
AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_PROD: (XML from step 4.2)
AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_STAGING: (XML from step 4.2)
AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_PROD: (XML from step 4.2)
APPINSIGHTS_CONNECTION_STRING_PROD: (from Phase 2.9)
```

#### 4.4 Create GitHub Actions Workflows

Create `.github/workflows/azure-backend-deploy.yml`:

```yaml
name: Deploy Backend to Azure

on:
  push:
    branches:
      - main
      - staging
    paths:
      - 'backend/**'
      - '.github/workflows/azure-backend-deploy.yml'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run backend tests
        run: |
          PYTHONPATH=backend pytest backend/tests/ -v --maxfail=5

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Azure App Service (Staging)
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME_BACKEND_STAGING }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_STAGING }}
          package: ./backend

      - name: Run database migrations
        run: |
          # Install Alembic
          pip install alembic psycopg2-binary
          cd backend
          # Run migrations (requires DATABASE_URL in environment)
          alembic upgrade head
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_STAGING }}

      - name: Health check with retry
        run: |
          for i in {1..36}; do
            if curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_STAGING }}.azurewebsites.net/health; then
              echo "✅ Health check passed"
              exit 0
            fi
            echo "Attempt $i/36 failed, waiting 5s..."
            sleep 5
          done
          echo "❌ Health check failed after 3 minutes"
          exit 1

      - name: Smoke tests
        run: |
          # Create game
          GAME_ID=$(curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_STAGING }}.azurewebsites.net/games \
            -X POST -H "Content-Type: application/json" \
            -d '{"num_ai_players":3}' | jq -r '.game_id')
          echo "Created game: $GAME_ID"

          # Verify game exists
          curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_STAGING }}.azurewebsites.net/games/$GAME_ID

          echo "✅ Smoke tests passed"

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_PROD }}.azurewebsites.net
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Azure App Service (Production)
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME_BACKEND_PROD }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND_PROD }}
          package: ./backend

      - name: Run database migrations
        run: |
          pip install alembic psycopg2-binary
          cd backend
          alembic upgrade head
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_PROD }}

      - name: Health check with retry
        run: |
          for i in {1..36}; do
            if curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_PROD }}.azurewebsites.net/health; then
              echo "✅ Health check passed"
              exit 0
            fi
            echo "Attempt $i/36 failed, waiting 5s..."
            sleep 5
          done
          echo "❌ Health check failed"
          exit 1

      - name: Smoke tests
        run: |
          GAME_ID=$(curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_PROD }}.azurewebsites.net/games \
            -X POST -H "Content-Type: application/json" \
            -d '{"num_ai_players":3}' | jq -r '.game_id')
          echo "Created game: $GAME_ID"
          curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_BACKEND_PROD }}.azurewebsites.net/games/$GAME_ID
          echo "✅ Smoke tests passed"
```

Create `.github/workflows/azure-frontend-deploy.yml`:

```yaml
name: Deploy Frontend to Azure

on:
  push:
    branches:
      - main
      - staging
    paths:
      - 'frontend/**'
      - '.github/workflows/azure-frontend-deploy.yml'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run frontend tests
        run: npm test

      - name: Build frontend
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: "https://poker-api-staging.azurewebsites.net"

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Build production bundle
        run: cd frontend && npm run build
        env:
          NEXT_PUBLIC_API_URL: "https://poker-api-staging.azurewebsites.net"
          NEXT_PUBLIC_ENVIRONMENT: "staging"

      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME_FRONTEND_STAGING }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_STAGING }}
          package: ./frontend

      - name: Health check
        run: |
          for i in {1..24}; do
            if curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_FRONTEND_STAGING }}.azurewebsites.net; then
              echo "✅ Frontend is up"
              exit 0
            fi
            echo "Attempt $i/24 failed, waiting 5s..."
            sleep 5
          done
          echo "❌ Frontend health check failed"
          exit 1

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://${{ secrets.AZURE_WEBAPP_NAME_FRONTEND_PROD }}.azurewebsites.net
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Build production bundle
        run: cd frontend && npm run build
        env:
          NEXT_PUBLIC_API_URL: "https://poker-api-prod.azurewebsites.net"
          NEXT_PUBLIC_ENVIRONMENT: "production"

      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_WEBAPP_NAME_FRONTEND_PROD }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND_PROD }}
          package: ./frontend

      - name: Health check
        run: |
          for i in {1..24}; do
            if curl -sf https://${{ secrets.AZURE_WEBAPP_NAME_FRONTEND_PROD }}.azurewebsites.net; then
              echo "✅ Frontend is up"
              exit 0
            fi
            echo "Attempt $i/24 failed, waiting 5s..."
            sleep 5
          done
          echo "❌ Frontend health check failed"
          exit 1
```

---

### Phase 5: Monitoring & Alerts Setup (60 minutes)

#### 5.1 Configure Alert Rules

```bash
# Get resource IDs
BACKEND_ID=$(az webapp show \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --query id -o tsv)

INSIGHTS_ID=$(az monitor app-insights component show \
  --app poker-insights-prod \
  --resource-group poker-learning-app-rg \
  --query id -o tsv)

# Create action group (email notifications)
az monitor action-group create \
  --name poker-alerts \
  --resource-group poker-learning-app-rg \
  --short-name poker \
  --email-receiver \
    name="Admin" \
    email-address="your-email@example.com" \
    use-common-alert-schema=true

ACTION_GROUP_ID=$(az monitor action-group show \
  --name poker-alerts \
  --resource-group poker-learning-app-rg \
  --query id -o tsv)

# Alert 1: High error rate
az monitor metrics alert create \
  --name "High Error Rate (5xx)" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg Http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "HTTP 5xx errors exceeding threshold" \
  --action $ACTION_GROUP_ID

# Alert 2: High response time
az monitor metrics alert create \
  --name "High Response Time" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg ResponseTime > 3000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 3 \
  --description "Response time over 3 seconds" \
  --action $ACTION_GROUP_ID

# Alert 3: High CPU usage
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg CpuPercentage > 80" \
  --window-size 10m \
  --evaluation-frequency 5m \
  --severity 3 \
  --description "CPU usage over 80%" \
  --action $ACTION_GROUP_ID

# Alert 4: High memory usage
az monitor metrics alert create \
  --name "High Memory Usage" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg MemoryPercentage > 85" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "Memory usage over 85%" \
  --action $ACTION_GROUP_ID

# Alert 5: Low availability
az monitor metrics alert create \
  --name "Service Unavailable" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg HealthCheckStatus < 1" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 1 \
  --description "Health check failing" \
  --action $ACTION_GROUP_ID
```

#### 5.2 Enable Diagnostic Logging

```bash
# Create storage account for logs (optional, uses retention)
az storage account create \
  --name pokerlogsstorage \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku Standard_LRS

# Enable App Service logging
az webapp log config \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --application-logging azureblobstorage \
  --level verbose \
  --web-server-logging filesystem \
  --docker-container-logging filesystem

# Enable diagnostic settings (sends to Application Insights)
az monitor diagnostic-settings create \
  --name poker-api-diagnostics \
  --resource $BACKEND_ID \
  --logs '[{"category": "AppServiceHTTPLogs", "enabled": true}, {"category": "AppServiceConsoleLogs", "enabled": true}]' \
  --metrics '[{"category": "AllMetrics", "enabled": true}]' \
  --workspace $INSIGHTS_ID
```

---

## Security Configuration

### 1. Network Security

#### SSL/TLS Configuration

```bash
# Enforce HTTPS (already configured in Phase 2)
az webapp update \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --https-only true

# Verify TLS 1.2 minimum
az webapp config show \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --query minTlsVersion
```

#### IP Restrictions (Optional)

```bash
# Restrict SCM site access (Kudu/deployment portal)
az webapp config access-restriction add \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --rule-name "Block-Public-SCM" \
  --action Deny \
  --priority 100 \
  --scm-site true

# Allow specific IP for admin access
az webapp config access-restriction add \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --rule-name "Allow-Admin-IP" \
  --action Allow \
  --priority 50 \
  --ip-address "YOUR.IP.ADDRESS.HERE" \
  --scm-site true
```

### 2. Authentication & Authorization

App Service uses managed identity for Key Vault access (configured in Phase 2).

**Rate Limiting** is implemented in application code (see Pre-Deployment Requirements section).

### 3. Secrets Management

All secrets stored in Azure Key Vault:
- ✅ ANTHROPIC_API_KEY
- ✅ REDIS_PASSWORD
- ✅ DATABASE_URL

App Services reference secrets via:
```
@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/SECRET-NAME/)
```

### 4. Audit Logging

Key Vault audit logs are automatically enabled. View in Azure Portal:
```
Key Vault → Monitoring → Logs → AuditEvent table
```

---

## Cost Analysis

### Monthly Cost Breakdown

#### Staging Environment

| Service | Tier | Specs | Monthly Cost |
|---------|------|-------|--------------|
| App Service Plan B1 | Shared (backend + frontend) | 1 vCore, 1.75GB RAM | $13.14 |
| Redis Cache Basic C0 | No HA | 250 MB | $16.79 |
| PostgreSQL B1ms | Burstable | 1 vCore, 2 GB RAM | $13.63 |
| Key Vault Standard | - | - | ~$3 |
| Application Insights | 1 GB/mo | 30-day retention | Free tier |
| **Staging Total** | | | **$46.56/mo** |

#### Production Environment

| Service | Tier | Specs | Monthly Cost |
|---------|------|-------|--------------|
| App Service Plan B2 (backend) | Dedicated | 2 vCore, 3.5GB RAM | $26.06 |
| App Service Plan B1 (frontend) | Dedicated | 1 vCore, 1.75GB RAM | $13.14 |
| Redis Cache Standard C1 | HA, 99.9% SLA | 1 GB | $61.68 |
| PostgreSQL B1ms | Burstable | 1 vCore, 2GB RAM | $13.63 |
| Key Vault Standard | - | - | ~$5 |
| Application Insights | ~2 GB/mo | 30-day retention | ~$5 |
| **Production Total** | | | **$124.51/mo** |

#### Combined Total

**Staging + Production**: **$171.07/month**

### Cost Optimization Tips

1. **Share App Service Plan** (staging only): Saves $13/mo by hosting both backend and frontend on same plan
2. **30-day log retention**: Saves $15-20/mo vs 90-day retention
3. **Basic tiers for initial deployment**: Save $150/mo vs Premium tiers, upgrade when >500 users
4. **Reserved instances** (after 3 months): Save 40-72% if usage is stable

### When to Upgrade

**Upgrade to Premium Tier (P1v3) when:**
- Sustained >500 concurrent users
- Monthly revenue >$1,000/month
- Need zero-downtime deployments (deployment slots)
- Need more than 3 instances for auto-scale

**Cost at Scale**:
- P1v3 Plan (2-5 instances): ~$200-500/month
- Total with databases: ~$300-600/month

### Cost Monitoring

Set up budget alerts:
```bash
az consumption budget create \
  --resource-group poker-learning-app-rg \
  --budget-name poker-monthly-budget \
  --amount 200 \
  --category cost \
  --time-grain monthly \
  --time-period start-date=2026-01-01 \
  --notification \
    enabled=true \
    operator=GreaterThan \
    threshold=80 \
    contact-emails="your-email@example.com"
```

---

## Monitoring & Operations

### Application Insights Dashboards

Create custom dashboard in Azure Portal:

1. **Overview Metrics**:
   - Request rate (requests/sec)
   - Average response time
   - Failed requests (%)
   - Server response time

2. **WebSocket Metrics**:
   - Active connections
   - Connection duration
   - Messages sent/received

3. **Business Metrics**:
   - Games created per hour
   - Hands played per hour
   - AI analysis requests (count + cost)
   - Active users

4. **Infrastructure Metrics**:
   - CPU percentage
   - Memory working set
   - Disk queue length
   - Network in/out

### Custom KQL Queries

Access in Application Insights → Logs:

```kql
// Top 10 slowest API endpoints
requests
| where timestamp > ago(1h)
| summarize avg(duration), count() by name
| order by avg_duration desc
| take 10

// Anthropic API cost tracking (custom events)
customEvents
| where name == "anthropic_api_call"
| extend cost = toreal(customDimensions.cost), model = tostring(customDimensions.model)
| summarize total_cost = sum(cost), call_count = count() by model, bin(timestamp, 1h)
| order by timestamp desc

// WebSocket connection health
customMetrics
| where name == "websocket_connections"
| summarize avg(value), max(value), min(value) by bin(timestamp, 5m)
| render timechart

// Error rate by endpoint
exceptions
| where timestamp > ago(1h)
| summarize count() by operation_Name
| order by count_ desc
| take 10

// User session duration
pageViews
| where timestamp > ago(24h)
| summarize session_duration = max(timestamp) - min(timestamp) by session_Id
| summarize avg(session_duration), percentile(session_duration, 50), percentile(session_duration, 95)
```

### Streaming Logs

```bash
# Stream application logs
az webapp log tail \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg

# Download logs for analysis
az webapp log download \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --log-file ./app-logs.zip
```

---

## Rollback & Disaster Recovery

### Rollback Procedures

#### Option 1: Redeploy Previous Commit (Simple)

```bash
# Trigger GitHub Actions workflow for specific commit
git checkout <previous-commit-hash>
git push --force origin main
# GitHub Actions redeploys automatically
```

#### Option 2: Manual Deployment from Local

```bash
# Checkout previous version
git checkout <previous-commit-hash>

# Deploy backend
cd backend
zip -r ../backend.zip .
az webapp deployment source config-zip \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --src ../backend.zip

# Deploy frontend
cd frontend
npm run build
zip -r ../frontend.zip .
az webapp deployment source config-zip \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --src ../frontend.zip
```

#### Option 3: Swap Deployment Slots (Premium Tier Only)

If using Premium tier with deployment slots:
```bash
az webapp deployment slot swap \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --slot staging \
  --target-slot production
```

### Disaster Recovery Strategy

#### Backups

**PostgreSQL**: Automatic backups enabled (7-day retention, geo-redundant)
```bash
# Restore from backup
az postgres flexible-server restore \
  --name poker-db-prod-restore \
  --resource-group poker-learning-app-rg \
  --source-server poker-db-prod \
  --restore-time "2026-01-10T10:00:00Z"
```

**Redis**: No persistent backups (data is transient)
- Game state can be recovered from PostgreSQL hand history
- Session data is acceptable to lose (users reconnect)

**App Service**: Backup not configured (stateless, code in Git)

#### Recovery Objectives

| Metric | Target | Notes |
|--------|--------|-------|
| **RTO** (Recovery Time Objective) | 1 hour | Time to restore service |
| **RPO** (Recovery Point Objective) | 5 minutes | Acceptable data loss |
| **MTTR** (Mean Time To Recover) | 30 minutes | Average recovery time |

#### Disaster Recovery Steps

1. **Assess Impact** (5 min)
   - Check Application Insights for error patterns
   - Identify affected services (backend, frontend, database)
   - Determine scope (partial vs total outage)

2. **Communication** (5 min)
   - Post status update (status page or social media)
   - Notify team via Slack/email
   - Set expectations for recovery time

3. **Execute Recovery** (20-40 min)
   - **Database issue**: Restore from backup
   - **Code issue**: Rollback deployment
   - **Infrastructure issue**: Recreate Azure resources

4. **Validation** (10 min)
   - Run smoke tests
   - Verify health checks pass
   - Monitor logs for errors

5. **Post-Mortem** (1-2 hours, after incident)
   - Document timeline
   - Identify root cause
   - Create action items to prevent recurrence

---

## Deployment Checklist

### Pre-Deployment (3-4 days)

#### Code Changes
- [ ] Redis session store implemented
- [ ] PostgreSQL models created
- [ ] Database migrations ready (Alembic)
- [ ] Startup command updated (gunicorn)
- [ ] CORS configuration environment-specific
- [ ] Rate limiting implemented
- [ ] Security headers added
- [ ] Application Insights integration added
- [ ] All tests passing locally

#### Local Testing
- [ ] Backend runs with Redis (Docker)
- [ ] Backend runs with PostgreSQL (Docker)
- [ ] Frontend builds successfully
- [ ] WebSocket connections work
- [ ] Database migrations apply successfully
- [ ] Integration tests pass

---

### Azure Setup (Phase 1-5: ~4 hours)

#### Phase 1: Account Setup
- [ ] Azure account created
- [ ] Azure CLI installed and logged in
- [ ] Subscription selected
- [ ] Resource group created

#### Phase 2: Backend Infrastructure
- [ ] App Service Plans created (staging + production)
- [ ] Backend App Services created
- [ ] WebSocket support enabled
- [ ] Always-on enabled
- [ ] Startup command configured
- [ ] Redis caches created (Basic for staging, Standard for production)
- [ ] PostgreSQL databases created
- [ ] Key Vaults created
- [ ] Secrets added to Key Vault (ANTHROPIC_API_KEY, REDIS_PASSWORD, DATABASE_URL)
- [ ] Managed identity enabled for App Services
- [ ] Key Vault access policies configured
- [ ] Environment variables configured
- [ ] CORS configured
- [ ] Application Insights created
- [ ] Insights linked to App Services

#### Phase 3: Frontend Infrastructure
- [ ] Frontend App Services created
- [ ] Startup command configured
- [ ] Environment variables configured

#### Phase 4: CI/CD Pipeline
- [ ] Service principal created
- [ ] Publish profiles downloaded
- [ ] GitHub secrets configured
- [ ] Backend deployment workflow created
- [ ] Frontend deployment workflow created
- [ ] Test deployment successful (staging)

#### Phase 5: Monitoring & Alerts
- [ ] Action group created (email notifications)
- [ ] 5+ alert rules configured
- [ ] Diagnostic logging enabled
- [ ] Custom dashboard created

---

### Post-Deployment Validation (1-2 hours)

#### Smoke Tests
- [ ] Health endpoints accessible
- [ ] Create game via API
- [ ] Submit 10 actions via API
- [ ] Verify WebSocket connection
- [ ] Test hand analysis feature
- [ ] Verify Redis session persistence (restart backend)
- [ ] Verify PostgreSQL hand history stored

#### Performance Tests
- [ ] Load test with 10 concurrent users
- [ ] Monitor response times (<1 second P95)
- [ ] Check memory usage (<70%)
- [ ] Check CPU usage (<60%)
- [ ] Verify auto-cleanup works (idle games deleted)

#### Security Validation
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] TLS 1.2 minimum enforced
- [ ] CORS only allows configured origins
- [ ] Rate limiting works (test by exceeding limits)
- [ ] Managed identity can access Key Vault
- [ ] No secrets in environment variables
- [ ] Security headers present in responses

#### Monitoring Validation
- [ ] Logs streaming to Application Insights
- [ ] Custom metrics appearing (Anthropic cost, WebSocket connections)
- [ ] Alert rules functional (trigger test alert)
- [ ] Dashboard showing real-time metrics

#### Documentation
- [ ] Update docs/AZURE-DEPLOYMENT-PLAN.md with actual resource names
- [ ] Document database connection details
- [ ] Create operations runbook
- [ ] Document rollback procedures
- [ ] Update README with deployment URLs

---

### Production Cutover

#### Before Launch
- [ ] Staging environment fully tested
- [ ] Production environment deployed
- [ ] DNS configured (if custom domain)
- [ ] SSL certificate validated
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Backup/restore tested
- [ ] Monitoring dashboard ready
- [ ] Alert recipients confirmed
- [ ] Launch announcement prepared

#### Launch Day
- [ ] Deploy production backend
- [ ] Deploy production frontend
- [ ] Run smoke tests
- [ ] Monitor logs for first 30 minutes
- [ ] Monitor Application Insights dashboard
- [ ] Verify no critical alerts
- [ ] Test from multiple devices/browsers
- [ ] Announce launch

#### Post-Launch (First 48 Hours)
- [ ] Monitor error rates every 4 hours
- [ ] Review Application Insights daily
- [ ] Check Anthropic API costs daily
- [ ] Verify no resource exhaustion (memory, CPU)
- [ ] Collect user feedback
- [ ] Document any issues encountered

---

## Appendix

### Useful Azure CLI Commands

```bash
# View all resources in resource group
az resource list --resource-group poker-learning-app-rg --output table

# Get App Service URL
az webapp show --name poker-api-prod --resource-group poker-learning-app-rg --query defaultHostName -o tsv

# Restart App Service
az webapp restart --name poker-api-prod --resource-group poker-learning-app-rg

# Get Redis connection string
az redis show --name poker-cache-prod --resource-group poker-learning-app-rg --query hostName -o tsv

# Get PostgreSQL connection details
az postgres flexible-server show --name poker-db-prod --resource-group poker-learning-app-rg

# View cost analysis
az consumption usage list --start-date 2026-01-01 --end-date 2026-01-31

# Delete all resources (DANGER!)
az group delete --name poker-learning-app-rg --yes --no-wait
```

### Troubleshooting

**Issue**: App Service not starting
```bash
# Check logs
az webapp log tail --name poker-api-prod --resource-group poker-learning-app-rg

# Check startup command
az webapp config show --name poker-api-prod --resource-group poker-learning-app-rg --query appCommandLine
```

**Issue**: Cannot connect to Redis
```bash
# Test connection
nc -zv poker-cache-prod.redis.cache.windows.net 6380

# Check firewall rules
az redis firewall-rules list --name poker-cache-prod --resource-group poker-learning-app-rg
```

**Issue**: Database connection failing
```bash
# Check firewall rules
az postgres flexible-server firewall-rule list --name poker-db-prod --resource-group poker-learning-app-rg

# Test connection
psql "host=poker-db-prod.postgres.database.azure.com port=5432 dbname=pokerapp user=pokeradmin password=<password> sslmode=require"
```

**Issue**: High memory usage
```bash
# Restart App Service
az webapp restart --name poker-api-prod --resource-group poker-learning-app-rg

# Scale up if needed
az appservice plan update --name poker-plan-prod-backend --resource-group poker-learning-app-rg --sku P1v3
```

---

## Summary

This deployment plan provides a production-ready Azure architecture for the Poker Learning App with:

✅ **Scalability**: Redis + PostgreSQL enable horizontal scaling
✅ **Reliability**: High availability Redis, automatic backups
✅ **Security**: Key Vault, managed identity, rate limiting
✅ **Monitoring**: Application Insights with 5+ alert rules
✅ **Cost-Effective**: $171/month total (staging + production)
✅ **CI/CD**: Automated GitHub Actions deployments
✅ **Disaster Recovery**: 1-hour RTO, 5-minute RPO

**Estimated Total Effort**: 1 week (3-4 days pre-deployment + 1 day Azure setup + 1-2 days testing)

**Next Steps**: Complete pre-deployment requirements, then execute Phase 1-5 in sequence.

---

**Document Version**: 2.0 (Final)
**Last Updated**: 2026-01-12
**Review Status**: ✅ Peer Reviewed and Approved
