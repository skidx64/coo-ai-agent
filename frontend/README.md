# Coo - Frontend Demo

## Overview

This is a single-page HTML demo frontend that showcases all the key features of the Coo AI Parenting Companion backend API.

## Features

### 1. API Status & Health Check
- Test backend API connectivity
- Check AI service status
- Verify RAG service functionality
- List available workflows

### 2. AI Q&A
- Ask any parenting question
- Get AI-powered answers with RAG context
- Choose use case (general, vaccine info, symptom assessment)
- See sources used in responses

### 3. Symptom Triage
- Describe symptoms
- Get urgency assessment (EMERGENCY, URGENT, ROUTINE, HOME_CARE)
- AI-powered medical guidance with age consideration
- Emergency keyword detection

### 4. AI Workflows
- **Pregnancy Guidance**: Trimester info, milestones, action items
- **Vaccine Planning**: Schedule, concerns, timeline
- **Milestone Assessment**: Development evaluation, activities, red flags
- **Activity Recommendations**: Age-appropriate activities, weekly plans

### 5. Knowledge Base Search
- Semantic search through 42 documents
- Filter by category (pregnancy, vaccines, development, etc.)
- See relevance scores
- RAG-powered retrieval

## How to Access

### Production (AWS)

The app is deployed on AWS Lambda with API Gateway:
- **API Base URL**: https://4p58s628h1.execute-api.us-east-1.amazonaws.com
- **Demo Interface**: Open `frontend/index.html` or `frontend/app.html` directly in a browser
- The frontend is configured to use the deployed API automatically

### Local Development

1. **Start the backend server:**
   ```bash
   python -m uvicorn src.main:app --reload --port 8000
   ```

2. **Update API_BASE in frontend files:**
   - Change `API_BASE` to `http://127.0.0.1:8000` in:
     - `frontend/index.html`
     - `frontend/app.html`

3. **Open the demo:**
   - Navigate to: http://127.0.0.1:8000/demo
   - Or open: `frontend/index.html` directly in a browser

## Tech Stack

- **Pure HTML/CSS/JavaScript** - No build process required
- **Fetch API** - For backend communication
- **Responsive Design** - Works on all screen sizes
- **Modern UI** - Gradient backgrounds, smooth transitions

## API Endpoints Used

- `GET /` - API status
- `GET /api/ai/test` - AI service status
- `POST /api/ai/ask` - Ask questions
- `POST /api/ai/triage` - Symptom triage
- `GET /api/rag/info` - KB information
- `POST /api/rag/search` - Knowledge search
- `GET /api/workflows/` - List workflows
- `POST /api/workflows/{name}` - Execute workflows

## Features Demonstrated

- **Real-time API interaction** - All features call live backend
- **Error handling** - Graceful error display
- **Loading states** - Visual feedback during API calls
- **Formatted results** - Pretty JSON display
- **Tab navigation** - Organized feature sections

## Future Enhancements

For a production frontend, consider:
- React/Vue/Angular framework
- User authentication & sessions
- Family dashboard with saved data
- SMS conversation history view
- Task scheduling interface
- Multi-child/multi-parent management
- Real-time notifications
