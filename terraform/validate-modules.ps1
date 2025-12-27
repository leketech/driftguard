# Validation script for DriftGuard Terraform modules

Write-Host "Validating DriftGuard Terraform modules..." -ForegroundColor Green

# Validate the shared IAM policy module
Write-Host "Validating shared IAM policy module..." -ForegroundColor Yellow
Set-Location -Path "modules/iam-policy"
terraform init -backend=false
$Result = terraform validate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Shared IAM policy module validation passed" -ForegroundColor Green
} else {
    Write-Host "❌ Shared IAM policy module validation failed" -ForegroundColor Red
    exit 1
}
Set-Location -Path "../.."

# Validate the IAM module
Write-Host "Validating IAM module..." -ForegroundColor Yellow
Set-Location -Path "iam"
terraform init -backend=false
$Result = terraform validate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ IAM module validation passed" -ForegroundColor Green
} else {
    Write-Host "❌ IAM module validation failed" -ForegroundColor Red
    exit 1
}
Set-Location -Path ".."

# Validate the OIDC module
Write-Host "Validating OIDC module..." -ForegroundColor Yellow
Set-Location -Path "oidc"
terraform init -backend=false
$Result = terraform validate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ OIDC module validation passed" -ForegroundColor Green
} else {
    Write-Host "❌ OIDC module validation failed" -ForegroundColor Red
    exit 1
}
Set-Location -Path ".."

Write-Host "✅ All DriftGuard Terraform modules validated successfully!" -ForegroundColor Green