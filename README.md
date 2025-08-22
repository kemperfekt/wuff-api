# WuffChat Backend API

> **Current Status**: Stable V2 in production | V3 agentic architecture in development

FastAPI backend service powering WuffChat - providing AI-driven dog behavior consultation through GPT-4 integration.

## Quick Start

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.main:app --reload --port 8000
```

## Technical Stack

- **Framework**: FastAPI with Python 3.11+
- **AI Model**: GPT-4 for natural language processing
- **Knowledge Base**: Weaviate vector database
- **Architecture**: V2 FSM (Finite State Machine) with 11 conversation states

## API Endpoints (V2)

```
POST /flow_intro    - Start new conversation session
POST /flow_step     - Send message and receive response
GET  /health        - Service health check
GET  /docs          - Interactive API documentation
```

## Key Features

- FSM-based conversation flow management
- Dog perspective response generation
- Session management with secure tokens
- Rate limiting and security headers
- Comprehensive error handling

## Security

- API key authentication (X-API-Key header)
- Session tokens with 30-minute expiration
- Rate limiting: 10 req/min (intro), 30 req/min (messages)
- CORS protection and security headers

## Full Documentation

For architecture details, security implementation, and development roadmap:  
**[-> View Complete Documentation](https://github.com/kemperfekt/dogbot)**

---

Part of the WuffChat ecosystem - see [wuffchat](https://github.com/kemperfekt/wuffchat) for overview.