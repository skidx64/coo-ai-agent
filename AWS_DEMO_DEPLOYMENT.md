# AWS Demo Deployment Guide

This guide walks you through deploying the Coo AI Agent to AWS with authentication bypassed and pre-populated demo data.

## Demo Configuration

**Pre-populated Users:**
- **Parent 1 (Mom):** Sarah Johnson - Phone: +15555550001
- **Parent 2 (Dad):** Michael Johnson - Phone: +15555550002
- **Child 1:** Emma Johnson - 3 years old (female)
- **Child 2:** Noah Johnson - 6 months old (male)

**Authentication:** BYPASSED - No login/signup required
**Subscription Tier:** FAMILY (1 year trial)

---

## Prerequisites

1. **AWS Account** with Administrator access
2. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```
3. **Terraform** installed (v1.0+)
   ```bash
   terraform --version
   ```
4. **Python 3.11** installed locally
5. **Bedrock Access** enabled in your AWS account
   - Go to AWS Console → Bedrock → Model access
   - Enable: `Claude 3.5 Sonnet v2` and `Nova Lite`

---

## Step 1: Verify AWS Credentials

```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## Step 2: Build Lambda Deployment Package

### Windows (PowerShell)

```powershell
# Navigate to project root
cd C:\Users\SCA33\Desktop\PersonalProjects\coo

# Install dependencies with Lambda-compatible binaries
pip install --platform manylinux2014_x86_64 --target ./package --implementation cp --python-version 3.11 --only-binary=:all: -r requirements.txt

# Create deployment package
cd package
Compress-Archive -Path * -DestinationPath ..\coo-lambda.zip -Force
cd ..

# Add source code
Compress-Archive -Path src\* -Update -DestinationPath coo-lambda.zip
```

### Linux/Mac

```bash
# Navigate to project root
cd ~/PersonalProjects/coo

# Create clean build directory
rm -rf package
mkdir package

# Install dependencies
pip install --platform manylinux2014_x86_64 --target ./package --implementation cp --python-version 3.11 --only-binary=:all: -r requirements.txt

# Create zip file
cd package
zip -r ../coo-lambda.zip .
cd ..

# Add source code
zip -r coo-lambda.zip src/
```

---

## Step 3: Configure Terraform Variables

The `terraform/terraform.tfvars` file has been pre-configured for demo mode:

```hcl
environment = "demo"
lambda_timeout = 60
bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
database_url = "sqlite:////tmp/coo.db"
```

**Note:** Twilio SMS is optional for testing AI functionality. Leave placeholders if not using.

---

## Step 4: Deploy with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy to AWS
terraform apply

# Type 'yes' when prompted
```

**Expected Output:**
```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

api_gateway_url = "https://abc123xyz.execute-api.us-east-1.amazonaws.com"
lambda_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:coo-api-handler-demo"
lambda_function_name = "coo-api-handler-demo"
```

**Save the `api_gateway_url` - this is your API endpoint!**

---

## Step 5: Verify Deployment

### Test Health Endpoint

```bash
curl https://YOUR_API_GATEWAY_URL/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test Demo Data Seeding

Check Lambda logs to verify demo data was created:

```bash
aws logs tail /aws/lambda/coo-api-handler-demo --follow
```

Look for:
```
[DEMO] Demo data seeded. Family ID: 1
[DEMO] Auth is BYPASSED - demo mode enabled
```

---

## Step 6: Test AI Functionality

### Option A: Using curl

**Ask a parenting question:**
```bash
curl -X POST "https://YOUR_API_GATEWAY_URL/api/ai/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo" \
  -d '{
    "question": "What are common signs of teething in a 6-month-old baby?",
    "family_id": 1,
    "child_id": 2
  }'
```

**Symptom Triage:**
```bash
curl -X POST "https://YOUR_API_GATEWAY_URL/api/ai/triage" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo" \
  -d '{
    "family_id": 1,
    "child_id": 2,
    "symptoms": "mild fever of 100.5F, fussy, drooling a lot",
    "child_age_months": 6
  }'
```

### Option B: Using Python

```python
import requests

API_URL = "https://YOUR_API_GATEWAY_URL"
HEADERS = {
    "Authorization": "Bearer demo",
    "Content-Type": "application/json"
}

# Ask a question
response = requests.post(
    f"{API_URL}/api/ai/answer",
    headers=HEADERS,
    json={
        "question": "What vaccines does a 3-year-old need?",
        "family_id": 1,
        "child_id": 1
    }
)

print(response.json())
```

---

## Step 7: Test SMS Functionality (Optional)

If you configured Twilio:

1. **Get Twilio webhook URL:**
   ```
   https://YOUR_API_GATEWAY_URL/api/sms/webhook
   ```

2. **Configure in Twilio Console:**
   - Go to Phone Numbers → Your Number → Messaging
   - Set "A MESSAGE COMES IN" webhook to your URL
   - Method: POST

3. **Send test SMS:**
   - Text your Twilio number from **+15555550001** or **+15555550002**
   - Ask: "What should I do if my baby has a fever?"

---

## Architecture Overview

```
User Request
    ↓
API Gateway (HTTPS)
    ↓
Lambda Function (FastAPI + Mangum)
    ↓
├─ Bedrock (Claude 3.5 Sonnet) - AI responses
├─ ChromaDB (in /tmp) - RAG knowledge base
└─ SQLite (in /tmp) - User data & conversations
```

---

## Environment Variables (Auto-configured)

| Variable | Value | Purpose |
|----------|-------|---------|
| `SKIP_AUTH` | `true` | Bypass login/signup |
| `DEMO_FAMILY_ID` | `1` | Default family for demo |
| `ENVIRONMENT` | `aws` | AWS-specific config |
| `AI_PROVIDER` | `bedrock` | Use AWS Bedrock |
| `RAG_PROVIDER` | `chromadb` | Local vector DB |

---

## API Endpoints Reference

### AI Endpoints (No Auth Required)

```
POST /api/ai/answer
  - Ask parenting questions
  - Body: { "question": "...", "family_id": 1 }

POST /api/ai/triage
  - Symptom triage
  - Body: { "symptoms": "...", "child_age_months": 6 }

GET /api/children?family_id=1
  - List children

GET /api/families/1
  - Get family details
```

---

## Cost Estimation

**Lambda:**
- Free tier: 1M requests/month, 400,000 GB-seconds
- After free tier: ~$0.20 per 1M requests

**Bedrock (Claude 3.5 Sonnet):**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- ~100 questions = ~$0.50

**API Gateway:**
- Free tier: 1M requests/month
- After: $1.00 per 1M requests

**Estimated monthly cost for testing: < $5**

---

## Troubleshooting

### Lambda timeout errors
```bash
# Increase timeout in terraform/terraform.tfvars
lambda_timeout = 120

# Reapply
cd terraform && terraform apply
```

### Bedrock access denied
```bash
# Check model access in AWS Console
aws bedrock list-foundation-models --region us-east-1
```

### Demo data not created
```bash
# Check Lambda logs
aws logs tail /aws/lambda/coo-api-handler-demo --follow

# Manually trigger
curl https://YOUR_API_GATEWAY_URL/
```

### Database not persisting
- SQLite in `/tmp` is ephemeral in Lambda
- For persistence, use RDS PostgreSQL (see production deployment)

---

## Cleanup

To remove all AWS resources:

```bash
cd terraform
terraform destroy
# Type 'yes' when prompted
```

---

## Next Steps

### Add Real Users
Update `src/seed_demo_data.py` with real phone numbers and redeploy.

### Enable Production Database
Replace SQLite with RDS PostgreSQL in `terraform/terraform.tfvars`:
```hcl
database_url = "postgresql://user:pass@your-rds.amazonaws.com:5432/coo"
```

### Enable Knowledge Base
Create Bedrock KB and set in `terraform.tfvars`:
```hcl
bedrock_kb_id = "YOUR_KB_ID"
```

### Remove Auth Bypass
Set in `terraform/lambda.tf`:
```hcl
SKIP_AUTH = "false"
```

---

## Support

For issues, check:
1. Lambda logs: `/aws/lambda/coo-api-handler-demo`
2. API Gateway logs in CloudWatch
3. Bedrock quotas in Service Quotas console

---

**Happy Testing!** 🚀
