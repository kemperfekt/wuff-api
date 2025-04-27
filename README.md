    ## 🐶 dogbot-agent
    DogBot gives your dog a voice.

    It’s an empathetic AI agent that helps you understand your dog’s behavior — powered by GPT-4 and a semantic database (Weaviate).
    Together, they translate symptoms into insights and support you with clear, kind guidance.

    This repo contains the backend: a FastAPI app that connects OpenAI's language intelligence with structured dog behavior knowledge.

    ## 🔧 Local Setup
    Clone the repo and install dependencies in a virtual environment:
    git clone https://github.com/kemperfekt/dogbot-agent.git
    cd dogbot-agent
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    ## 🧪 Start the Agent
    bash
    uvicorn main:app --reload
    # Available at http://localhost:8000/docs

    ## 🔑 Required Environment Variables
    Make sure to set these system-wide:

    OPENAI_APIKEY – your OpenAI key
    WEAVIATE_API_KEY – API key for your Weaviate Cloud instance
    WEAVIATE_URL – the REST endpoint of your Weaviate Cloud

    ## 📦 Tech Stack
    FastAPI – modern Python web framework
    OpenAI Python SDK – connects to GPT
    Weaviate Python Client – queries the semantic knowledge base
    Plus: pydantic, uvicorn, python-dotenv (optional for local dev)

    ## 🔄 How It Works
    A user describes a behavioral symptom (e.g., “Why is my dog barking at other dogs?”)
    GPT analyzes the request and decides whether to look up data
    Relevant symptom data is retrieved from Weaviate
    GPT asks follow-up questions to clarify the situation
    Based on the answers, it identifies the underlying instinct
    A tailored diagnosis and advice are generated

    ## 📚 Related Repositories
    🔵 Frontend (React): github.com/kemperfekt/dogbot-ui
    🟡 Data & Weaviate content: github.com/kemperfekt/dogbot-ops
    🐶 Project meta-repo with vision and coordination: https://github.com/kemperfekt/dogbot