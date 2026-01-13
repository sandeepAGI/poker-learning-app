# MVP Azure Deployment Checklist

**Target**: Deploy demo in 1.5-2 days
**Cost**: ~$27/month
**User Limit**: 500+ (no hard limit with this architecture)

---

## Overview

This is a simplified deployment plan for a 10-20 user demo. Key differences from the full plan:

| Feature | Full Plan | MVP |
|---------|-----------|-----|
| Auth | Auth0 (OAuth, magic links) | Simple username/password |
| Caching | Redis ($62/month) | None (PostgreSQL only) |
| Database Schema | 8 tables, triggers, views | 4 simple tables |
| Environments | Dev, Staging, Prod | Dev (local) + Prod |
| CI/CD | GitHub Actions (multi-env) | GitHub Actions (single-env) |
| Monitoring | 10+ alerts, analytics | Basic Application Insights |
| Monthly Cost | $145 | $27 |
| Setup Time | 7-9 days | 2 days |

---

## Day 1 Morning: Backend Code Changes (4 hours)

### 1. Add Dependencies (5 minutes)

```bash
cd backend
```

Add to `requirements.txt`:
```
bcrypt>=4.0.1
pyjwt>=2.8.0
alembic>=1.13.0
psycopg2-binary>=2.9.9
```

Install:
```bash
pip install -r requirements.txt
```

### 2. Create Auth Module (30 minutes)

Create `backend/auth.py`:
```python
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 3. Create Database Models (30 minutes)

Create `backend/models.py` (see migration file for schema).

### 4. Initialize Alembic (15 minutes)

```bash
cd backend
alembic init alembic
```

Copy `backend/alembic/versions/001_mvp_schema.py` from the provided migration.

Update `alembic.ini`:
```ini
sqlalchemy.url = postgresql://localhost/poker_dev
```

### 5. Update Main.py with Auth Endpoints (45 minutes)

Add to `backend/main.py`:
```python
from auth import hash_password, verify_password, create_token, verify_token
from models import User, Game, Hand, AnalysisCache
from sqlalchemy.orm import Session

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/poker_dev")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth endpoints
@app.post("/auth/register")
async def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()

    return {
        "token": create_token(user.user_id),
        "user_id": user.user_id,
        "username": username
    }

@app.post("/auth/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "token": create_token(user.user_id),
        "user_id": user.user_id,
        "username": username
    }
```

### 6. Update Game Endpoints (1 hour)

Add user_id to game creation, save hands to database, implement analysis caching (see full implementation in main response).

### 7. Add History Endpoints (45 minutes)

```python
# Get user's games
@app.get("/users/me/games")
async def get_my_games(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    games = db.query(Game).filter(
        Game.user_id == user_id,
        Game.status == "completed"
    ).order_by(Game.started_at.desc()).limit(20).all()

    return {"games": [...]}  # Format response

# Get game hands
@app.get("/games/{game_id}/hands")
async def get_game_hands(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Verify ownership and return hands
```

### ✅ Checkpoint: Test Locally

```bash
# Terminal 1: Start local PostgreSQL
docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=poker_dev -p 5432:5432 -d postgres:15

# Terminal 2: Run migrations
export DATABASE_URL="postgresql://postgres:postgres@localhost/poker_dev"
cd backend && alembic upgrade head

# Terminal 3: Start backend
cd backend && python main.py
```

Test:
```bash
# Register
curl -X POST http://localhost:8000/auth/register -d "username=test&password=test123"

# Login
curl -X POST http://localhost:8000/auth/login -d "username=test&password=test123"
```

---

## Day 1 Afternoon: Frontend Code Changes (4 hours)

### 1. Create Auth Library (30 minutes)

Create `frontend/lib/auth.ts` with `login()`, `register()`, `logout()`, `getToken()`, `apiClient()`.

### 2. Create Login Page (1 hour)

Create `frontend/app/login/page.tsx` with username/password form.

### 3. Create Game History Page (1.5 hours)

Create `frontend/app/history/page.tsx` with table of completed games.

### 4. Create Hand Review Page (1 hour)

Create `frontend/app/history/[gameId]/page.tsx` with hand-by-hand review and analysis.

### 5. Update Existing Game Flow (30 minutes)

Add auth token to existing API calls in `PokerTable.tsx` and WebSocket connection.

```typescript
// In PokerTable.tsx
import { apiClient } from '@/lib/auth';

// Replace fetch calls with apiClient
const response = await apiClient(`/games/${gameId}/action`, {
  method: 'POST',
  body: JSON.stringify({ action, amount })
});
```

### ✅ Checkpoint: Test Locally

```bash
cd frontend
npm run dev
```

- Visit http://localhost:3000/login
- Register new account
- Play a game
- Visit http://localhost:3000/history
- Review hands

---

## Day 2 Morning: CI/CD Setup with GitHub Actions (2 hours)

**Full documentation**: See `docs/GITHUB-ACTIONS-SETUP.md` for detailed instructions.
**Quick reference**: See `docs/CICD-QUICK-REFERENCE.md` for common commands.

### 1. Create Azure Service Principal (5 minutes)

```bash
# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac \
  --name "github-poker-learning-app" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

**Save the entire JSON output** - you'll add it to GitHub Secrets.

### 2. Add GitHub Secrets (5 minutes)

Go to GitHub repo → **Settings → Secrets and variables → Actions**

Add these secrets:
1. **AZURE_CREDENTIALS**: Paste the full JSON from step 1
2. **ANTHROPIC_API_KEY**: Your Anthropic API key from console.anthropic.com

### 3. Run Azure Setup Workflow (15 minutes)

In GitHub:
1. Go to **Actions** tab
2. Click **"Azure Initial Setup"** workflow
3. Click **"Run workflow"**
4. Enter your Anthropic API key
5. Type `setup` to confirm
6. Click **"Run workflow"**

**This creates all Azure resources automatically** (10-15 minutes).

After completion:
1. Click the completed workflow run
2. Download the **"azure-credentials"** artifact
3. Open `CREDENTIALS.txt` and **save securely**

### 4. Add Generated Secrets (5 minutes)

From `CREDENTIALS.txt`, add to GitHub Secrets:
1. **DATABASE_URL_PRODUCTION**: PostgreSQL connection string
2. **AZURE_STATIC_WEB_APPS_API_TOKEN**: Static Web App deployment token

You should now have **4 total secrets** in GitHub.

### 5. Run Database Migration (2 minutes)

In GitHub:
1. Go to **Actions** tab
2. Click **"Database Migration"** workflow
3. Click **"Run workflow"**
4. Select `production` environment
5. Type `migrate` to confirm
6. Click **"Run workflow"**

This creates the database tables.

### 6. Deploy Code (Automatic!)

```bash
# Commit your code
git add .
git commit -m "MVP implementation with auth and database"
git push origin main
```

GitHub Actions will automatically:
- ✅ Run tests
- ✅ Deploy backend to Azure App Service
- ✅ Deploy frontend to Azure Static Web App

**Watch the deployment**:
- Go to **Actions** tab
- See workflows running in real-time
- Green checkmark = success!

**Deployment takes 5-7 minutes total.**

---

## Day 2 Afternoon: Testing & Validation (4 hours)

### 1. Smoke Tests (2 hours)

**Backend Health Check**:
```bash
curl https://poker-api-demo.azurewebsites.net/health
```

**Register Demo User**:
```bash
curl -X POST https://poker-api-demo.azurewebsites.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

**Full Flow Test**:
1. Open frontend URL
2. Register account
3. Play full game (10+ hands)
4. Complete game
5. Check game history
6. Review hands
7. Get AI analysis (check cache on second request)
8. Verify database has records:
   ```bash
   # Connect to Azure PostgreSQL
   psql "$DATABASE_URL"

   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM games;
   SELECT COUNT(*) FROM hands;
   SELECT COUNT(*) FROM analysis_cache;
   ```

### 2. Performance Tests (1 hour)

- Load test with 5 concurrent users (Apache Bench):
  ```bash
  ab -n 100 -c 5 https://poker-api-demo.azurewebsites.net/health
  ```
- Check response times < 500ms
- Verify WebSocket connections work
- Test from mobile device

### 3. Cost Validation (30 minutes)

Check Azure Portal → Cost Management:
- Expected: ~$0.90/day = ~$27/month
- If higher, identify culprit (likely database tier)

### 4. Fix Issues (2 hours buffer)

Common issues:
- CORS errors → Update CORS origins in backend
- Database connection timeout → Check firewall rules
- 500 errors → Check Application Insights logs
- Frontend not loading → Check NEXT_PUBLIC_API_URL

---

## Post-Deployment Checklist

### Production Readiness
- [ ] Backend deployed and responding
- [ ] Frontend deployed and loading
- [ ] Database migrations applied
- [ ] Auth registration works
- [ ] Auth login works
- [ ] Game creation works
- [ ] WebSocket connection works
- [ ] Hand history saves
- [ ] Game history page loads
- [ ] Hand review page works
- [ ] AI analysis works
- [ ] Analysis caching works (check logs)
- [ ] Mobile responsive
- [ ] HTTPS working
- [ ] Logs visible in Application Insights

### Security
- [ ] JWT_SECRET is random 64-char hex (not default)
- [ ] Database password is strong (auto-generated)
- [ ] ANTHROPIC_API_KEY set correctly
- [ ] Database firewall allows Azure services only
- [ ] CORS only allows your frontend domain
- [ ] No secrets in git repository
- [ ] No test accounts with weak passwords

### Documentation
- [ ] Save all credentials securely (1Password, etc.)
- [ ] Document DATABASE_URL
- [ ] Document JWT_SECRET
- [ ] Document backend URL
- [ ] Document frontend URL
- [ ] Share demo credentials with team

### User Acceptance
- [ ] Demo to 3-5 test users
- [ ] Collect feedback
- [ ] Create GitHub issues for bugs
- [ ] Prioritize top 3 improvements

---

## Rollback Plan

If deployment fails catastrophically:

```bash
# Delete everything and start over
az group delete --name poker-demo-rg --yes

# Or just redeploy backend
cd backend
zip -r ../backend.zip .
az webapp deploy --name poker-api-demo --resource-group poker-demo-rg --src-path ../backend.zip --type zip
```

---

## Scaling Later

When you outgrow MVP (>50 users):

1. **Upgrade database** (5 minutes, $10/month):
   ```bash
   az postgres flexible-server update \
     --name poker-db-demo \
     --resource-group poker-demo-rg \
     --sku-name Standard_B2s
   ```

2. **Upgrade backend** (5 minutes, $13/month):
   ```bash
   az appservice plan update \
     --name poker-plan \
     --resource-group poker-demo-rg \
     --sku B2
   ```

3. **Add Redis** (4 hours, $17/month):
   ```bash
   az redis create --name poker-cache --resource-group poker-demo-rg --sku Basic --vm-size C0
   ```

4. **Add Auth0** (1 day, free tier):
   - Follow Auth0 integration guide from full deployment plan
   - Migrate existing users with password reset flow

---

## Cost Breakdown

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| App Service (backend) | B1 | $13.14 |
| Static Web App (frontend) | Free | $0 |
| PostgreSQL | B1ms | $13.63 |
| Application Insights | Free tier | $0 |
| **Total** | | **$26.77** |

**Savings vs full plan**: $118/month = $1,416/year

---

## Success Criteria

After 1.5-2 days, you should have:

✅ Working poker game in Azure
✅ User accounts with username/password
✅ Game history stored in database
✅ Hand-by-hand review capability
✅ AI analysis with caching (cost savings)
✅ Production-ready architecture (can scale to 500+ users)
✅ Total cost <$30/month

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg

# Common issues:
# - Missing DATABASE_URL
# - Wrong Python version
# - Missing dependencies in requirements.txt
```

### Frontend shows blank page
```bash
# Check browser console for errors
# Common issues:
# - CORS not configured
# - API URL wrong in .env.production
# - Build failed (check npm run build locally)
```

### Database connection fails
```bash
# Check firewall
az postgres flexible-server firewall-rule list \
  --name poker-db-demo \
  --resource-group poker-demo-rg

# Add your IP if needed
az postgres flexible-server firewall-rule create \
  --name poker-db-demo \
  --resource-group poker-demo-rg \
  --rule-name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

### Analysis not caching
```bash
# Check database
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM analysis_cache;"

# Check logs for "Cache HIT" / "Cache MISS"
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg | grep -i cache
```

---

## Next Steps After MVP

1. **Week 1**: Demo to 5-10 users, collect feedback
2. **Week 2**: Fix critical bugs, polish UX
3. **Week 3**: Decide whether to:
   - Scale up (add Auth0, Redis, staging environment)
   - Pivot (change game mechanics, target audience)
   - Stop (validate demand before investing more)

MVP gives you **validation before investment**.

---

**Questions?** Check logs first:
```bash
# Backend logs
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg

# Database connection test
psql "$DATABASE_URL" -c "SELECT 1;"
```
