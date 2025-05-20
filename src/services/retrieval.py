# src/services/retrieval.py
import json
from typing import Optional
from src.services.weaviate_service import query_agent_service

# Diese Funktion war bereits async
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
        
        # Verbesserte Fehlerbehandlung
        if "error" in result and result["error"]:
            print(f"⚠️ Fehler bei der Symptomsuche: {result['error']}")
            return "Ich kann zu diesem Verhalten leider keine spezifischen Informationen finden."
        
        # Ergebnis extrahieren
        if "data" in result and result["data"]:
            # Überprüfe verschiedene mögliche Felder
            for field in ["text", "description", "content"]:
                if field in result["data"]:
                    return result["data"][field]
            
            # Wenn keines der erwarteten Felder vorhanden ist
            return json.dumps(result["data"])
        
        return "Ich habe leider keine passenden Informationen zu diesem Verhalten gefunden."
    except Exception as e:
        print(f"⚠️ Fehler bei der Symptomsuche: {e}")
        return "Es gab ein technisches Problem bei der Suche nach Informationen zu diesem Verhalten."