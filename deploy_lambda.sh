#!/bin/bash
# Quick Lambda deployment script

echo "🚀 Starting Lambda deployment..."

# Clean up previous builds
rm -rf lambda-package coo-lambda.zip

# Create deployment package
echo "📦 Creating deployment package..."
mkdir lambda-package
cd lambda-package

# Install dependencies
echo "⬇️ Installing dependencies (this may take 5-10 minutes)..."
pip install -r ../requirements.txt -t . \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --quiet

# Copy source code
echo "📋 Copying source code..."
cp -r ../src .
cp -r ../frontend .
cp -r ../knowledge-base .

# Copy vector database if it exists
if [ -d "../vector_db" ]; then
    echo "📊 Copying vector database..."
    cp -r ../vector_db .
else
    echo "⚠️  No vector_db found - RAG will use empty database"
fi

# Create zip file (exclude unnecessary files)
echo "🗜️ Creating zip file..."
zip -r ../coo-lambda.zip . \
    -x "*.pyc" \
    -x "*__pycache__*" \
    -x "*.dist-info*" \
    -x "*.egg-info*" \
    -q

cd ..

# Get zip file size
SIZE=$(du -h coo-lambda.zip | cut -f1)
echo "✅ Deployment package created: coo-lambda.zip ($SIZE)"

echo ""
echo "📤 Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Find function: coo-api-handler"
echo "3. Upload coo-lambda.zip"
echo "4. Wait for upload to complete"
echo "5. Test your deployment!"
echo ""
echo "🔗 Deployment guide: BUDGET_AWS_DEPLOYMENT.md"
