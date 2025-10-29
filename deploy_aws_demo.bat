@echo off
REM AWS Demo Deployment Script for Coo AI Agent
REM This script builds and deploys the application to AWS with demo mode enabled

echo ============================================
echo Coo AI Agent - AWS Demo Deployment
echo ============================================
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AWS CLI not found. Please install from https://aws.amazon.com/cli/
    pause
    exit /b 1
)

REM Check if Terraform is installed
where terraform >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Terraform not found. Please install from https://www.terraform.io/downloads
    pause
    exit /b 1
)

REM Verify AWS credentials
echo [1/5] Verifying AWS credentials...
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AWS credentials not configured. Run: aws configure
    pause
    exit /b 1
)
echo [OK] AWS credentials verified
echo.

REM Build Lambda deployment package
echo [2/5] Building Lambda deployment package...
echo This may take a few minutes...

REM Clean up previous build
if exist package rmdir /s /q package
if exist coo-lambda.zip del /f /q coo-lambda.zip

REM Create package directory
mkdir package

REM Install dependencies
echo Installing Python dependencies...
pip install --platform manylinux2014_x86_64 --target package --implementation cp --python-version 3.11 --only-binary=:all: -r requirements.txt --quiet

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Create zip file with dependencies
echo Creating deployment package...
cd package
powershell -Command "Compress-Archive -Path * -DestinationPath ..\coo-lambda.zip -Force"
cd ..

REM Add source code
powershell -Command "Compress-Archive -Path src\* -Update -DestinationPath coo-lambda.zip"

if not exist coo-lambda.zip (
    echo [ERROR] Failed to create deployment package
    pause
    exit /b 1
)

echo [OK] Lambda package created: coo-lambda.zip
echo.

REM Initialize Terraform
echo [3/5] Initializing Terraform...
cd terraform
terraform init -input=false

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Terraform initialization failed
    cd ..
    pause
    exit /b 1
)
echo [OK] Terraform initialized
echo.

REM Plan deployment
echo [4/5] Planning deployment...
terraform plan -out=tfplan -input=false

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Terraform plan failed
    cd ..
    pause
    exit /b 1
)
echo [OK] Deployment plan created
echo.

REM Apply deployment
echo [5/5] Deploying to AWS...
echo This will create AWS resources (Lambda, API Gateway, IAM roles, etc.)
echo.
set /p CONFIRM="Continue with deployment? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Deployment cancelled
    cd ..
    pause
    exit /b 0
)

terraform apply -input=false tfplan

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Deployment failed
    cd ..
    pause
    exit /b 1
)

echo.
echo ============================================
echo [SUCCESS] Deployment Complete!
echo ============================================
echo.

REM Get outputs
echo Retrieving API Gateway URL...
for /f "delims=" %%i in ('terraform output -raw api_gateway_url 2^>nul') do set API_URL=%%i

if defined API_URL (
    echo.
    echo API Gateway URL: %API_URL%
    echo.
    echo Test with:
    echo curl %API_URL%/health
    echo.
) else (
    echo [WARN] Could not retrieve API Gateway URL
    echo Run: terraform output
)

echo Demo Configuration:
echo - Auth: BYPASSED
echo - Family ID: 1
echo - Parent 1: Sarah Johnson (+15555550001)
echo - Parent 2: Michael Johnson (+15555550002)
echo - Child 1: Emma Johnson (3 years old)
echo - Child 2: Noah Johnson (6 months old)
echo.
echo Next steps:
echo 1. Test health endpoint: curl %API_URL%/health
echo 2. Test AI endpoint: See AWS_DEMO_DEPLOYMENT.md
echo 3. Check logs: aws logs tail /aws/lambda/coo-api-handler-demo --follow
echo.

cd ..
pause
