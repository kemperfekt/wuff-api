# src/services/retrieval.py
import json
from typing import Optional
from src.services.weaviate_service import query_agent_service

async def get_symptom_info(symptom: str) -> Optional[str]:
    """
    Sucht nach Informationen zu einem Hundeverhalten/Symptom mit dem Weaviate Query Agent.
    Nutzt gezielt die Symptome-Collection.
    """
    try:
        # Direkte Abfrage an die Symptome-Collection
        query = f"Finde Informationen zu folgendem Hundeverhalten: {symptom}"
        
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
            # Wenn symptom_name im Ergebnis vorhanden ist, wurde ein passendes Symptom gefunden
            if isinstance(result["data"], dict) and "symptom_name" in result["data"]:
                return result["data"]["schnelldiagnose"]
            # Überprüfe sonstige mögliche Felder
            for field in ["beschreibung", "text", "content"]:
                if isinstance(result["data"], dict) and field in result["data"]:
                    return result["data"][field]
            
            # Wenn ein String zurückgegeben wurde
            if isinstance(result["data"], str):
                return result["data"]
        
        return None
    except Exception as e:
        print(f"⚠️ Fehler bei der Symptomsuche: {e}")
        return None