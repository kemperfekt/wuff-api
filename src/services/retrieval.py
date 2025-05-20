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
        # Query in natürlicher Sprache an die Symptome-Collection
        query = f"Beschreibe das folgende Hundeverhalten kurz und präzise: {symptom}"
        
        result = await query_agent_service.query(
            query=query,
            collection_name="Symptome"  # Gezielt in Symptome-Collection suchen
        )
        
        # Fehlerbehandlung
        if "error" in result and result["error"]:
            print(f"⚠️ Fehler bei der Symptomsuche: {result['error']}")
            return None
        
        # Ergebnis extrahieren
        if "data" in result and result["data"]:
            return result["data"]
        
        return None
    except Exception as e:
        print(f"⚠️ Fehler bei der Symptomsuche: {e}")
        return None