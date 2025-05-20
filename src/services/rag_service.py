# src/services/rag_service.py
import json
from typing import Dict, Any, Optional, List
from src.services.weaviate_service import query_agent_service
from src.config.prompts import COMBINED_INSTINCT_QUERY_TEMPLATE
from src.services.gpt_service import ask_gpt
from src.core.error_handling import with_error_handling, RAGServiceError, GPTServiceError

# Fallback-Analyse außerhalb der Klasse definieren
def get_fallback_analysis() -> Dict[str, Any]:
    """Gibt eine Fallback-Analyse zurück, wenn ein Fehler auftritt"""
    return {
        "primary_instinct": "unbekannter Instinkt",
        "primary_description": "Ich konnte keine Diagnose erstellen aufgrund eines technischen Problems.",
        "all_instincts": {
            "jagd": "Der Jagdinstinkt lässt mich Dinge verfolgen und fangen wollen.",
            "rudel": "Der Rudelinstinkt regelt mein soziales Verhalten in der Gruppe.",
            "territorial": "Der territoriale Instinkt lässt mich mein Gebiet und meine Ressourcen schützen.",
            "sexual": "Der Sexualinstinkt steuert mein Fortpflanzungsverhalten."
        },
        "exercise": "Eine grundlegende Übung ist, mit dem Hund an seiner Impulskontrolle zu arbeiten und klare Grenzen zu setzen.",
        "confidence": 0.3,
        "success": False
    }

class RAGService:
    """Verbesserte RAG-Service-Klasse für effiziente Weaviate-Abfragen"""
    
    @staticmethod
    @with_error_handling(RAGServiceError, get_fallback_analysis())
    async def get_comprehensive_analysis(symptom: str, context: str = "") -> Dict[str, Any]:
        """
        Führt eine umfassende Analyse eines Hundeverhaltens durch mit einer einzigen Abfrage.
        Kombiniert Instinkt-Identifikation, Beschreibungen und Übungsvorschläge.
        
        Args:
            symptom: Das beschriebene Hundeverhalten
            context: Zusätzlicher Kontext zur Situation
            
        Returns:
            Ein Dictionary mit allen relevanten Informationen
        """
        # Eine einzige, komplexe Abfrage statt mehrerer einzelner
        query = COMBINED_INSTINCT_QUERY_TEMPLATE.format(
            symptom=symptom,
            context=context
        )
        
        result = await query_agent_service.query(
            query=query,
            collection_name="Instinkt"  # Optional, könnte auch mehrere Collections durchsuchen
        )
        
        # Überprüfen auf Fehler
        if "error" in result and result["error"]:
            print(f"⚠️ Fehler bei der RAG-Analyse: {result['error']}")
            return get_fallback_analysis()
        
        # Daten aus dem Ergebnis extrahieren
        if "data" in result and result["data"]:
            return {
                "primary_instinct": result["data"].get("primary_instinct", "unbekannter Instinkt"),
                "primary_description": result["data"].get("primary_description", "Keine Beschreibung verfügbar"),
                "all_instincts": result["data"].get("all_instincts", {}),
                "exercise": result["data"].get("exercise", "Keine Übung verfügbar"),
                "confidence": result["data"].get("confidence", 0.5),
                "success": True
            }
        
        return get_fallback_analysis()
    
    @staticmethod
    @with_error_handling(GPTServiceError, "Als Hund spüre ich verschiedene innere Impulse. Manchmal ist es schwer, sie zu beschreiben, aber sie leiten mich in meinem Verhalten.")
    async def generate_dog_perspective(symptom: str, analysis: Dict[str, Any]) -> str:
        """
        Generiert eine Hundeperspektive basierend auf der RAG-Analyse.
        
        Args:
            symptom: Das beschriebene Hundeverhalten
            analysis: Die Ergebnisse der RAG-Analyse
            
        Returns:
            Eine textuelle Beschreibung aus Hundesicht
        """
        # Varianten für die verschiedenen Instinkte vorbereiten
        varianten = analysis.get("all_instincts", {})
        
        # Wenn die Varianten leer sind, Fallback verwenden
        if not varianten:
            varianten = {
                "jagd": "Ich will etwas fangen oder verfolgen",
                "rudel": "Ich will meinen Platz in der Gruppe finden",
                "territorial": "Ich will meinen Bereich schützen",
                "sexual": "Ich folge meinem Fortpflanzungstrieb"
            }
        
        # Prompt für die Hundeperspektive
        prompt = f"""
        Ich bin ein Hund und habe dieses Verhalten gezeigt:
        '{symptom}'
        
        Der wahrscheinlichste Instinkt ist: {analysis.get('primary_instinct', 'unbekannt')}
        Mit dieser Beschreibung: {analysis.get('primary_description', '')}
        
        Die möglichen Instinkte sind:
        Jagd: {varianten.get('jagd', '')}
        Rudel: {varianten.get('rudel', '')}
        Territorial: {varianten.get('territorial', '')}
        Sexual: {varianten.get('sexual', '')}
        
        Du bist ich – ein Hund. Erkläre dem Menschen, wie du dieses Verhalten aus deiner Sicht erlebst.
        Vermeide Fachbegriffe, bleib bei deinem Gefühl. Nenne keine Instinktnamen. Sprich nicht über Menschen oder Training.
        """
        
        # GPT für die Textgenerierung nutzen
        dog_view = await ask_gpt(prompt)
        return dog_view
    
    @staticmethod
    async def batch_query(questions: List[Dict[str, str]], collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Führt mehrere Abfragen in einem Batch aus, um die Anzahl der API-Aufrufe zu reduzieren.
        
        Args:
            questions: Liste von Dictionaries im Format {"id": "unique_id", "query": "abfragetext"}
            collection_name: Optional, der Name der Collection
            
        Returns:
            Dictionary mit Antworten, wobei die Schlüssel die IDs aus den Fragen sind
        """
        try:
            combined_query = "Beantworte folgende Fragen im JSON-Format mit einem Feld für jede Frage-ID:\n\n"
            
            for q in questions:
                combined_query += f"Frage '{q['id']}': {q['query']}\n"
            
            combined_query += "\nFormatiere die Antwort als JSON-Objekt mit den Frage-IDs als Schlüssel."
            
            result = await query_agent_service.query(
                query=combined_query,
                collection_name=collection_name
            )
            
            if "error" in result and result["error"]:
                print(f"⚠️ Fehler bei der Batch-Abfrage: {result['error']}")
                return {"error": result["error"]}
            
            if "data" in result and result["data"]:
                # Versuche, das Ergebnis als strukturiertes JSON zu interpretieren
                try:
                    if isinstance(result["data"], dict):
                        return result["data"]
                    else:
                        return json.loads(result["data"])
                except (json.JSONDecodeError, TypeError):
                    # Wenn das nicht funktioniert, gib das Ergebnis als Rohtext zurück
                    return {"raw_result": result["data"]}
            
            return {"error": "Keine Daten in der Antwort"}
        except Exception as e:
            print(f"⚠️ Fehler bei der Batch-Abfrage: {e}")
            return {"error": str(e)}