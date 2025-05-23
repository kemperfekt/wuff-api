# src/services/rag_service.py
import json
from typing import Dict, Any, Optional, List
from src.services.weaviate_service import query_agent_service
from src.services.gpt_service import ask_gpt
from src.core.error_handling import with_error_handling, RAGServiceError, GPTServiceError

# ✨ NEUE IMPORTS für PromptManager
from src.core.prompt_manager import get_prompt_manager, PromptType

# ❌ DIESER IMPORT KANN ENTFERNT WERDEN:
# from src.config.prompts import COMBINED_INSTINCT_QUERY_TEMPLATE

# Einfaches In-Memory-Cache für schnellere Antworten
_analysis_cache = {}
_dog_perspective_cache = {}

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
        Führt eine umfassende Analyse eines Hundeverhaltens durch mit dem Query Agent.
        Mit Caching für schnellere Antworten.
        """
        # Cache-Schlüssel generieren
        cache_key = f"{symptom}:{context}"
        
        # Cache prüfen
        if cache_key in _analysis_cache:
            print("✅ Lade Analyse aus Cache")
            return _analysis_cache[cache_key]
            
        # ✅ VORHER: Direkter Query-String im Code
        # ✨ NACHHER: PromptManager verwenden
        prompt_manager = get_prompt_manager()
        query = prompt_manager.get_prompt(
            PromptType.COMBINED_INSTINCT,
            symptom=symptom,
            context=context
        )
        
        # Instinktveranlagung-Collection für beste Ergebnisse
        result = await query_agent_service.query(
            query=query,
            collection_name="Instinktveranlagung"  # Änderung zur präziseren Collection
        )
        
        # Überprüfen auf Fehler
        if "error" in result and result["error"]:
            print(f"⚠️ Fehler bei der RAG-Analyse: {result['error']}")
            return get_fallback_analysis()
        
        # Daten aus dem Ergebnis extrahieren
        if "data" in result and result["data"]:
            # Versuche, strukturierte Daten aus der Antwort zu extrahieren
            try:
                # Wenn das Ergebnis ein String ist, versuche es zu parsen
                if isinstance(result["data"], str):
                    # Extrahiere die Informationen aus dem Text
                    text = result["data"]
                    
                    # Einfacher Parser für strukturierten Text
                    primary_instinct = None
                    primary_description = None
                    all_instincts = {}
                    exercise = None
                    confidence = 0.5
                    
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith("primary_instinct:") or line.startswith("- primary_instinct:"):
                            primary_instinct = line.split(":", 1)[1].strip()
                        elif line.startswith("primary_description:") or line.startswith("- primary_description:"):
                            primary_description = line.split(":", 1)[1].strip()
                        elif line.startswith("exercise:") or line.startswith("- exercise:"):
                            exercise = line.split(":", 1)[1].strip()
                        elif line.startswith("confidence:") or line.startswith("- confidence:"):
                            try:
                                confidence = float(line.split(":", 1)[1].strip())
                            except:
                                pass
                        elif "jagd" in line.lower():
                            all_instincts["jagd"] = line.split(":", 1)[1].strip() if ":" in line else line
                        elif "rudel" in line.lower():
                            all_instincts["rudel"] = line.split(":", 1)[1].strip() if ":" in line else line
                        elif "territorial" in line.lower():
                            all_instincts["territorial"] = line.split(":", 1)[1].strip() if ":" in line else line
                        elif "sexual" in line.lower():
                            all_instincts["sexual"] = line.split(":", 1)[1].strip() if ":" in line else line
                    
                    parsed_result = {
                        "primary_instinct": primary_instinct or "unbekannter Instinkt",
                        "primary_description": primary_description or "Keine Beschreibung verfügbar",
                        "all_instincts": all_instincts or {
                            "jagd": "Der Jagdinstinkt lässt mich Dinge verfolgen und fangen wollen.",
                            "rudel": "Der Rudelinstinkt regelt mein soziales Verhalten in der Gruppe.",
                            "territorial": "Der territoriale Instinkt lässt mich mein Gebiet und meine Ressourcen schützen.",
                            "sexual": "Der Sexualinstinkt steuert mein Fortpflanzungsverhalten."
                        },
                        "exercise": exercise or "Übe mit deinem Hund Impulskontrolle durch kurze, regelmäßige Trainingseinheiten.",
                        "confidence": confidence,
                        "success": True
                    }
                    
                    # Ergebnis cachen
                    _analysis_cache[cache_key] = parsed_result
                    return parsed_result
                    
                elif isinstance(result["data"], dict):
                    # Wenn das Ergebnis bereits ein Dict ist
                    parsed_result = {
                        "primary_instinct": result["data"].get("primary_instinct", "unbekannter Instinkt"),
                        "primary_description": result["data"].get("primary_description", "Keine Beschreibung verfügbar"),
                        "all_instincts": result["data"].get("all_instincts", {}),
                        "exercise": result["data"].get("exercise", "Keine Übung verfügbar"),
                        "confidence": result["data"].get("confidence", 0.5),
                        "success": True
                    }
                    
                    # Ergebnis cachen
                    _analysis_cache[cache_key] = parsed_result
                    return parsed_result
            except Exception as e:
                print(f"⚠️ Fehler bei der Verarbeitung der RAG-Antwort: {e}")
        
        # Fallback-Werte zurückgeben
        return get_fallback_analysis()
    
    @staticmethod
    @with_error_handling(GPTServiceError, "Als Hund spüre ich verschiedene innere Impulse. Manchmal ist es schwer, sie zu beschreiben, aber sie leiten mich in meinem Verhalten.")
    async def generate_dog_perspective(symptom: str, analysis: Dict[str, Any]) -> str:
        """
        Generiert eine Hundeperspektive basierend auf der RAG-Analyse.
        Mit Caching für schnellere Antworten.
        """
        # Cache-Schlüssel generieren
        primary_instinct = analysis.get("primary_instinct", "unbekannt")
        cache_key = f"{symptom}:{primary_instinct}"
        
        # Cache prüfen
        if cache_key in _dog_perspective_cache:
            print("✅ Lade Hundeperspektive aus Cache")
            return _dog_perspective_cache[cache_key]
        
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
        
        # Direkter Versuch, die Perspektive aus der Instinkte-Collection zu holen
        try:
            result = await query_agent_service.query(
                query=f"""
                Als Hund beschreibe ich, wie ich das folgende Verhalten aus meiner Sicht erlebe: '{symptom}'
                
                Der wahrscheinlichste Instinkt dahinter ist {primary_instinct}.
                
                Antworte als Hund in der ersten Person (Ich-Form). 
                Sei authentisch und emotional aus Hundesicht.
                Vermeide Fachbegriffe und sprich nicht über Menschen oder Training.
                """,
                collection_name="Instinkte"  # Primär in der Instinkte-Collection suchen
            )
            
            if "data" in result and result["data"]:
                # Ergebnis cachen
                _dog_perspective_cache[cache_key] = result["data"]
                return result["data"]
        except Exception as e:
            print(f"⚠️ Fehler bei der Instinkte-Abfrage: {e}")
        
        # GPT für die Textgenerierung nutzen als Fallback
        dog_view = await ask_gpt(prompt)
        
        # Ergebnis cachen
        _dog_perspective_cache[cache_key] = dog_view
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
