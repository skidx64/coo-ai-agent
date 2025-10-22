# Coo AI - Intelligent Parenting Companion Agent

> **AWS AI Agent Hackathon 2025 Submission**
> Autonomous AI agent providing evidence-based parenting guidance through multi-tier classification, reasoning LLMs, and agentic workflows.

[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-purple)](https://aws.amazon.com/bedrock/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Problem Statement

New parents face overwhelming information overload during critical moments—3am fever spikes, vaccine confusion, developmental concerns. They need instant, personalized, evidence-based guidance from a trusted source that understands their child's unique context.

3.6M US babies are born every year. Their parents need 24/7 support. Coo delivers age-aware guidance, vaccine reminders, milestones as well as school/ daycare deadlines for parents with kids 5 years or younger

**Statistics:**
- 85% of new parents report feeling overwhelmed by conflicting health advice
- Average wait time for pediatrician advice: 24-48 hours
- Unnecessary ER visits cost families $2,000+ per incident

## 💡 Solution

**Coo AI** is an autonomous AI agent powered by AWS Bedrock that provides personalized parenting guidance 24/7 through SMS and web interfaces.

So how does coo stand out from the other ai agents 

Coo maintains your child's profile and has all the information like age, allergies, milestones, etc so it gives personalized responses and also proactively reminds you of the upcoming vaccinations, side effects of a paricular vaccine, milestones, etc. It also integrates information about pediatricians, daycare and schools near by to remind you about the upcoming events.

The agent uses:

- **3-Tier Classification Pipeline**: Emergency detection → Keyword classification → Nova Lite AI fallback
- **Reasoning LLM**: Claude 3.5 Haiku for context-aware decision-making
- **Agentic Workflows**: 5 autonomous multi-step workflows (pregnancy, vaccines, milestones, activities, preschool)
- **RAG Knowledge Base**: 70+ evidence-based medical documents from CDC, AAP, Mayo Clinic
- **Conversation Memory**: Context-aware responses with full conversation history

## 🏆 AWS AI Agent Hackathon Requirements

| Requirement | Implementation | Evidence |
|-------------|---------------|----------|
| **✅ LLM from Bedrock/SageMaker** | Claude 3.5 Haiku via Bedrock | `ai_service.py:92-125` |
| **✅ AWS Service Usage** | Bedrock + Nova Lite + Lambda + API Gateway + RDS | See Architecture |
| **✅ Reasoning LLM** | Age-aware symptom triage with urgency classification | `ai_service.py:203-286` |
| **✅ Autonomous Capabilities** | 5 multi-step workflows execute independently | `workflow_service.py:8-577` |
| **✅ External Integrations** | RAG (ChromaDB), PostgreSQL, Twilio SMS, Conversation Memory | See Tech Stack |
| **⭐ AgentCore Primitive** | Workflow orchestration with autonomous tool calling | `workflow_service.py:21-55` |

## 🏗️ Architecture

### Current Implementation (Budget-Friendly)

**Message Flow:**
```
Parent (SMS/Web)
  ↓
API Gateway (AWS)
  ↓
Lambda Function (coo-api-handler-dev)
  ↓
┌─────────────────────────────────────┐
│  Message Classification Pipeline    │
│  ┌──────────────────────────────┐  │
│  │ Tier 1: Emergency Detection   │  │
│  │ <1ms | Free                   │  │
│  │ Keywords: "can't breathe",    │  │
│  │ "unconscious", "seizure"      │  │
│  └──────────────────────────────┘  │
│            ↓ (if no match)          │
│  ┌──────────────────────────────┐  │
│  │ Tier 2: Question Classifier   │  │
│  │ ~50ms | Free                  │  │
│  │ Categories: vaccine, symptom, │  │
│  │ development, pregnancy, etc.  │  │
│  └──────────────────────────────┘  │
│            ↓ (if ambiguous)         │
│  ┌──────────────────────────────┐  │
│  │ Tier 3: Nova Lite AI          │  │
│  │ 200-300ms | $0.000003/query   │  │
│  │ Analyzes context, child age   │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
  ↓
AI/ML - Bedrock
  ├─ Claude 3.5 Haiku (conversation & reasoning)
  ├─ Nova Lite (smart classification)
  └─ RAG (ChromaDB + local embeddings)
  ↓
Data Layer
  ├─ PostgreSQL/SQLite (family, children, messages)
  └─ Conversation Memory (last 10 messages)
  ↓
Response → Twilio → Parent
```

**Performance Metrics:**
- **Response Time:** < 3 seconds end-to-end
- **Classification Accuracy:** 95%+ with hybrid approach
- **Cost per Message:** ~$0.0001 (Nova Lite) + ~$0.002 (Claude) = **$0.0021**
- **Region:** us-east-1 (N. Virginia)

### Production Scale Architecture

**Scaling from 1K → 100K daily messages:**

| Component | Current | Scaled | Purpose |
|-----------|---------|--------|---------|
| **API Gateway** | HTTP API | HTTP API + CloudFront | Global CDN, rate limiting |
| **Lambda** | 1 function (1024MB) | 3 functions (2048MB) | API handler, workflow executor, scheduler |
| **Bedrock** | Haiku on-demand | Provisioned throughput | Consistent low latency |
| **Database** | SQLite (Lambda /tmp) | RDS PostgreSQL Multi-AZ | High availability, ACID compliance |
| **RAG** | ChromaDB (local) | Bedrock Knowledge Base + OpenSearch | Managed vector search |
| **Cache** | None | ElastiCache Redis | Frequent query caching |
| **Queue** | Synchronous | SQS + DLQ | Async processing, retry logic |
| **Monitoring** | CloudWatch Logs | CloudWatch + X-Ray + Alarms | Distributed tracing, alerts |

**Auto-Scaling Triggers:**
- Lambda concurrency: 10 → 1000 instances
- RDS read replicas: 1 → 3 (read-heavy queries)
- API Gateway throttling: 10 req/sec → 1000 req/sec
- ElastiCache cluster: 1 node → 3 nodes (high availability)

**Cost Comparison:**

| Scale | Users | Messages/Day | Monthly Cost |
|-------|-------|--------------|--------------|
| **Budget** | 50 families | 1,000 | **$3** |
| **Small** | 500 families | 10,000 | **$58** |
| **Medium** | 5,000 families | 100,000 | **$580** |
| **Large** | 50,000 families | 1,000,000 | **$5,200** |

## 🚀 Live Demo

**Production URL:** https://4p58s628h1.execute-api.us-east-1.amazonaws.com/app

**Test Queries:**
```bash
# Health Check
curl https://4p58s628h1.execute-api.us-east-1.amazonaws.com/

# AI Query (RAG)
curl -X POST https://4p58s628h1.execute-api.us-east-1.amazonaws.com/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "When should my baby start solid foods?"}'

# Vaccine Workflow
curl -X POST https://4p58s628h1.execute-api.us-east-1.amazonaws.com/api/workflows/vaccines \
  -H "Content-Type: application/json" \
  -d '{"child_age_months": 6, "concerns": "vaccine safety"}'
```

## 🛠️ Technology Stack

### AWS Services (Current Implementation)

| Service | Usage | Purpose |
|---------|-------|---------|
| **Amazon Bedrock** | Claude 3.5 Haiku | Primary reasoning LLM for conversations |
| **Amazon Nova Lite** | Classification fallback | Cost-efficient ambiguous query classification |
| **AWS Lambda** | Python 3.11 (1024MB, 30s timeout) | Serverless compute for API logic |
| **Amazon API Gateway** | HTTP API | RESTful routing for web/SMS |
| **Amazon RDS PostgreSQL** | db.t3.micro (optional) | Persistent family/child data |
| **SQLite** | Lambda /tmp (budget mode) | Lightweight database for testing |
| **Amazon S3** | Knowledge base storage (optional) | RAG document hosting |
| **Amazon CloudWatch** | Logs & metrics | Monitoring, debugging |

### Backend Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database access
- **ChromaDB** - Local vector database for RAG
- **Boto3** - AWS SDK for Bedrock/Lambda
- **Twilio** - SMS messaging API
- **Pydantic** - Data validation

### Frontend

- **Pure HTML/CSS/JavaScript** - No build tools
- **Responsive Design** - Mobile-first approach
- **SMS Simulator** - Test AI without real phone

## 🚀 Quick Start

### Local Development

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Set environment variables:**
```bash
# Copy template
cp .env.aws.example .env

# Edit .env
ENVIRONMENT=local
AI_PROVIDER=anthropic  # or bedrock
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com
RAG_PROVIDER=chromadb
DATABASE_URL=sqlite:///./coo.db
```

**3. Initialize database:**
```bash
python -c "from src.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

**4. Run application:**
```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

**5. Access:**
- **Web App:** http://127.0.0.1:8000/app
- **API Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/

### AWS Deployment

**Prerequisites:**
- AWS Account with billing enabled
- AWS CLI configured (optional)
- Python 3.11+ installed

**Quick Deploy (30 minutes):**

```bash
# 1. Package Lambda function
deploy_lambda.bat  # Windows
# OR
./deploy_lambda.sh  # Linux/Mac

# 2. Upload to S3
aws s3 cp coo-lambda.zip s3://coo-lambda-deployments-dev-449476174049/coo-lambda.zip --region us-east-1

# 3. Open AWS CloudShell and deploy
aws s3 cp s3://coo-lambda-deployments-dev-449476174049/coo-lambda.zip .
aws lambda update-function-code \
  --function-name coo-api-handler-dev \
  --zip-file fileb://coo-lambda.zip \
  --region us-east-1
```
## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Test specific workflow
pytest tests/test_workflows.py::test_vaccine_planning_workflow

# Test AI service
pytest tests/test_ai_service.py
```
## 🎥 Demo Video

**Watch the 3-minute demo:** [YouTube Link](https://www.youtube.com/watch?v=PFSqnPIRLio)

## 🤝 Contributing

This project was built for the AWS AI Agent Hackathon 2025. 

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AWS Bedrock Team** - For Claude 3.5 Haiku and Nova Lite models
- **Anthropic** - For Claude API and excellent documentation
- **CDC & AAP** - For evidence-based parenting guidelines
- **Mayo Clinic** - For medical symptom information
- **Twilio** - For SMS integration

---

**Live Demo:** https://4p58s628h1.execute-api.us-east-1.amazonaws.com/app
**Demo Video:** [YouTube Link](https://www.youtube.com/watch?v=PFSqnPIRLio)
