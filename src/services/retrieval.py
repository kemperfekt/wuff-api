# src/services/retrieval.py

import os
from fastapi import HTTPException
from typing import List
from pydantic import ValidationError
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery

from src.models.symptom_models import SymptomInfo
from src.models.breed_models import BreedInfo


def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    Baut den Weaviate-Client via Cloud-Connector auf und gibt ihn zurück.
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
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={"X-OpenAI-Api-Key": openai_key}
        )
        if not client.is_ready():
            raise RuntimeError("Weaviate-Cluster nicht erreichbar")
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weaviate-Verbindung fehlgeschlagen: {e}")


def get_symptom_info(symptom_input: str) -> SymptomInfo:
    """
    Führt eine Near-Text-Suche in der Collection "Symptom" durch und
    gibt das Top-1-Ergebnis als SymptomInfo zurück.
    """
    client = get_weaviate_client()
    try:
        coll = client.collections.get("Symptom")
        response = coll.query.near_text(
            query=symptom_input,
            limit=1,
            return_metadata=MetadataQuery(distance=True)
        )
    except Exception as e:
        client.close()
        raise HTTPException(status_code=500, detail=f"Weaviate-Abfrage fehlgeschlagen: {e}")

    client.close()
    objs = response.objects
    if not objs:
        raise HTTPException(status_code=404, detail="Kein Symptom-Muster gefunden")
    props = objs[0].properties

    # Patch: instinktvarianten als Liste sicherstellen
    raw_variants = props.get("instinktvarianten") or {}
    if isinstance(raw_variants, dict):
        props["instinktvarianten"] = list(raw_variants.values())
    elif not isinstance(raw_variants, list):
        props["instinktvarianten"] = []

    try:
        # Pydantic V2-konforme Validierung
        symptom = SymptomInfo.model_validate(props)
        return symptom
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"SymptomInfo-Parsing fehlgeschlagen: {e}")


def get_breed_info(breed: str) -> BreedInfo:
    """
    Führt eine Near-Text-Suche in der Collection "BreedGroup" durch und
    gibt das Top-1-Ergebnis als BreedInfo zurück.
    """
    client = get_weaviate_client()
    try:
        coll = client.collections.get("BreedGroup")
        response = coll.query.near_text(
            query=breed,
            limit=1,
            return_metadata=MetadataQuery(distance=True)
        )
    except Exception as e:
        client.close()
        raise HTTPException(status_code=500, detail=f"Weaviate-Abfrage fehlgeschlagen: {e}")

    client.close()
    objs = response.objects
    if not objs:
        raise HTTPException(status_code=404, detail="Keine passende Rasse-Gruppe gefunden")
    props = objs[0].properties

    try:
        breed_info = BreedInfo.model_validate(props)
        return breed_info
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"BreedInfo-Parsing fehlgeschlagen: {e}")
