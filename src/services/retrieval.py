# src/services/retrieval.py

import json
from typing import Optional
from src.services.weaviate_service import query_agent_service

async def get_symptom_info(symptom: str) -> Optional[str]:
    """
    Sucht nach Informationen zu einem Hundeverhalten/Symptom mit dem Weaviate Query Agent.
    
    Args:
        symptom: Das beschriebene Hundeverhalten
        
    Returns:
        Ein Text mit relevanten Informationen oder None, wenn nichts gefunden wurde
    """
    try:
        # Direktes Query an den Weaviate Query Agent
        query = f"Beschreibe das folgende Hundeverhalten: {symptom}"
        
        result = await query_agent_service.query(
            query=query,
            collection_name="Symptom"
        )
        
        # Ergebnis extrahieren
        if "data" in result and result["data"]:
            # Je nach Struktur deiner Daten könnte dies angepasst werden müssen
            if "text" in result["data"]:
                return result["data"]["text"]
            elif "description" in result["data"]:
                return result["data"]["description"]
            elif "content" in result["data"]:
                return result["data"]["content"]
            else:
                # Versuche, das ganze data-Objekt zu serialisieren
                return json.dumps(result["data"])
        
        return None
    except Exception as e:
        print(f"⚠️ Fehler bei der Symptomsuche: {e}")
        return None


async def get_instinct_info(instinct: str) -> Optional[str]:
    """
    Sucht nach Informationen zu einem Hundeinstinkt mit dem Weaviate Query Agent.
    
    Args:
        instinct: Der Name des Instinkts
        
    Returns:
        Ein Text mit relevanten Informationen oder None, wenn nichts gefunden wurde
    """
    try:
        # Direktes Query an den Weaviate Query Agent
        query = f"Beschreibe den folgenden Hundeinstinkt: {instinct}"
        
        result = await query_agent_service.query(
            query=query,
            collection_name="Instinkt"
        )
        
        # Ergebnis extrahieren
        if "data" in result and result["data"]:
            # Je nach Struktur deiner Daten könnte dies angepasst werden müssen
            if "description" in result["data"]:
                return result["data"]["description"]
            elif "text" in result["data"]:
                return result["data"]["text"]
            else:
                # Versuche, das ganze data-Objekt zu serialisieren
                return json.dumps(result["data"])
        
        return None
    except Exception as e:
        print(f"⚠️ Fehler bei der Instinktsuche: {e}")
        return None


async def get_exercise_info(symptom: str, instinct: str) -> Optional[str]:
    """
    Sucht nach passenden Übungen für ein Hundeverhalten und einen Instinkt.
    
    Args:
        symptom: Das beschriebene Hundeverhalten
        instinct: Der identifizierte Instinkt
        
    Returns:
        Ein Text mit einer passenden Übung oder None, wenn nichts gefunden wurde
    """
    try:
        # Direktes Query an den Weaviate Query Agent
        query = f"Finde eine passende Übung für einen Hund mit aktivem {instinct}-Instinkt, der folgendes Verhalten zeigt: {symptom}"
        
        result = await query_agent_service.query(
            query=query,
            collection_name="Uebung"
        )
        
        # Ergebnis extrahieren
        if "data" in result and result["data"]:
            # Je nach Struktur deiner Daten könnte dies angepasst werden müssen
            if "exercise" in result["data"]:
                return result["data"]["exercise"]
            elif "text" in result["data"]:
                return result["data"]["text"]
            else:
                # Versuche, das ganze data-Objekt zu serialisieren
                return json.dumps(result["data"])
        
        return None
    except Exception as e:
        print(f"⚠️ Fehler bei der Übungssuche: {e}")
        return None