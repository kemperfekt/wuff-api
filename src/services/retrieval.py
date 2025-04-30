# src/services/retrieval.py

import os
from fastapi import HTTPException
from typing import List

from pydantic import ValidationError
from weaviate import Client

from services.weaviate_client import get_weaviate_client
from src.models.symptom_models import SymptomInfo
from src.models.breed_models import BreedInfo


def get_symptom_info(symptom_input: str) -> SymptomInfo:
    """
    Semantische Suche in der Weaviate-Collection "Symptom" mit dem v4-Client.

    Args:
        symptom_input: Freitext-Eingabe des Nutzers zum Symptom
                       (z.B. "hund zieht an der leine").

    Returns:
        SymptomInfo: Pydantic-Modell mit den Feldern symptom_name und instinktvarianten.
    """
    client: Client = get_weaviate_client()

    try:
        # Native v4: Collection-Objekt holen
        collection = client.collections.get("Symptom")
        # Query ausführen: Vektorbasierte Suche via nearText
        resp = (
            collection.query
                      .with_near_text({"concepts": [symptom_input]})
                      .with_limit(1)
                      .do()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weaviate-Abfrage fehlgeschlagen: {e}")

    try:
        # resp.objects ist Liste von Objekten mit Attribut .properties
        objs = resp.objects
        if not objs:
            raise HTTPException(status_code=404, detail="Kein Symptom-Muster gefunden")
        props = objs[0].properties
        # Pydantic-Validierung
        return SymptomInfo.parse_obj(props)
    except (AttributeError, ValidationError) as e:
        raise HTTPException(status_code=500, detail=f"SymptomInfo-Parsing fehlgeschlagen: {e}")


def get_breed_info(breed: str) -> BreedInfo:
    """
    Semantische Suche in der Weaviate-Collection "BreedGroup" mit dem v4-Client.

    Args:
        breed: Name oder Stichwort zur Hunderasse (z.B. "Labrador").

    Returns:
        BreedInfo: Pydantic-Modell mit den Feldern group_name, function,
                   features, requirements und instinct_score.
    """
    client: Client = get_weaviate_client()

    try:
        collection = client.collections.get("BreedGroup")
        resp = (
            collection.query
                      .with_near_text({"concepts": [breed]})
                      .with_limit(1)
                      .do()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weaviate-Abfrage fehlgeschlagen: {e}")

    try:
        objs = resp.objects
        if not objs:
            raise HTTPException(status_code=404, detail="Keine passende Rasse-Gruppe gefunden")
        props = objs[0].properties
        return BreedInfo.parse_obj(props)
    except (AttributeError, ValidationError) as e:
        raise HTTPException(status_code=500, detail=f"BreedInfo-Parsing fehlgeschlagen: {e}")
