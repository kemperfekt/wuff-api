import os
import weaviate
from weaviate.classes.init import Auth
from connect_weaviate import get_weaviate_client
from weaviate.classes.query import Filter

# Verbindungsparameter
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_APIKEY")

# -----------------------------------------------
# Verbindungsaufbau zu Weaviate
# -----------------------------------------------
def get_weaviate_client():
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers={
            "X-Openai-Api-Key": openai_api_key
        }
    )

# -----------------------------------------------
# Holt Symptom-Info basierend auf semantischer Suche
# -----------------------------------------------
def get_symptom_info(symptom_input: str) -> dict:
    client = get_weaviate_client()

    try:
        # Semantische Suche über near_text
        response = client.collections.get("Symptom").query.near_text(
            query=symptom_input,
            limit=1
        )

        if not response.objects:
            return {"fehler": f"Symptom '{symptom_input}' nicht gefunden."}

        raw_data = response.objects[0].properties

        # Feldübernahme exakt wie im Weaviate-Modell
        mapped_data = {
            "symptom_name": raw_data.get("symptom_name", ""),
            "instinktvarianten": []
        }

        # Optional: Falls instinkt_varianten (alt) vorhanden ist
        instinkt_dict = raw_data.get("instinkt_varianten", {})
        instinkt_mapping = {
            "jagd": "Jagdinstinkt",
            "rudel": "Rudelinstinkt",
            "territorial": "Territorialinstinkt",
            "sexual": "Sexualinstinkt"
        }

        for key, instinkt_name in instinkt_mapping.items():
            beschreibung = instinkt_dict.get(key)
            if beschreibung:
                mapped_data["instinktvarianten"].append({
                    "instinkt": instinkt_name,
                    "beschreibung": beschreibung
                })

        return mapped_data

    except Exception as e:
        return {"fehler": f"Fehler bei der Weaviate-Abfrage: {str(e)}"}

    finally:
        client.close()

# -----------------------------------------------
# Validiert SymptomInfo-Datenstruktur
# -----------------------------------------------
def is_valid_symptom_info(data: dict) -> bool:
    """
    Prüft, ob ein Dict eine valide SymptomInfo-Datenstruktur darstellt.
    """
    if not isinstance(data, dict):
        return False
    if "symptom_name" not in data or "instinktvarianten" not in data:
        return False
    if not isinstance(data["instinktvarianten"], list):
        return False
    return True
