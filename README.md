# DogBot Agent (Backend API)

This is the backend API service for DogBot. For comprehensive documentation, please refer to the [main DogBot README](../README.md).

## Quick Links

- 📚 [Full Documentation](../README.md)
- 🏗️ [Architecture Overview](../README.md#️-architecture-overview)
- 🚀 [Quick Start Guide](../README.md#-quick-start)
- 🔧 [Development Setup](../README.md#-development)
- 📊 [API Documentation](https://api.wuffchat.de/docs)

## Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn src.v2.main:app --reload --port 8000

# Test
pytest
```

## Key Features
- V2 FSM-based architecture
- GPT-4 powered responses from dog's perspective
- Weaviate vector search integration
- 11-state conversation flow
- Comprehensive test coverage

For detailed information, see the [main repository documentation](../README.md).