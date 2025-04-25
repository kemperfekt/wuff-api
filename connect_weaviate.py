# -------------------------------
# DogBot Weaviate Verbindung
# -------------------------------
# Aufgabe: Verbindungsaufbau zu Weaviate-Server
# - Wird von anderen Modulen (z.B. symptom_tools) genutzt
# - Macht das Projekt modularer und übersichtlicher

import weaviate
import os

def connect_weaviate() -> weaviate.Client:
    """
    Stellt eine Verbindung zu Weaviate her.
    Nutzt Umgebungsvariablen WEAVIATE_URL und OPENAIAPIKEY (optional).
    """
    weaviate_url = os.getenv("WEAVIATE_URL")
    if not weaviate_url:
        raise EnvironmentError("WEAVIATE_URL ist nicht gesetzt.")

    openai_key = os.getenv("OPENAIAPIKEY")

    client = weaviate.Client(
        url=weaviate_url,
        auth_client_secret=None,  # Auth deaktiviert für lokale Nutzung
        additional_headers={
            "X-OpenAI-Api-Key": openai_key
        } if openai_key else {}
    )

    return client
