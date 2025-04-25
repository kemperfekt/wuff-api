# -------------------------------
# DogBot Weaviate Tools
# -------------------------------
# Aufgabe: Abfrage von Symptom-Informationen aus Weaviate
# - Liefert strukturierte Infos zu einem Symptom (z.B. Instinktvarianten)

import weaviate
import os

# Verbindung zu Weaviate-Server herstellen
client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),  # Beispiel: "http://localhost:8080"
    auth_client_secret=None,         # Authentifizierung aktuell nicht aktiv
    additional_headers={
        "X-OpenAI-Api-Key": os.getenv("OPENAIAPIKEY")  # Falls Vektorizer OpenAI nutzt
    }
)

# ---------------------------------------
# Holt ein Symptom-Dokument aus Weaviate anhand des Namens
# ---------------------------------------
def get_symptom_info(symptom_name: str) -> dict:
    """
    Holt strukturierte Informationen über ein Symptom aus Weaviate.
    Liefert z.B. Symptom-Name, zugeordnete Instinktvarianten etc.
    """

    # GraphQL-Query an Weaviate senden
    response = client.query.get(
        "Symptom",                # Collection / Klasse in Weaviate
        ["symptom", "instinktvarianten { instinkt beschreibung }"]  # Gewünschte Felder
    ).with_where({
        "path": ["symptom"],
        "operator": "Equal",
        "valueText": symptom_name
    }).with_limit(1).do()

    # Ausgabe prüfen
    symptome = response.get("data", {}).get("Get", {}).get("Symptom", [])
    if not symptome:
        raise ValueError(f"Symptom '{symptom_name}' nicht gefunden.")

    return symptome[0]
