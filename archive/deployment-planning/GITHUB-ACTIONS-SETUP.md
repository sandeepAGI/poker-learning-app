# GitHub Actions CI/CD Setup Guide

Complete guide for setting up automated deployments to Azure using GitHub Actions.

---

## Overview

### What Gets Automated

✅ **Backend Deployment** - Auto-deploy on push to `main` (backend changes)
✅ **Frontend Deployment** - Auto-deploy on push to `main` (frontend changes)
✅ **Database Migrations** - Manual trigger (for safety)
✅ **Test Suite** - Auto-run on PRs and pushes
✅ **Security Scanning** - Auto-scan for vulnerabilities
✅ **Azure Initial Setup** - One-time manual trigger

### Deployment Flow

```
git push origin main
    │
    ├─→ Backend changed?
    │   ├─→ Run backend tests
    │   └─→ Deploy to Azure App Service
    │
    └─→ Frontend changed?
        ├─→ Run linter + build
        └─→ Deploy to Azure Static Web App
```

---

## Prerequisites

1. **Azure Subscription** (Free tier works)
2. **Anthropic API Key** from https://console.anthropic.com/
3. **GitHub Repository** (this repo)

---

## Step 1: Create Azure Service Principal (5 minutes)

This allows GitHub Actions to manage your Azure resources.

### Option A: Using Azure CLI (Recommended)

```bash
# Login to Azure
az login

# Get your subscription ID
az account show --query id -o tsv

# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-poker-learning-app" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

**Important**: Save the entire JSON output. You'll need it for GitHub secrets.

The output looks like:
```json
{
  "clientId": "xxxxx",
  "clientSecret": "xxxxx",
  "subscriptionId": "xxxxx",
  "tenantId": "xxxxx",
  ...
}
```

### Option B: Using Azure Portal

1. Go to Azure Portal → Azure Active Directory → App Registrations
2. Click "New registration"
3. Name: "github-poker-learning-app"
4. Click "Register"
5. Go to "Certificates & secrets" → "New client secret"
6. Save the secret value (you won't see it again)
7. Go to Subscriptions → Your Subscription → Access Control (IAM)
8. Add role assignment → Contributor → Select your app

Then manually create the JSON:
```json
{
  "clientId": "<from app registration>",
  "clientSecret": "<from secrets>",
  "subscriptionId": "<your subscription ID>",
  "tenantId": "<from app registration>"
}
```

---

## Step 2: Configure GitHub Secrets (10 minutes)

Go to your GitHub repo → Settings → Secrets and variables → Actions

### Required Secrets

Click "New repository secret" for each:

#### 1. `AZURE_CREDENTIALS`
Paste the entire JSON from Step 1:
```json
{
  "clientId": "xxxxx",
  "clientSecret": "xxxxx",
  "subscriptionId": "xxxxx",
  "tenantId": "xxxxx"
}
```

#### 2. `ANTHROPIC_API_KEY`
Your Anthropic API key from https://console.anthropic.com/
```
sk-ant-api03-...
```

---

## Step 3: Run Azure Setup Workflow (15 minutes)

This creates all Azure resources automatically.

### In GitHub:

1. Go to **Actions** tab
2. Click **"Azure Initial Setup"** workflow
3. Click **"Run workflow"** dropdown
4. Fill in:
   - **anthropic_api_key**: Paste your Anthropic key
   - **confirm_setup**: Type `setup`
5. Click **"Run workflow"**

### What This Creates:

- Resource Group: `poker-demo-rg`
- PostgreSQL: `poker-db-demo` (B1ms tier)
- App Service Plan: `poker-plan` (B1 tier)
- Backend: `poker-api-demo` (Python 3.12)
- Frontend: `poker-web-demo` (Static Web App)

**Timeline**: 5-10 minutes (database creation is slowest)

### After Completion:

1. Click on the completed workflow run
2. Download the **"azure-credentials"** artifact
3. Open `CREDENTIALS.txt` and **save it securely** (1Password, etc.)

---

## Step 4: Add Generated Secrets to GitHub (5 minutes)

From the `CREDENTIALS.txt` file, add these to GitHub Secrets:

#### 3. `DATABASE_URL_PRODUCTION`
```
postgresql://pokeradmin:PASSWORD@poker-db-demo.postgres.database.azure.com/pokerapp?sslmode=require
```

#### 4. `AZURE_STATIC_WEB_APPS_API_TOKEN`
```
<long token from credentials file>
```

**Total Secrets** (should have 4):
- ✅ `AZURE_CREDENTIALS`
- ✅ `ANTHROPIC_API_KEY`
- ✅ `DATABASE_URL_PRODUCTION`
- ✅ `AZURE_STATIC_WEB_APPS_API_TOKEN`

---

## Step 5: Run Database Migration (5 minutes)

Create the database tables.

### In GitHub:

1. Go to **Actions** tab
2. Click **"Database Migration"** workflow
3. Click **"Run workflow"** dropdown
4. Fill in:
   - **environment**: Select `production`
   - **confirm**: Type `migrate`
5. Click **"Run workflow"**

This creates the 4 tables: `users`, `games`, `hands`, `analysis_cache`.

---

## Step 6: Deploy Code (Automatic)

Now that Azure is set up, deployments are automatic!

### Deploy Backend:

```bash
git add backend/
git commit -m "Update backend"
git push origin main
```

GitHub Actions will:
1. Run tests
2. Create deployment package
3. Deploy to Azure App Service
4. Verify deployment

**Timeline**: 3-5 minutes

### Deploy Frontend:

```bash
git add frontend/
git commit -m "Update frontend"
git push origin main
```

GitHub Actions will:
1. Run linter
2. Build Next.js app
3. Deploy to Azure Static Web App

**Timeline**: 2-4 minutes

---

## Workflow Reference

### 1. Deploy Backend to Production

**File**: `.github/workflows/deploy-backend-production.yml`

**Triggers**:
- Auto: Push to `main` (if `backend/**` changed)
- Manual: Actions tab → Deploy Backend → Run workflow

**Steps**:
1. Checkout code
2. Run tests (pytest with coverage)
3. Create deployment package (zip with dependencies)
4. Deploy to Azure App Service
5. Verify health endpoint

**Duration**: ~3-5 minutes

---

### 2. Deploy Frontend to Production

**File**: `.github/workflows/deploy-frontend-production.yml`

**Triggers**:
- Auto: Push to `main` (if `frontend/**` changed)
- Manual: Actions tab → Deploy Frontend → Run workflow

**Steps**:
1. Checkout code
2. Install npm dependencies
3. Run linter
4. Build Next.js app (static export)
5. Deploy to Azure Static Web App

**Duration**: ~2-4 minutes

---

### 3. Database Migration

**File**: `.github/workflows/database-migration.yml`

**Triggers**:
- Manual only (for safety)

**Steps**:
1. Validate confirmation ("migrate")
2. Show pending migrations
3. Run `alembic upgrade head`
4. Verify current version

**When to use**:
- After adding new migration files
- Initial setup (Step 5 above)
- When database schema changes

**Duration**: ~1-2 minutes

---

### 4. Test Suite

**File**: `.github/workflows/test-suite.yml`

**Triggers**:
- Auto: Pull requests to `main`
- Auto: Push to `main`
- Manual: Actions tab → Test Suite → Run workflow

**Steps**:
1. **Backend Tests**:
   - Run pytest with coverage
   - Generate coverage report
   - Upload artifacts

2. **Frontend Tests**:
   - Run ESLint
   - Run TypeScript type check
   - Build Next.js app

3. **Integration Tests**:
   - Start PostgreSQL
   - Run database migrations
   - Start backend server
   - Test API endpoints (register, login, create game)

4. **Security Scan**:
   - Scan for vulnerabilities (Trivy)
   - Check for accidentally committed secrets

**Duration**: ~5-8 minutes

---

### 5. Azure Initial Setup

**File**: `.github/workflows/azure-setup.yml`

**Triggers**:
- Manual only (run once)

**Steps**:
1. Validate confirmation
2. Generate secure passwords
3. Create Azure resources
4. Configure environment variables
5. Output credentials

**When to use**:
- Initial deployment (Step 3 above)
- Creating new environments (staging, etc.)

**Duration**: ~10-15 minutes

---

## Monitoring Deployments

### View Workflow Runs

Go to GitHub repo → **Actions** tab

You'll see:
- ✅ Green checkmark = Success
- ❌ Red X = Failed
- 🟡 Yellow circle = In progress

### View Logs

1. Click on a workflow run
2. Click on a job (e.g., "Deploy to Azure")
3. Expand steps to see detailed logs

### Common Issues

#### "Invalid AZURE_CREDENTIALS"
- Check that you pasted the full JSON (all fields)
- Verify service principal has Contributor role

#### "Database connection failed"
- Check that DATABASE_URL_PRODUCTION secret is correct
- Verify PostgreSQL firewall allows Azure services

#### "Tests failed"
- Check test logs for specific failures
- Run tests locally: `cd backend && pytest tests/ -v`

#### "Static Web App deployment failed"
- Check that AZURE_STATIC_WEB_APPS_API_TOKEN is correct
- Verify frontend builds locally: `cd frontend && npm run build`

---

## Manual Deployment (Backup)

If GitHub Actions fails, you can deploy manually:

### Backend:
```bash
cd backend
zip -r ../backend.zip .
az webapp deploy \
  --name poker-api-demo \
  --resource-group poker-demo-rg \
  --src-path ../backend.zip \
  --type zip
```

### Frontend:
```bash
cd frontend
npm run build
az staticwebapp deploy \
  --name poker-web-demo \
  --resource-group poker-demo-rg \
  --app-location ./out
```

---

## Environment Variables Reference

### Backend (Azure App Service)

| Variable | Value | Source |
|----------|-------|--------|
| `ENVIRONMENT` | `production` | Set by workflow |
| `TEST_MODE` | `0` | Set by workflow |
| `DATABASE_URL` | Connection string | Azure Setup workflow |
| `JWT_SECRET` | Random 64-char hex | Azure Setup workflow |
| `ANTHROPIC_API_KEY` | Your API key | GitHub secret |
| `PYTHONUNBUFFERED` | `1` | Set by workflow |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Set by workflow |
| `WEBSITES_PORT` | `8000` | Set by workflow |

### Frontend (Build-time)

| Variable | Value | Set in |
|----------|-------|--------|
| `NEXT_PUBLIC_API_URL` | `https://poker-api-demo.azurewebsites.net` | Workflow YAML |
| `NEXT_PUBLIC_ENVIRONMENT` | `production` | Workflow YAML |

---

## Cost of CI/CD

GitHub Actions pricing:

| Plan | Free Minutes/Month | Cost After |
|------|-------------------|------------|
| Public repo | Unlimited | Free |
| Private repo | 2,000 minutes | $0.008/minute |

**Estimated usage**:
- Backend deploy: 5 minutes
- Frontend deploy: 3 minutes
- Test suite: 8 minutes
- Database migration: 2 minutes

**Per deployment**: ~18 minutes total

**Example**:
- 10 deploys/month × 18 min = 180 minutes
- Well within free tier (2,000 minutes)

---

## Security Best Practices

### ✅ Do's:
- ✅ Store ALL secrets in GitHub Secrets (never commit)
- ✅ Use `::add-mask::` in workflows for sensitive output
- ✅ Require manual confirmation for destructive operations
- ✅ Run security scans on every PR
- ✅ Limit workflow permissions to minimum required
- ✅ Review workflow runs regularly

### ❌ Don'ts:
- ❌ Never commit `.env` files
- ❌ Never echo secrets in logs
- ❌ Never use `--no-verify` for migrations
- ❌ Never skip tests before deploy
- ❌ Never give workflows write access unless needed

---

## Rollback Procedure

If a deployment breaks production:

### Option 1: Revert Git Commit
```bash
git revert HEAD
git push origin main
# Triggers automatic redeploy
```

### Option 2: Manual Rollback
```bash
# Find previous working deployment
az webapp deployment list \
  --name poker-api-demo \
  --resource-group poker-demo-rg

# Rollback to specific deployment
az webapp deployment source show \
  --name poker-api-demo \
  --resource-group poker-demo-rg \
  --deployment-id <id>
```

### Option 3: Emergency Manual Deploy
```bash
# Deploy last known good version
git checkout <working-commit>
cd backend && zip -r ../backend.zip .
az webapp deploy --name poker-api-demo --src-path ../backend.zip --type zip
```

---

## Adding Staging Environment

To add a staging environment later:

1. **Duplicate Azure Setup workflow** with `-staging` suffix for resource names
2. **Add staging secrets** to GitHub
3. **Create staging branch** protection rules
4. **Update workflows** to deploy to staging on PR merge

Estimated time: 2 hours
Additional cost: ~$27/month

---

## Troubleshooting

### Deployment stuck at "Validating"

**Solution**: Check App Service logs
```bash
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg
```

### "Module not found" errors after deployment

**Cause**: Missing dependency in `requirements.txt`

**Solution**:
1. Add to `requirements.txt`
2. Test locally: `pip install -r requirements.txt`
3. Push to trigger redeploy

### Database connection timeout

**Cause**: PostgreSQL firewall blocking Azure services

**Solution**:
```bash
az postgres flexible-server firewall-rule list \
  --name poker-db-demo \
  --resource-group poker-demo-rg

# Add rule if needed
az postgres flexible-server firewall-rule create \
  --name poker-db-demo \
  --resource-group poker-demo-rg \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Static Web App shows 404

**Cause**: Build output directory mismatch

**Solution**: Verify `output_location` in workflow matches Next.js export directory (`out`)

---

## Next Steps

After CI/CD is set up:

1. ✅ **Push a test commit** to verify deployments work
2. ✅ **Monitor first deployment** (don't walk away)
3. ✅ **Test the deployed app** (register, play game, check history)
4. ✅ **Set up branch protection** (require PR reviews)
5. ✅ **Configure notifications** (Slack/Discord for failed deployments)

---

## Support

**Workflow fails**:
- Check workflow logs in GitHub Actions
- Search error message in documentation
- Check Azure Portal for resource status

**Azure issues**:
- Check Application Insights logs
- Check App Service diagnostics
- Verify environment variables are set

**Database issues**:
- Connect with psql to test: `psql "$DATABASE_URL"`
- Check migrations: `alembic current`
- Review PostgreSQL logs in Azure Portal

---

**Document Version**: 1.0
**Last Updated**: 2026-01-12
**Status**: Ready for production use
