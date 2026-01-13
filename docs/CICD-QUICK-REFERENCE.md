# CI/CD Quick Reference Card

Fast reference for common GitHub Actions tasks.

---

## 🚀 Quick Start (First Time Setup)

```bash
# 1. Create Azure service principal
az ad sp create-for-rbac --name "github-poker-app" --role contributor --scopes /subscriptions/YOUR_SUB_ID --sdk-auth

# 2. Add to GitHub Secrets (Settings → Secrets → Actions)
#    - AZURE_CREDENTIALS (paste full JSON)
#    - ANTHROPIC_API_KEY

# 3. Run "Azure Initial Setup" workflow in GitHub Actions
#    - Input your Anthropic API key
#    - Type "setup" to confirm

# 4. Download credentials artifact, add to GitHub Secrets:
#    - DATABASE_URL_PRODUCTION
#    - AZURE_STATIC_WEB_APPS_API_TOKEN

# 5. Run "Database Migration" workflow
#    - Type "migrate" to confirm

# 6. Push code to deploy!
git push origin main
```

**Total time**: 30-40 minutes

---

## 📋 GitHub Secrets Checklist

Go to Settings → Secrets and variables → Actions

- [ ] `AZURE_CREDENTIALS` - Service principal JSON
- [ ] `ANTHROPIC_API_KEY` - API key from Anthropic console
- [ ] `DATABASE_URL_PRODUCTION` - PostgreSQL connection string
- [ ] `AZURE_STATIC_WEB_APPS_API_TOKEN` - Static Web App deployment token

---

## 🔄 Common Workflows

### Deploy Backend
```bash
# Auto-deploy on push
git add backend/
git commit -m "Update backend"
git push origin main

# Or manual trigger
# GitHub → Actions → Deploy Backend → Run workflow
```

### Deploy Frontend
```bash
# Auto-deploy on push
git add frontend/
git commit -m "Update frontend"
git push origin main

# Or manual trigger
# GitHub → Actions → Deploy Frontend → Run workflow
```

### Run Database Migration
```bash
# Manual trigger only (for safety)
# GitHub → Actions → Database Migration → Run workflow
# Type "migrate" to confirm
```

### Run Tests
```bash
# Auto-run on PR or push to main

# Or manual trigger
# GitHub → Actions → Test Suite → Run workflow
```

---

## 🛠️ Manual Deployment (If CI/CD Fails)

### Backend
```bash
cd backend
zip -r ../backend.zip . -x "tests/*" -x "*.pyc" -x "__pycache__/*"
az webapp deploy --name poker-api-demo --resource-group poker-demo-rg --src-path ../backend.zip --type zip
```

### Frontend
```bash
cd frontend
npm run build
az staticwebapp deploy --name poker-web-demo --resource-group poker-demo-rg --app-location ./out
```

### Database
```bash
export DATABASE_URL="<from GitHub secrets>"
cd backend
alembic upgrade head
```

---

## 🐛 Debugging Failed Deployments

### Check Workflow Logs
```bash
# In GitHub
# Actions tab → Click failed run → Click job → Expand steps
```

### Check Azure Logs
```bash
# Backend logs (streaming)
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg

# Or view in Azure Portal
# App Service → Log stream
```

### Test Locally
```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

### Verify Deployment
```bash
# Health check
curl https://poker-api-demo.azurewebsites.net/health

# Test auth
curl -X POST https://poker-api-demo.azurewebsites.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

---

## 🔐 Security Commands

### Check for Secrets
```bash
# Never commit these files
.env
.env.local
.env.production
**/*.pem
**/*.key
credentials.txt

# Search for accidentally committed secrets
git log -p | grep -i "sk-ant-api"
```

### Rotate Secrets
```bash
# 1. Generate new JWT secret
openssl rand -hex 32

# 2. Update in Azure
az webapp config appsettings set \
  --name poker-api-demo \
  --resource-group poker-demo-rg \
  --settings JWT_SECRET="<new-secret>"

# 3. Update in GitHub Secrets (if needed)
```

---

## 📊 Monitoring

### View App Insights
```bash
# In Azure Portal
# Application Insights → Logs

# Query recent errors
traces
| where severityLevel >= 3
| order by timestamp desc
| take 50
```

### Check Resource Usage
```bash
# Database size
az postgres flexible-server show \
  --name poker-db-demo \
  --resource-group poker-demo-rg \
  --query "storage"

# App Service metrics
az monitor metrics list \
  --resource poker-api-demo \
  --resource-group poker-demo-rg \
  --resource-type "Microsoft.Web/sites" \
  --metric CpuTime,MemoryWorkingSet
```

### Cost Analysis
```bash
# In Azure Portal
# Cost Management → Cost Analysis
# Filter: Resource Group = poker-demo-rg

# Expected: ~$27/month
# Breakdown: $13 backend + $14 database
```

---

## 🔄 Rollback Procedures

### Rollback via Git
```bash
# Find last working commit
git log --oneline

# Revert to it
git revert <commit-hash>
git push origin main

# Auto-triggers redeploy
```

### Rollback Database (Emergency)
```bash
export DATABASE_URL="<from secrets>"
cd backend

# List migrations
alembic history

# Downgrade to previous
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision>
```

### Emergency Stop
```bash
# Stop backend (prevents new requests)
az webapp stop --name poker-api-demo --resource-group poker-demo-rg

# Fix issue, then restart
az webapp start --name poker-api-demo --resource-group poker-demo-rg
```

---

## 📦 Adding New Dependencies

### Backend (Python)
```bash
# 1. Add to requirements.txt
echo "redis>=5.0.0" >> backend/requirements.txt

# 2. Test locally
cd backend && pip install -r requirements.txt

# 3. Commit and push (auto-deploys)
git add backend/requirements.txt
git commit -m "Add redis dependency"
git push origin main
```

### Frontend (npm)
```bash
# 1. Install package
cd frontend
npm install @tanstack/react-query

# 2. Test build
npm run build

# 3. Commit and push (auto-deploys)
git add frontend/package*.json
git commit -m "Add react-query"
git push origin main
```

---

## 🗄️ Database Operations

### Run New Migration
```bash
# 1. Create migration locally
cd backend
alembic revision -m "add_user_preferences_table"

# 2. Edit migration file
# backend/alembic/versions/XXX_add_user_preferences_table.py

# 3. Test locally
alembic upgrade head

# 4. Commit
git add backend/alembic/versions/
git commit -m "Add user preferences table"
git push origin main

# 5. Run in production
# GitHub → Actions → Database Migration → Run workflow
```

### Backup Database
```bash
# Export schema + data
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql

# Or just schema
pg_dump "$DATABASE_URL" --schema-only > schema.sql
```

### Restore Database
```bash
# Restore from backup
psql "$DATABASE_URL" < backup_20260112.sql

# Or just run specific SQL
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM users;"
```

---

## 🧪 Testing

### Run Tests Locally
```bash
# Backend
cd backend
PYTHONPATH=. pytest tests/ -v --cov=.

# Frontend
cd frontend
npm run lint
npm run type-check
npm run build
```

### Test with Production Environment
```bash
# Set production env vars
export DATABASE_URL="<production-url>"
export ANTHROPIC_API_KEY="<real-key>"
export JWT_SECRET="<production-secret>"

# Run backend
cd backend
python main.py

# Test in another terminal
curl http://localhost:8000/health
```

---

## 🚨 Emergency Procedures

### Production Down
```bash
# 1. Check health
curl https://poker-api-demo.azurewebsites.net/health

# 2. Check logs
az webapp log tail --name poker-api-demo --resource-group poker-demo-rg

# 3. Restart app
az webapp restart --name poker-api-demo --resource-group poker-demo-rg

# 4. If still down, rollback
git revert HEAD && git push origin main
```

### Database Connection Issues
```bash
# 1. Test connection
psql "$DATABASE_URL" -c "SELECT 1;"

# 2. Check firewall
az postgres flexible-server firewall-rule list \
  --name poker-db-demo \
  --resource-group poker-demo-rg

# 3. Add Azure IPs if needed
az postgres flexible-server firewall-rule create \
  --name poker-db-demo \
  --resource-group poker-demo-rg \
  --rule-name AllowAzure \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Out of Money (Cost Overrun)
```bash
# Check current spend
az consumption usage list \
  --start-date $(date -d "30 days ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)

# Stop everything (last resort)
az group delete --name poker-demo-rg --yes --no-wait

# Expected cost: $27/month
# If higher, check for:
# - Accidental premium tier
# - Excessive API calls
# - Storage overage
```

---

## 📞 Support Resources

### Azure CLI Help
```bash
az webapp --help
az postgres flexible-server --help
az staticwebapp --help
```

### Logs
- **Backend**: App Service → Log stream
- **Database**: PostgreSQL → Logs
- **Frontend**: Static Web App → Monitoring
- **CI/CD**: GitHub → Actions → Workflow runs

### Documentation
- **GitHub Actions**: `docs/GITHUB-ACTIONS-SETUP.md`
- **MVP Deployment**: `docs/MVP-DEPLOYMENT-CHECKLIST.md`
- **Full vs MVP**: `docs/MVP-VS-FULL-COMPARISON.md`

---

## 💡 Pro Tips

### Speed Up Deployments
```bash
# Use caching in workflows (already configured)
# - Python packages cached by setup-python
# - npm packages cached by setup-node

# Skip tests (emergency only)
# Edit workflow, comment out test job
```

### Debug Failed Tests
```bash
# Run tests with more detail
cd backend
pytest tests/ -vv --tb=long

# Run specific test
pytest tests/test_auth.py::test_register -vv

# See print statements
pytest tests/ -v -s
```

### Quick Status Check
```bash
# One command to check everything
echo "Backend:" && curl -s https://poker-api-demo.azurewebsites.net/health | jq .
echo "Database:" && psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM users;"
echo "Recent deploys:" && az webapp deployment list --name poker-api-demo --resource-group poker-demo-rg --query "[0].{date:startTime,status:status}" -o table
```

---

## 📅 Maintenance Schedule

### Daily
- Check GitHub Actions for failed workflows
- Monitor Application Insights for errors

### Weekly
- Review cost in Azure Portal
- Check database size growth
- Test backup/restore procedure

### Monthly
- Rotate JWT_SECRET (optional)
- Review security scan results
- Update dependencies (`npm audit`, `pip check`)

---

**Quick Links**:
- [Full Setup Guide](./GITHUB-ACTIONS-SETUP.md)
- [MVP Checklist](./MVP-DEPLOYMENT-CHECKLIST.md)
- [Troubleshooting](./GITHUB-ACTIONS-SETUP.md#troubleshooting)

**Keep this file handy** - bookmark it or print as PDF!
