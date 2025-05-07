# src/services/weaviate_client.py

import os
from fastapi import HTTPException
import weaviate
from weaviate.classes.init import Auth


def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    Erstellt einen Weaviate-Client via Cloud-Connector und übergibt
    notwendige Header für OpenAI.

    Erwartete Umgebungsvariablen:
      - WEAVIATE_URL
      - WEAVIATE_API_KEY
      - OPENAI_APIKEY oder OPENAI_API_KEY
    """
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    openai_key = os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_API_KEY")

    if not weaviate_url:
        raise HTTPException(status_code=500, detail="WEAVIATE_URL ist nicht gesetzt")
    if not weaviate_api_key:
        raise HTTPException(status_code=500, detail="WEAVIATE_API_KEY ist nicht gesetzt")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_APIKEY ist nicht gesetzt")

    try:
        # Connect to Weaviate Cloud with OpenAI header
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={"X-OpenAI-Api-Key": openai_key}
        )
        # Optional: Verbindungscheck
        if not client.is_ready():
            raise RuntimeError("Weaviate-Cluster nicht erreichbar")
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weaviate-Verbindung fehlgeschlagen: {e}")
