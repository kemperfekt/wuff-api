import os
import weaviate
from weaviate.classes.init import Auth


# -----------------------------------------------
# Verbindungsaufbau zu Weaviate Cloud (v4)
# -----------------------------------------------
def get_client() -> weaviate.Client:
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    openai_api_key = os.getenv("OPENAI_APIKEY")

    if not weaviate_url:
        raise RuntimeError("WEAVIATE_URL nicht gesetzt")
    if not weaviate_api_key:
        raise RuntimeError("WEAVIATE_API_KEY nicht gesetzt")
    if not openai_api_key:
        raise RuntimeError("OPENAI_APIKEY nicht gesetzt")

    # Verbinde mit Cloud und übergebe OpenAI-Key als Header
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers={"X-Openai-Api-Key": openai_api_key}
    )
    return client

from weaviate.classes.query import MetadataQuery

def search_relevant_chunks(query: str, class_name: str = "Symptom", limit: int = 3) -> list[str]:
    """
    Sucht in der angegebenen Weaviate-Collection (z. B. 'Symptom') nach passenden Inhalten.
    Gibt eine Liste von Kontext-Texten zurück, basierend auf semantischer Ähnlichkeit.
    """
    client = get_client()
    collection = client.collections.get(class_name)

    response = collection.query.near_text(
        query=query,
        limit=limit,
        return_metadata=MetadataQuery(distance=True),
    )

    print(f"🔎 Weaviate Query: '{query}' in Klasse '{class_name}'")
    print(f"📦 Treffer: {[obj.properties for obj in response.objects]}")

    client.close()

    # ⚠️ HINWEIS: Aktuell wird nur das Feld 'text' verwendet.
    # Wenn du eine andere Property (z. B. 'beschreibung' oder 'antwort') nutzt,
    # muss diese hier angepasst werden!
    return [
        f"{obj.properties.get('thema', '')}: {obj.properties.get('beschreibung', '')}"
        for obj in response.objects
    ]