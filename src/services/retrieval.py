# src/services/retrieval.py

import os
import weaviate
from weaviate import Client
from src.models.symptom_models import SymptomInfo
from src.models.breed_models import BreedInfo
from src.models.instinct_models import InstinktVeranlagung


def get_client() -> Client:
    """
    Erstellt und gibt einen Weaviate-Client basierend auf Umgebungsvariablen zurück.
    Erwartet:
      - WEAVIATE_URL
      - optional WEAVIATE_APIKEY
    """
    url = os.getenv("WEAVIATE_URL")
    if not url:
        raise RuntimeError("WEAVIATE_URL nicht gesetzt")
    api_key = os.getenv("WEAVIATE_APIKEY")
    headers = {"X-API-KEY": api_key} if api_key else {}
    return weaviate.Client(
        url,
        additional_headers=headers
    )


def get_symptom_info(symptom_name: str) -> SymptomInfo:
    """
    Holt die Details zu einem Symptom aus der Weaviate-Klasse 'Symptom'
    und validiert sie gegen das Pydantic-Modell SymptomInfo.
    """
    client = get_client()
    resp = (
        client.query
              .get("Symptom", ["symptom_name", "beschreibung", "erste_hilfe", "instinkt_varianten"])
              .with_where({
                  "path": ["symptom_name"],
                  "operator": "Equal",
                  "valueString": symptom_name
              })
              .do()
    )
    items = resp.get("data", {}).get("Get", {}).get("Symptom", [])
    if not items:
        raise ValueError(f"Kein Symptom '{symptom_name}' gefunden.")
    props = items[0]["properties"]
    # Pydantic v2: model_validate
    return SymptomInfo.model_validate(props)


def get_breed_info(rassename: str) -> BreedInfo:
    """
    Holt die Rasse-Details aus der Weaviate-Klasse 'Hunderassen'
    und validiert sie gegen das Pydantic-Modell BreedInfo.
    """
    client = get_client()
    resp = (
        client.query
              .get("Hunderassen", ["rassename", "alternative_namen", "ursprungsland", "gruppen_code"])
              .with_where({
                  "path": ["rassename"],
                  "operator": "Equal",
                  "valueString": rassename
              })
              .do()
    )
    items = resp.get("data", {}).get("Get", {}).get("Hunderassen", [])
    if not items:
        raise ValueError(f"Keine Rasse '{rassename}' gefunden.")
    props = items[0]["properties"]
    return BreedInfo.model_validate(props)


def get_instinkt_profile(gruppen_code: str) -> InstinktVeranlagung:
    """
    Holt das Instinktprofil aus der Weaviate-Klasse 'Instinktveranlagung'
    basierend auf dem Gruppen-Code und validiert es gegen InstinktVeranlagung.
    """
    client = get_client()
    resp = (
        client.query
              .get(
                  "Instinktveranlagung",
                  ["gruppen_code", "gruppe", "untergruppe", "funktion", "merkmale", "anforderungen", "instinkte"]
              )
              .with_where({
                  "path": ["gruppen_code"],
                  "operator": "Equal",
                  "valueString": gruppen_code
              })
              .do()
    )
    items = resp.get("data", {}).get("Get", {}).get("Instinktveranlagung", [])
    if not items:
        raise ValueError(f"Kein Instinktprofil für Gruppe '{gruppen_code}' gefunden.")
    props = items[0]["properties"]
    return InstinktVeranlagung.model_validate(props)
