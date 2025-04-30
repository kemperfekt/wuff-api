# src/services/weaviate_client.py

import os
from fastapi import HTTPException
import weaviate

def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    Native v4-Client-Instanziierung mit AuthApiKey und zusätzlichen Headers.
    """
    url = os.getenv("WEAVIATE_URL")
    api_key = os.getenv("WEAVIATE_API_KEY")
    openai_key = os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_API_KEY")

    if not url:
        raise HTTPException(500, "WEAVIATE_URL ist nicht gesetzt")
    if not api_key:
        raise HTTPException(500, "WEAVIATE_API_KEY ist nicht gesetzt")
    if not openai_key:
        raise HTTPException(500, "OPENAI_APIKEY ist nicht gesetzt")

    try:
        client = weaviate.Client(
            url=url,
            auth_client_secret=weaviate.auth.AuthApiKey(api_key=api_key),
            additional_headers={"X-OpenAI-Api-Key": openai_key},
        )
        # Optional: Überprüfen, ob der Cluster erreichbar ist
        if not client.is_ready():
            raise RuntimeError("Weaviate-Cluster nicht erreichbar")
        return client
    except Exception as e:
        raise HTTPException(500, f"Weaviate-Verbindung fehlgeschlagen: {e}")
