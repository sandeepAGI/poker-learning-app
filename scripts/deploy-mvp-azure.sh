#!/bin/bash
# MVP Azure Deployment Script
# Estimated time: 4 hours (first time), 1 hour (subsequent deploys)

set -e  # Exit on error

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Poker Learning App - MVP Azure Deployment ===${NC}"
echo ""

# Configuration
RESOURCE_GROUP="poker-demo-rg"
LOCATION="eastus"
DB_NAME="poker-db-demo"
DB_ADMIN="pokeradmin"
BACKEND_APP="poker-api-demo"
FRONTEND_APP="poker-web-demo"
APP_SERVICE_PLAN="poker-plan"

# Generate random password for database
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -hex 32)

echo -e "${GREEN}Step 1: Creating Resource Group${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

echo ""
echo -e "${GREEN}Step 2: Creating PostgreSQL Database${NC}"
echo "This will take 5-10 minutes..."
az postgres flexible-server create \
  --name $DB_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $DB_ADMIN \
  --admin-password "$DB_PASSWORD" \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0 \
  --yes

# Create database
echo "Creating poker database..."
az postgres flexible-server db create \
  --server-name $DB_NAME \
  --resource-group $RESOURCE_GROUP \
  --database-name pokerapp

# Get connection string
DB_HOST="${DB_NAME}.postgres.database.azure.com"
DATABASE_URL="postgresql://${DB_ADMIN}:${DB_PASSWORD}@${DB_HOST}/pokerapp?sslmode=require"

echo ""
echo -e "${GREEN}Step 3: Creating App Service Plan${NC}"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux

echo ""
echo -e "${GREEN}Step 4: Creating Backend App Service${NC}"
az webapp create \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.12"

# Configure backend
echo "Configuring backend environment variables..."
az webapp config appsettings set \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    ENVIRONMENT=production \
    TEST_MODE=0 \
    DATABASE_URL="$DATABASE_URL" \
    JWT_SECRET="$JWT_SECRET" \
    ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-CHANGE_THIS}" \
    PYTHONUNBUFFERED=1 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000

# Enable WebSockets
az webapp config set \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --web-sockets-enabled true

echo ""
echo -e "${GREEN}Step 5: Creating Frontend Static Web App${NC}"
az staticwebapp create \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get backend URL
BACKEND_URL="https://${BACKEND_APP}.azurewebsites.net"

echo ""
echo -e "${GREEN}Step 6: Running Database Migrations${NC}"
echo "You'll need to run this manually from your local machine:"
echo ""
echo "  export DATABASE_URL='$DATABASE_URL'"
echo "  cd backend && alembic upgrade head"
echo ""

echo ""
echo -e "${BLUE}=== Deployment Complete! ===${NC}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: https://${FRONTEND_APP}.azurestaticapps.net (will be shown after first deploy)"
echo ""
echo -e "${RED}IMPORTANT: Save these credentials securely!${NC}"
echo ""
echo "Database:"
echo "  Host: $DB_HOST"
echo "  Username: $DB_ADMIN"
echo "  Password: $DB_PASSWORD"
echo "  Database: pokerapp"
echo "  Connection String: $DATABASE_URL"
echo ""
echo "JWT Secret: $JWT_SECRET"
echo ""
echo "Next steps:"
echo "1. Set ANTHROPIC_API_KEY:"
echo "   az webapp config appsettings set --name $BACKEND_APP --resource-group $RESOURCE_GROUP --settings ANTHROPIC_API_KEY='your-key-here'"
echo ""
echo "2. Run database migrations (see above)"
echo ""
echo "3. Deploy backend:"
echo "   cd backend && zip -r ../backend.zip . && az webapp deploy --name $BACKEND_APP --resource-group $RESOURCE_GROUP --src-path ../backend.zip --type zip"
echo ""
echo "4. Deploy frontend:"
echo "   cd frontend && npm run build"
echo "   az staticwebapp deploy --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --app-location ./out"
echo ""
echo "5. Update frontend .env.production:"
echo "   NEXT_PUBLIC_API_URL=$BACKEND_URL"
echo ""
echo -e "${GREEN}Estimated monthly cost: ~$27${NC}"
echo ""
