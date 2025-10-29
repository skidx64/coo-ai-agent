#!/bin/bash

# AWS Demo Deployment Script for Coo AI Agent
# This script builds and deploys the application to AWS with demo mode enabled

set -e  # Exit on error

echo "============================================"
echo "Coo AI Agent - AWS Demo Deployment"
echo "============================================"
echo

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "[ERROR] AWS CLI not found. Please install from https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "[ERROR] Terraform not found. Please install from https://www.terraform.io/downloads"
    exit 1
fi

# Verify AWS credentials
echo "[1/5] Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "[ERROR] AWS credentials not configured. Run: aws configure"
    exit 1
fi
echo "[OK] AWS credentials verified"
echo

# Build Lambda deployment package
echo "[2/5] Building Lambda deployment package..."
echo "This may take a few minutes..."

# Clean up previous build
rm -rf package
rm -f coo-lambda.zip

# Create package directory
mkdir -p package

# Install dependencies
echo "Installing Python dependencies..."
pip install --platform manylinux2014_x86_64 \
    --target package \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    -r requirements.txt \
    --quiet

# Create zip file with dependencies
echo "Creating deployment package..."
cd package
zip -r ../coo-lambda.zip . > /dev/null
cd ..

# Add source code
zip -r coo-lambda.zip src/ > /dev/null

if [ ! -f coo-lambda.zip ]; then
    echo "[ERROR] Failed to create deployment package"
    exit 1
fi

echo "[OK] Lambda package created: coo-lambda.zip"
echo

# Initialize Terraform
echo "[3/5] Initializing Terraform..."
cd terraform
terraform init -input=false

echo "[OK] Terraform initialized"
echo

# Plan deployment
echo "[4/5] Planning deployment..."
terraform plan -out=tfplan -input=false

echo "[OK] Deployment plan created"
echo

# Apply deployment
echo "[5/5] Deploying to AWS..."
echo "This will create AWS resources (Lambda, API Gateway, IAM roles, etc.)"
echo

read -p "Continue with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    cd ..
    exit 0
fi

terraform apply -input=false tfplan

echo
echo "============================================"
echo "[SUCCESS] Deployment Complete!"
echo "============================================"
echo

# Get outputs
echo "Retrieving API Gateway URL..."
API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")

if [ -n "$API_URL" ]; then
    echo
    echo "API Gateway URL: $API_URL"
    echo
    echo "Test with:"
    echo "curl $API_URL/health"
    echo
else
    echo "[WARN] Could not retrieve API Gateway URL"
    echo "Run: terraform output"
fi

echo "Demo Configuration:"
echo "- Auth: BYPASSED"
echo "- Family ID: 1"
echo "- Parent 1: Sarah Johnson (+15555550001)"
echo "- Parent 2: Michael Johnson (+15555550002)"
echo "- Child 1: Emma Johnson (3 years old)"
echo "- Child 2: Noah Johnson (6 months old)"
echo
echo "Next steps:"
echo "1. Test health endpoint: curl $API_URL/health"
echo "2. Test AI endpoint: See AWS_DEMO_DEPLOYMENT.md"
echo "3. Check logs: aws logs tail /aws/lambda/coo-api-handler-demo --follow"
echo

cd ..
