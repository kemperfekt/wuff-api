import os
from typing import Dict

import weaviate
from weaviate.classes.init import Auth

from src.models.symptom_models import SymptomInfo
from src.models.breed_models import BreedInfo
from src.models.instinct_models import InstinktVeranlagung

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

# -----------------------------------------------
# Holt Symptom-Info basierend auf semantischer Suche
# -----------------------------------------------
def get_symptom_info(symptom_input: str) -> SymptomInfo:
    client = get_client()
    try:
        response = (
            client
            .collections
            .get("Symptom")
            .query
            .near_text(query=symptom_input, limit=1)
        )

        if not response.objects:
            raise RuntimeError(f"Symptom '{symptom_input}' nicht gefunden.")

        raw = response.objects[0].properties
        instinkt_dict = raw.get("instinktvarianten", {})

        # Rücktransform in Dict[str, str]
        instinkt_mapping = {
            "jagd": "Jagdinstinkt",
            "rudel": "Rudelinstinkt",
            "territorial": "Territorialinstinkt",
            "sexual": "Sexualinstinkt"
        }
        instinktvarianten: Dict[str, str] = {}
        for key, name in instinkt_mapping.items():
            beschreibung = instinkt_dict.get(key)
            if beschreibung:
                instinktvarianten[name] = beschreibung

        return SymptomInfo(
            symptom_name=raw.get("symptom_name", ""),
            beschreibung=raw.get("beschreibung", ""),
            erste_hilfe=raw.get("erste_hilfe", ""),
            instinktvarianten=instinktvarianten  # ⚠️ Feldname angepasst
        )
    finally:
        client.close()

# -----------------------------------------------
# Holt Rasse-Info basierend auf exaktem Namen
# -----------------------------------------------
def get_breed_info(breed_name: str) -> BreedInfo:
    client = get_client()
    try:
        response = (
            client
            .collections
            .get("Hunderassen")
            .query
            .near_text(query=breed_name, limit=1)
        )
        if not response.objects:
            raise RuntimeError(f"Rasse '{breed_name}' nicht gefunden.")
        raw = response.objects[0].properties
        return BreedInfo(
            rassename=raw.get("rassename", ""),
            alternative_namen=raw.get("alternative_namen") or [],
            ursprungsland=raw.get("ursprungsland", ""),
            gruppen_code=raw.get("gruppen_code", "")
        )
    finally:
        client.close()

# -----------------------------------------------
# Holt Instinkt-Profil aus Gruppe basierend auf semantischer Suche
# -----------------------------------------------
def get_instinkt_profile(gruppen_code: str) -> InstinktVeranlagung:
    client = get_client()
    try:
        response = (
            client
            .collections
            .get("Instinktveranlagung")
            .query
            .near_text(query=gruppen_code, limit=1)
        )
        if not response.objects:
            raise RuntimeError(f"Instinktprofil für Gruppe '{gruppen_code}' nicht gefunden.")
        raw = response.objects[0].properties
        return InstinktVeranlagung(
            gruppen_code=raw.get("gruppen_code", ""),
            gruppe=raw.get("gruppe", ""),
            untergruppe=raw.get("untergruppe", ""),
            funktion=raw.get("funktion", ""),
            merkmale=raw.get("merkmale", ""),
            anforderungen=raw.get("anforderungen", ""),
            instinkte=raw.get("instinkte", {})
        )
    finally:
        client.close()
