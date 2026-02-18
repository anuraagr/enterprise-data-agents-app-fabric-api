# Azure Container Apps Deployment Script
# Run this after setting your variables

# Configuration - UPDATE THESE
$RESOURCE_GROUP = "rg-synthea-agent"
$LOCATION = "eastus"
$RANDOM_SUFFIX = (Get-Random -Minimum 1000 -Maximum 9999)
$ACR_NAME = "syntheaagentacr$RANDOM_SUFFIX"  # Must be globally unique, lowercase
$APP_NAME = "synthea-healthcare-agent"
$ENVIRONMENT_NAME = "synthea-agent-env"

# Load environment variables from src/.env
Write-Host "=== Loading Environment Variables ===" -ForegroundColor Cyan
$ENV_FILE = Join-Path $PSScriptRoot "src\.env"
if (Test-Path $ENV_FILE) {
    Get-Content $ENV_FILE | ForEach-Object {
        if ($_ -match '^\s*([A-Z][A-Z0-9_]*)\s*=\s*"?([^"]*)"?\s*$') {
            Set-Variable -Name $matches[1] -Value $matches[2] -Scope Script
        }
    }
    Write-Host "Loaded environment from: $ENV_FILE" -ForegroundColor Green
} else {
    Write-Host "WARNING: .env file not found at $ENV_FILE" -ForegroundColor Yellow
}

Write-Host "=== Step 1: Create Resource Group ===" -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location $LOCATION

Write-Host "=== Step 2: Create Azure Container Registry ===" -ForegroundColor Cyan
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

Write-Host "=== Step 3: Build and Push Docker Image ===" -ForegroundColor Cyan
az acr build --registry $ACR_NAME --image synthea-agent:latest .

Write-Host "=== Step 4: Create Container Apps Environment ===" -ForegroundColor Cyan
az containerapp env create --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION

Write-Host "=== Step 5: Get ACR Credentials ===" -ForegroundColor Cyan
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
$ACR_SERVER = "$ACR_NAME.azurecr.io"

Write-Host "=== Step 6: Deploy Container App with Managed Identity ===" -ForegroundColor Cyan
az containerapp create `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --environment $ENVIRONMENT_NAME `
    --image "$ACR_SERVER/synthea-agent:latest" `
    --registry-server $ACR_SERVER `
    --registry-username $ACR_NAME `
    --registry-password $ACR_PASSWORD `
    --target-port 8501 `
    --ingress external `
    --cpu 1 --memory 2Gi `
    --min-replicas 0 `
    --max-replicas 3 `
    --system-assigned `
    --env-vars `
        "PROJECT_CONNECTION_STRING=$PROJECT_CONNECTION_STRING" `
        "FABRIC_CONNECTION_NAME=$FABRIC_CONNECTION_NAME" `
        "FABRIC_CLIENT_ID=$FABRIC_CLIENT_ID" `
        "FABRIC_CLIENT_SECRET=secretref:fabric-client-secret" `
        "FABRIC_TENANT_ID=$FABRIC_TENANT_ID" `
        "FABRIC_WORKSPACE_ID=$FABRIC_WORKSPACE_ID" `
        "FABRIC_ARTIFACT_ID=$FABRIC_ARTIFACT_ID" `
    --secrets "fabric-client-secret=$FABRIC_CLIENT_SECRET"

Write-Host "=== Step 7: Get App URL ===" -ForegroundColor Cyan
$APP_URL = az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "Your app is deployed at: https://$APP_URL" -ForegroundColor Green

Write-Host "=== Step 8: Assign Cognitive Services Role to Managed Identity ===" -ForegroundColor Cyan
$IDENTITY_PRINCIPAL_ID = az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "identity.principalId" -o tsv
az role assignment create --assignee $IDENTITY_PRINCIPAL_ID --role "Cognitive Services OpenAI User" --scope "/subscriptions/520c58eb-9501-4b21-adc0-2a5958398429"

Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "App URL: https://$APP_URL"
