# Changes Summary - AWS Demo Mode

This document summarizes all changes made to enable AWS deployment with authentication bypass and demo data.

## Files Created

### 1. `src/seed_demo_data.py`
**Purpose:** Auto-populate database with demo users

**What it does:**
- Creates 1 family with ID=1
- Adds 2 parents: Sarah Johnson (+15555550001) and Michael Johnson (+15555550002)
- Adds 2 children: Emma (3yo, female) and Noah (6mo, male)
- Sets up phone lookup table for SMS routing
- Grants FAMILY tier with 1-year trial

**When it runs:**
- Automatically on Lambda startup when `SKIP_AUTH=true`
- Can be run manually: `python -m src.seed_demo_data`

---

### 2. `deploy_aws_demo.bat` (Windows)
**Purpose:** One-click deployment script for Windows

**What it does:**
1. Verifies AWS CLI and Terraform installation
2. Validates AWS credentials
3. Builds Lambda deployment package (installs dependencies, creates zip)
4. Initializes Terraform
5. Plans and applies infrastructure changes
6. Displays API Gateway URL and next steps

**How to use:**
```cmd
deploy_aws_demo.bat
```

---

### 3. `deploy_aws_demo.sh` (Linux/Mac)
**Purpose:** One-click deployment script for Linux/Mac

**What it does:** Same as Windows version, adapted for bash

**How to use:**
```bash
chmod +x deploy_aws_demo.sh
./deploy_aws_demo.sh
```

---

### 4. `AWS_DEMO_DEPLOYMENT.md`
**Purpose:** Comprehensive deployment guide

**Sections:**
- Prerequisites and setup
- Step-by-step deployment instructions
- API testing examples (curl and Python)
- Architecture overview
- Cost estimation
- Troubleshooting guide
- Cleanup instructions

---

### 5. `QUICK_START_DEMO.md`
**Purpose:** Quick reference for rapid deployment

**Sections:**
- TL;DR deployment commands
- Demo user details
- Quick API tests
- Common troubleshooting
- Cost estimates

---

## Files Modified

### 1. `src/services/auth_service.py`
**Changes:**
- Added `SKIP_AUTH` environment variable check
- Added `DEMO_FAMILY_ID` environment variable (default: 1)
- Modified `verify_token()` to return mock payload when `SKIP_AUTH=true`

**Code added:**
```python
import os

SKIP_AUTH = os.getenv("SKIP_AUTH", "false").lower() == "true"
DEMO_FAMILY_ID = int(os.getenv("DEMO_FAMILY_ID", "1"))

def verify_token(token: str) -> Optional[dict]:
    if SKIP_AUTH:
        return {
            "sub": "demo@cooai.test",
            "family_id": DEMO_FAMILY_ID,
            "exp": (datetime.utcnow() + timedelta(days=365)).timestamp()
        }
    # ... rest of original code
```

**Impact:**
- When `SKIP_AUTH=true`, all API endpoints bypass authentication
- Requests are automatically associated with `family_id=1`

---

### 2. `src/main.py`
**Changes:**
- Added import for `Request` (for future middleware if needed)
- Added demo data seeding in `startup_event()`

**Code added:**
```python
@app.on_event("startup")
async def startup_event():
    init_db()

    # Seed demo data if SKIP_AUTH is enabled
    if os.getenv("SKIP_AUTH", "false").lower() == "true":
        from .seed_demo_data import seed_demo_data
        try:
            family_id = seed_demo_data()
            print(f"[DEMO] Demo data seeded. Family ID: {family_id}")
            print(f"[DEMO] Auth is BYPASSED - demo mode enabled")
        except Exception as e:
            print(f"[WARN] Error seeding demo data: {e}")
    # ... rest of original code
```

**Impact:**
- Demo data is automatically created on first Lambda cold start
- Logs confirm demo mode status

---

### 3. `terraform/lambda.tf`
**Changes:**
- Added `SKIP_AUTH` environment variable
- Added `DEMO_FAMILY_ID` environment variable

**Code added:**
```hcl
environment {
  variables = {
    # ... existing variables
    SKIP_AUTH       = "true"
    DEMO_FAMILY_ID  = "1"
  }
}
```

**Impact:**
- Lambda function runs in demo mode by default
- Can be toggled by changing `SKIP_AUTH` to `"false"`

---

### 4. `terraform/terraform.tfvars`
**Changes:**
- Updated `environment` from `"dev"` to `"demo"`
- Increased `lambda_timeout` from 30 to 60 seconds
- Changed `bedrock_model_id` to Claude 3.5 Sonnet v2 (better quality)

**Before:**
```hcl
environment = "dev"
lambda_timeout = 30
bedrock_model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
```

**After:**
```hcl
environment = "demo"
lambda_timeout = 60  # Increased for AI operations
bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

**Impact:**
- More time for AI processing (60s vs 30s)
- Better AI response quality (Sonnet vs Haiku)
- Resource names include "demo" suffix

---

## Configuration Changes

### Environment Variables (Lambda)

| Variable | Value | Purpose |
|----------|-------|---------|
| `SKIP_AUTH` | `true` | Bypass JWT authentication |
| `DEMO_FAMILY_ID` | `1` | Default family for all requests |
| `ENVIRONMENT` | `aws` | AWS-specific config (existing) |
| `AI_PROVIDER` | `bedrock` | Use AWS Bedrock (existing) |
| `RAG_PROVIDER` | `chromadb` | Local vector DB (existing) |

---

## How It Works

### Authentication Flow (Demo Mode)

**Before (Normal Mode):**
```
Client Request
  → API Gateway
  → Lambda: verify_token(JWT)
  → Decode JWT to get family_id
  → Process request with family_id
```

**After (Demo Mode):**
```
Client Request
  → API Gateway
  → Lambda: verify_token(ANY_TOKEN)
  → Return mock payload {family_id: 1}
  → Process request with family_id=1
```

**Key Points:**
- Any token is accepted (even "demo" or empty)
- All requests map to `family_id=1`
- No password verification
- No token expiration check

---

### Database Seeding Flow

**On Lambda Cold Start:**
```
1. main.py: startup_event() runs
2. Check: SKIP_AUTH == "true"?
3. Import seed_demo_data module
4. Check: Does family with email "demo@cooai.test" exist?
5. If NO: Create family, members, children, phone lookups
6. If YES: Skip (idempotent)
7. Log: "[DEMO] Demo data seeded. Family ID: X"
```

**Data Created:**
```
Family
├─ id: 1
├─ email: demo@cooai.test
├─ tier: FAMILY
└─ trial_end: 1 year from now

FamilyMembers
├─ Sarah Johnson (mom) → +15555550001
└─ Michael Johnson (dad) → +15555550002

Children
├─ Emma Johnson (3yo, female)
└─ Noah Johnson (6mo, male)

PhoneLookup
├─ +15555550001 → family_id=1, member_id=1
└─ +15555550002 → family_id=1, member_id=2
```

---

## Testing Checklist

After deployment, verify:

- [ ] Health endpoint responds: `curl https://API_URL/health`
- [ ] Lambda logs show: `[DEMO] Demo data seeded`
- [ ] Lambda logs show: `[DEMO] Auth is BYPASSED`
- [ ] AI endpoint works: `POST /api/ai/answer` with `family_id=1`
- [ ] Children endpoint works: `GET /api/children?family_id=1`
- [ ] No authentication errors (all tokens accepted)
- [ ] CloudWatch logs are accessible

---

## Reverting to Production Mode

To enable authentication and remove demo mode:

### 1. Update `terraform/lambda.tf`
```hcl
environment {
  variables = {
    # ... other vars
    SKIP_AUTH = "false"  # Changed from "true"
    # Remove DEMO_FAMILY_ID or set to ""
  }
}
```

### 2. Update `terraform/terraform.tfvars`
```hcl
environment = "prod"  # Changed from "demo"
```

### 3. Redeploy
```bash
cd terraform
terraform apply
```

### 4. Use Real Authentication
```bash
# Signup
curl -X POST "https://API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123",
    "phone": "+15551234567",
    "name": "Real User"
  }'

# Login and get JWT
curl -X POST "https://API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123"
  }'

# Use JWT in requests
curl -X POST "https://API_URL/api/ai/answer" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"question": "..."}'
```

---

## Security Considerations

**Current State (Demo Mode):**
- ⚠️ No authentication required
- ⚠️ All users access same data (family_id=1)
- ⚠️ Public API endpoint (anyone can call)
- ⚠️ Not suitable for production

**Recommended for Production:**
- ✅ Set `SKIP_AUTH=false`
- ✅ Use RDS PostgreSQL (not SQLite)
- ✅ Enable API Gateway authentication
- ✅ Use secrets manager for credentials
- ✅ Enable CloudWatch alarms
- ✅ Add rate limiting
- ✅ Enable WAF

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                 Client                          │
│         (curl, browser, mobile app)             │
└────────────────┬────────────────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────┐
│           API Gateway (HTTP API)                │
│  https://xyz.execute-api.us-east-1.amazonaws... │
└────────────────┬────────────────────────────────┘
                 │ Invoke
                 ▼
┌─────────────────────────────────────────────────┐
│     Lambda Function (Python 3.11)               │
│  ┌───────────────────────────────────────────┐  │
│  │  FastAPI App (via Mangum)                 │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ Auth: verify_token()                │  │  │
│  │  │   if SKIP_AUTH: return mock         │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ AI Service (Bedrock)                │  │  │
│  │  │   - Claude 3.5 Sonnet               │  │  │
│  │  │   - Nova Lite (classification)      │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ RAG Service (ChromaDB)              │  │  │
│  │  │   - 70+ medical docs                │  │  │
│  │  │   - Stored in /tmp                  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ Database (SQLite)                   │  │  │
│  │  │   - Stored in /tmp/coo.db           │  │  │
│  │  │   - Demo data auto-seeded           │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                 │ Logs
                 ▼
┌─────────────────────────────────────────────────┐
│   CloudWatch Logs                               │
│   /aws/lambda/coo-api-handler-demo              │
└─────────────────────────────────────────────────┘
```

---

## Cost Breakdown (Estimated)

**Lambda:**
- Free tier: 1M requests/month, 400,000 GB-seconds
- 1GB memory × 2 seconds average = 2 GB-seconds per request
- 100 requests = 200 GB-seconds
- Cost: $0.00 (within free tier)

**Bedrock (Claude 3.5 Sonnet):**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Average question: 1,000 input + 300 output tokens
- 100 questions = 100K input + 30K output
- Cost: (100K × $3/1M) + (30K × $15/1M) = $0.30 + $0.45 = $0.75

**API Gateway:**
- Free tier: 1M requests/month
- 100 requests = $0.00 (within free tier)

**Total for 100 AI questions: ~$0.75**

---

## Deployment Checklist

Before deploying:
- [ ] AWS CLI installed and configured
- [ ] Terraform installed
- [ ] Python 3.11 installed
- [ ] Bedrock models enabled (Sonnet, Nova Lite)
- [ ] AWS credentials have Lambda, API Gateway, IAM permissions

During deployment:
- [ ] Run `deploy_aws_demo.bat` or `deploy_aws_demo.sh`
- [ ] Verify no errors in Terraform output
- [ ] Save API Gateway URL from output

After deployment:
- [ ] Test health endpoint
- [ ] Check CloudWatch logs for demo data seeding
- [ ] Test AI endpoints
- [ ] Verify demo users exist

---

## Support & Resources

**Documentation:**
- Quick start: `QUICK_START_DEMO.md`
- Full guide: `AWS_DEMO_DEPLOYMENT.md`
- Terraform docs: `README_TERRAFORM.md`

**Useful Commands:**
```bash
# View all outputs
cd terraform && terraform output

# Update deployment
terraform apply

# View logs
aws logs tail /aws/lambda/coo-api-handler-demo --follow

# Destroy resources
terraform destroy
```

**Common Issues:**
- See troubleshooting section in `AWS_DEMO_DEPLOYMENT.md`
- Check CloudWatch logs for detailed error messages
- Verify Bedrock model access in AWS Console

---

**End of Changes Summary**
