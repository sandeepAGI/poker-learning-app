# CI/CD Flow Diagram

Visual representation of the automated deployment pipeline.

---

## Complete CI/CD Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Developer Workflow                          │
└─────────────────────────────────────────────────────────────────┘

Developer writes code
    │
    ├─→ Edit backend/main.py
    ├─→ Edit frontend/components/PokerTable.tsx
    └─→ git add . && git commit -m "Add feature" && git push origin main
        │
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub (Free Tier)                       │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │             Workflow: Test Suite (5-8 min)                │ │
│  │                                                            │ │
│  │  [1] Backend Tests                                        │ │
│  │      ├─→ pytest tests/ -v --cov=.                        │ │
│  │      ├─→ Generate coverage report                        │ │
│  │      └─→ ✅ Pass (70%+ coverage)                         │ │
│  │                                                            │ │
│  │  [2] Frontend Tests                                       │ │
│  │      ├─→ npm run lint                                    │ │
│  │      ├─→ npm run type-check                              │ │
│  │      ├─→ npm run build                                   │ │
│  │      └─→ ✅ Pass                                          │ │
│  │                                                            │ │
│  │  [3] Integration Tests                                    │ │
│  │      ├─→ Start PostgreSQL                                │ │
│  │      ├─→ Run migrations                                  │ │
│  │      ├─→ Test API endpoints                              │ │
│  │      └─→ ✅ Pass                                          │ │
│  │                                                            │ │
│  │  [4] Security Scan                                        │ │
│  │      ├─→ Trivy vulnerability scan                        │ │
│  │      ├─→ Check for secrets                               │ │
│  │      └─→ ✅ Pass                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼                                       │
│                    All tests pass?                               │
│                          │                                       │
│                ┌─────────┴─────────┐                            │
│                │                   │                             │
│              YES                  NO                             │
│                │                   │                             │
│                │                   └─→ ❌ Stop, notify developer │
│                │                                                 │
│                ▼                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │       Workflow: Deploy Backend (3-5 min)                  │ │
│  │                                                            │ │
│  │  [1] Checkout code                                        │ │
│  │  [2] Set up Python 3.12                                   │ │
│  │  [3] Install dependencies                                 │ │
│  │  [4] Create deployment package (zip)                      │ │
│  │  [5] Azure Login (service principal)                      │ │
│  │  [6] Deploy to App Service                                │ │
│  │  [7] Verify health endpoint                               │ │
│  │  └─→ ✅ Deployment successful!                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │       Workflow: Deploy Frontend (2-4 min)                 │ │
│  │                                                            │ │
│  │  [1] Checkout code                                        │ │
│  │  [2] Set up Node.js 20                                    │ │
│  │  [3] Install npm dependencies                             │ │
│  │  [4] Run linter                                           │ │
│  │  [5] Build Next.js (static export)                        │ │
│  │  [6] Deploy to Static Web App                             │ │
│  │  └─→ ✅ Deployment successful!                            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Azure Production                           │
│                                                                   │
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │   Backend Updated    │        │  Frontend Updated    │      │
│  │   poker-api-demo     │◄───────┤  poker-web-demo      │      │
│  │   (Python 3.12)      │        │  (Next.js static)    │      │
│  └──────────────────────┘        └──────────────────────┘      │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────┐                                       │
│  │  PostgreSQL B1ms     │                                       │
│  │  (Schema unchanged)  │                                       │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
        │
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Users See Updates                         │
│  - New features live in 5-7 minutes                              │
│  - Zero downtime                                                 │
│  - Automatic rollback if tests fail                              │
└─────────────────────────────────────────────────────────────────┘
```

**Total time**: 5-7 minutes from `git push` to live

---

## Pull Request Flow

```
Developer creates PR
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Pull Request                          │
│                                                                   │
│  Automatically runs:                                              │
│  ✅ Backend tests                                                │
│  ✅ Frontend tests                                               │
│  ✅ Integration tests                                            │
│  ✅ Security scan                                                │
│                                                                   │
│  Results shown in PR checks:                                     │
│  ┌──────────────────────────────────────────────┐              │
│  │ ✅ test-suite / backend-tests (5m)           │              │
│  │ ✅ test-suite / frontend-tests (3m)          │              │
│  │ ✅ test-suite / integration-tests (4m)       │              │
│  │ ✅ test-suite / security-scan (2m)           │              │
│  └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Code review + approval
    │
    ▼
Merge to main
    │
    ▼
Automatic deployment (see main flow above)
```

---

## Database Migration Flow (Manual)

```
Developer adds new migration
    │
    ├─→ cd backend
    ├─→ alembic revision -m "add_new_table"
    ├─→ Edit migration file
    ├─→ alembic upgrade head (test locally)
    └─→ git commit && git push
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GitHub Actions (Manual Trigger)                │
│                                                                   │
│  Developer goes to Actions tab                                   │
│  └─→ Click "Database Migration" workflow                         │
│      └─→ Click "Run workflow"                                    │
│          ├─→ Select environment: production                      │
│          └─→ Type "migrate" to confirm                           │
│              │                                                    │
│              ▼                                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Workflow: Database Migration (1-2 min)                   │ │
│  │                                                            │ │
│  │  [1] Validate confirmation                                │ │
│  │  [2] Show pending migrations                              │ │
│  │  [3] Connect to Azure PostgreSQL                          │ │
│  │  [4] Run: alembic upgrade head                            │ │
│  │  [5] Verify current version                               │ │
│  │  └─→ ✅ Migration complete!                               │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
Azure PostgreSQL schema updated
```

**Why manual?** Safety - database migrations are irreversible and require human confirmation.

---

## Rollback Flow

```
Production issue detected
    │
    ▼
Developer decides to rollback
    │
    ├─→ Option 1: Revert commit
    │   └─→ git revert HEAD && git push
    │       └─→ Triggers automatic redeploy (5-7 min)
    │
    ├─→ Option 2: Emergency manual deploy
    │   └─→ git checkout <last-good-commit>
    │       └─→ cd backend && zip -r ../backend.zip .
    │           └─→ az webapp deploy (manual)
    │
    └─→ Option 3: Stop app (last resort)
        └─→ az webapp stop --name poker-api-demo
            └─→ Fix issue
                └─→ az webapp start --name poker-api-demo
```

---

## Initial Setup Flow (One-Time)

```
New developer joins project
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Step 1: Azure Setup (5 min)                   │
│                                                                   │
│  az login                                                         │
│  az ad sp create-for-rbac --name "github-poker-app" ...         │
│  └─→ Save JSON output                                            │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                Step 2: GitHub Secrets (5 min)                    │
│                                                                   │
│  GitHub → Settings → Secrets → Actions                           │
│  Add secrets:                                                     │
│  ├─→ AZURE_CREDENTIALS                                           │
│  └─→ ANTHROPIC_API_KEY                                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│           Step 3: Run Azure Setup Workflow (15 min)              │
│                                                                   │
│  GitHub → Actions → Azure Initial Setup → Run workflow          │
│  ├─→ Creates: Resource Group                                     │
│  ├─→ Creates: PostgreSQL B1ms                                    │
│  ├─→ Creates: App Service B1                                     │
│  ├─→ Creates: Static Web App                                     │
│  └─→ Outputs: Credentials artifact                               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│        Step 4: Add Generated Secrets (5 min)                     │
│                                                                   │
│  Download credentials artifact                                   │
│  Add to GitHub Secrets:                                          │
│  ├─→ DATABASE_URL_PRODUCTION                                     │
│  └─→ AZURE_STATIC_WEB_APPS_API_TOKEN                            │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│          Step 5: Run Database Migration (2 min)                  │
│                                                                   │
│  GitHub → Actions → Database Migration → Run workflow           │
│  └─→ Creates: users, games, hands, analysis_cache tables        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                Step 6: Deploy Code (5-7 min)                     │
│                                                                   │
│  git push origin main                                             │
│  └─→ Automatic deployment                                        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
✅ Production ready!
```

**Total setup time**: 30-40 minutes

---

## Monitoring Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Continuous Monitoring                         │
│                                                                   │
│  GitHub Actions                                                   │
│  ├─→ Workflow run history                                        │
│  ├─→ Deployment logs                                             │
│  └─→ Test results                                                │
│                                                                   │
│  Azure Portal                                                     │
│  ├─→ Application Insights                                        │
│  │   ├─→ Request/response times                                  │
│  │   ├─→ Error rates                                             │
│  │   └─→ Custom metrics                                          │
│  │                                                                │
│  ├─→ App Service                                                  │
│  │   ├─→ Log stream (live)                                       │
│  │   ├─→ Metrics (CPU, memory)                                   │
│  │   └─→ Deployment history                                      │
│  │                                                                │
│  └─→ Cost Management                                              │
│      ├─→ Daily spend                                              │
│      ├─→ Projected monthly cost                                  │
│      └─→ Budget alerts                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Secrets Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       Secret Management                           │
│                                                                   │
│  GitHub Secrets (encrypted at rest)                              │
│  ├─→ AZURE_CREDENTIALS                                           │
│  ├─→ ANTHROPIC_API_KEY                                           │
│  ├─→ DATABASE_URL_PRODUCTION                                     │
│  └─→ AZURE_STATIC_WEB_APPS_API_TOKEN                            │
│      │                                                            │
│      ▼                                                            │
│  GitHub Actions workflows (secure injection)                     │
│  ├─→ Available as ${{ secrets.SECRET_NAME }}                     │
│  ├─→ Masked in logs                                              │
│  └─→ Never exposed to pull requests from forks                   │
│      │                                                            │
│      ▼                                                            │
│  Azure App Service (environment variables)                       │
│  ├─→ Set during deployment                                       │
│  ├─→ Available as os.getenv("SECRET_NAME")                       │
│  └─→ Not visible in Azure Portal by default                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Monthly Cost Breakdown                       │
│                                                                   │
│  Azure                                                            │
│  ├─→ App Service B1: $13.14/month                               │
│  ├─→ PostgreSQL B1ms: $13.63/month                              │
│  ├─→ Static Web App: $0 (free tier)                             │
│  └─→ Application Insights: $0 (free tier)                       │
│                                                                   │
│  GitHub Actions (private repo)                                   │
│  ├─→ Free tier: 2,000 minutes/month                             │
│  ├─→ Usage: ~180 minutes/month (10 deploys)                     │
│  └─→ Cost: $0 (within free tier)                                │
│                                                                   │
│  Total: $26.77/month ≈ $0.90/day                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       Security Pipeline                           │
│                                                                   │
│  [1] Code committed                                               │
│      └─→ Pre-commit hook (local)                                 │
│          ├─→ Run critical tests                                  │
│          └─→ Check for secrets                                   │
│              │                                                    │
│              ▼                                                    │
│  [2] Push to GitHub                                               │
│      └─→ Security scan workflow                                  │
│          ├─→ Trivy vulnerability scan                            │
│          ├─→ Check for accidentally committed secrets            │
│          └─→ Dependency audit                                    │
│              │                                                    │
│              ▼                                                    │
│  [3] Deployment                                                   │
│      └─→ Azure security                                           │
│          ├─→ HTTPS only                                           │
│          ├─→ Managed identity (no passwords in code)             │
│          ├─→ Secrets in environment variables                    │
│          └─→ Database firewall (Azure services only)             │
│              │                                                    │
│              ▼                                                    │
│  [4] Runtime                                                      │
│      └─→ Application security                                    │
│          ├─→ JWT token validation                                │
│          ├─→ CORS restrictions                                   │
│          ├─→ SQL injection protection (parameterized queries)    │
│          └─→ Password hashing (bcrypt)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Trigger Automatic Deployment
```bash
git push origin main
```

### Trigger Manual Deployment
```
GitHub → Actions → Deploy Backend → Run workflow
GitHub → Actions → Deploy Frontend → Run workflow
```

### Run Database Migration
```
GitHub → Actions → Database Migration → Run workflow
```

### View Deployment Status
```
GitHub → Actions → Click latest workflow run
```

### View Application Logs
```
Azure Portal → App Service → Log stream
```

### Check Cost
```
Azure Portal → Cost Management → Cost Analysis
```

---

**See also**:
- Full setup guide: `docs/GITHUB-ACTIONS-SETUP.md`
- Quick commands: `docs/CICD-QUICK-REFERENCE.md`
- Deployment checklist: `docs/MVP-DEPLOYMENT-CHECKLIST.md`
