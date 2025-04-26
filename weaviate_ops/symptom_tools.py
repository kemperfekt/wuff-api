
from connect_weaviate import get_weaviate_client
from weaviate.classes.query import Filter

def get_symptom_info(symptom_input: str) -> dict:
    client = get_weaviate_client()

    try:
        # Suche nach symptom_name (wie im Weaviate-Schema)
        where_filter = Filter.by_property("symptom_name").equal(symptom_input)

        response = client.collections.get("Symptom").query.fetch_objects(
            filters=where_filter,
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
