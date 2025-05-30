# DogBot Agent (Backend API)

This is the backend API service for DogBot. For comprehensive documentation, please refer to the [main DogBot README](https://github.com/kemperfekt/dogbot).

## Quick Links

- 📚 [Full Documentation](https://github.com/kemperfekt/dogbot)
- 🏗️ [Architecture Overview](https://github.com/kemperfekt/dogbot#-architecture-overview)
- 🚀 [Quick Start Guide](https://github.com/kemperfekt/dogbot#-quick-start)
- 🔧 [Development Setup](https://github.com/kemperfekt/dogbot#-development)
- 📊 [API Documentation](https://api.wuffchat.de/docs)

## Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn src.main:app --reload --port 8000

# Test
pytest
```

## Key Features
- V2 FSM-based architecture
- GPT-4 powered responses from dog's perspective
- Weaviate vector search integration
- 11-state conversation flow
- Comprehensive test coverage

For detailed information, see the [main repository documentation](https://github.com/kemperfekt/dogbot).