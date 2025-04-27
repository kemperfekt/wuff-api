import os
from connect_weaviate import get_weaviate_client
from weaviate.classes.query import Filter
from symptom_models import SymptomInfo

def get_symptom_info(symptom_input: str) -> dict:
    """
    Ruft Symptomdaten aus Weaviate ab und validiert sie über das SymptomInfo-Modell.
    """
    client = get_weaviate_client()

    try:
        where_filter = Filter.by_property("symptom_name").equal(symptom_input)

        response = client.collections.get("Symptom").query.fetch_objects(
            filters=where_filter,
            limit=1
        )

        if not response.objects:
            return {"fehler": f"Symptom '{symptom_input}' nicht gefunden."}

        raw_data = response.objects[0].properties

        mapped_data = {
            "symptom_name": raw_data.get("symptom_name", ""),
            "instinktvarianten": []
        }

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

        # Validierung und saubere Rückgabe
        symptom_info = SymptomInfo(**mapped_data)
        return symptom_info.model_dump()

    except Exception as e:
        return {"fehler": f"Fehler bei der Weaviate-Abfrage: {str(e)}"}

    finally:
        client.close()

def is_valid_symptom_info(data: dict) -> bool:
    """
    Prüft, ob ein SymptomInfo-Datensatz valide ist (kein Fehler enthalten).
    """
    if not isinstance(data, dict):
        return False
    if "fehler" in data:
        return False
    if "symptom_name" not in data or "instinktvarianten" not in data:
        return False
    return True
