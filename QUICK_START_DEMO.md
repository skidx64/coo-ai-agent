# Quick Start - AWS Demo Deployment

Deploy Coo AI Agent to AWS in 5 minutes with pre-populated demo data and no authentication required.

## TL;DR

```bash
# Windows
deploy_aws_demo.bat

# Linux/Mac
chmod +x deploy_aws_demo.sh
./deploy_aws_demo.sh
```

Then test:
```bash
curl YOUR_API_URL/health
```

---

## What's Included

**Demo Users (Auto-created):**
- 👨‍👩‍👧‍👦 2 Parents: Sarah & Michael Johnson
- 👶 2 Children: Emma (3yo) & Noah (6mo)

**Features Enabled:**
- ✅ AI Question Answering (Bedrock Claude)
- ✅ Symptom Triage
- ✅ RAG Knowledge Base (70+ medical docs)
- ✅ No Login Required (Auth bypassed)
- ✅ 1-year trial activated

**AWS Resources Created:**
- Lambda Function (FastAPI backend)
- API Gateway (HTTPS endpoint)
- CloudWatch Logs
- IAM Roles

---

## Prerequisites

Install these first:

1. [AWS CLI](https://aws.amazon.com/cli/)
2. [Terraform](https://www.terraform.io/downloads)
3. Python 3.11
4. AWS Account with Bedrock access enabled

**Enable Bedrock Models:**
```bash
# Go to AWS Console → Bedrock → Model access
# Enable: Claude 3.5 Sonnet v2, Nova Lite
```

---

## Deploy

### Windows

```powershell
# Run deployment script
.\deploy_aws_demo.bat

# Wait 5-10 minutes for deployment
# Save the API Gateway URL from output
```

### Linux/Mac

```bash
# Make script executable
chmod +x deploy_aws_demo.sh

# Run deployment
./deploy_aws_demo.sh

# Wait 5-10 minutes for deployment
# Save the API Gateway URL from output
```

---

## Test AI Functionality

Replace `YOUR_API_URL` with your API Gateway URL.

### 1. Health Check

```bash
curl https://YOUR_API_URL/health
```

Expected: `{"status":"healthy"}`

### 2. Ask a Question

```bash
curl -X POST "https://YOUR_API_URL/api/ai/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo" \
  -d '{
    "question": "What are the signs of teething in babies?",
    "family_id": 1,
    "child_id": 2
  }'
```

### 3. Symptom Triage

```bash
curl -X POST "https://YOUR_API_URL/api/ai/triage" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo" \
  -d '{
    "family_id": 1,
    "child_id": 2,
    "symptoms": "low fever, fussy, drooling",
    "child_age_months": 6
  }'
```

### 4. List Children

```bash
curl -X GET "https://YOUR_API_URL/api/children?family_id=1" \
  -H "Authorization: Bearer demo"
```

---

## View Logs

```bash
# Real-time log streaming
aws logs tail /aws/lambda/coo-api-handler-demo --follow

# Look for:
# [DEMO] Demo data seeded. Family ID: 1
# [DEMO] Auth is BYPASSED - demo mode enabled
```

---

## Cost Estimate

**Free Tier (First 12 months):**
- Lambda: 1M requests/month FREE
- API Gateway: 1M requests/month FREE
- Bedrock: Pay-as-you-go

**Estimated cost for 100 AI questions: ~$0.50**

---

## What Changed

The following modifications were made to bypass authentication and enable demo mode:

### 1. Authentication Bypass (`src/services/auth_service.py`)
```python
# Added environment variables
SKIP_AUTH = os.getenv("SKIP_AUTH", "false").lower() == "true"
DEMO_FAMILY_ID = int(os.getenv("DEMO_FAMILY_ID", "1"))

# Modified verify_token() to return mock payload when SKIP_AUTH=true
```

### 2. Demo Data Seeding (`src/seed_demo_data.py`)
- Creates 1 family with 2 parents and 2 children
- Auto-runs on Lambda startup when `SKIP_AUTH=true`

### 3. Terraform Configuration (`terraform/lambda.tf`)
```hcl
environment {
  variables = {
    SKIP_AUTH = "true"
    DEMO_FAMILY_ID = "1"
    # ... other vars
  }
}
```

### 4. Lambda Startup (`src/main.py`)
- Auto-seeds demo data on startup
- Logs demo mode status

---

## Cleanup

To remove all AWS resources and stop incurring costs:

```bash
cd terraform
terraform destroy
# Type 'yes' when prompted
```

---

## Troubleshooting

**"AWS credentials not configured"**
```bash
aws configure
# Enter Access Key ID, Secret Key, Region (us-east-1)
```

**"Bedrock access denied"**
- Go to AWS Console → Bedrock → Model access
- Enable Claude 3.5 Sonnet and Nova Lite models

**"Lambda timeout"**
- Update `lambda_timeout = 120` in `terraform/terraform.tfvars`
- Run `terraform apply`

**"Demo data not created"**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/coo-api-handler-demo --follow
```

---

## Next Steps

- 📖 Read full guide: [AWS_DEMO_DEPLOYMENT.md](AWS_DEMO_DEPLOYMENT.md)
- 🔧 Add real users: Update `src/seed_demo_data.py`
- 📱 Enable SMS: Configure Twilio in `terraform.tfvars`
- 🗄️ Use PostgreSQL: Replace SQLite with RDS
- 🔒 Enable Auth: Set `SKIP_AUTH=false` in Terraform

---

## Support

**Documentation:**
- Full deployment guide: `AWS_DEMO_DEPLOYMENT.md`
- Terraform guide: `README_TERRAFORM.md`

**Common Commands:**
```bash
# View deployment outputs
cd terraform && terraform output

# Update deployment
terraform apply

# View Lambda logs
aws logs tail /aws/lambda/coo-api-handler-demo

# Destroy resources
terraform destroy
```

---

**Happy Testing!** 🚀
