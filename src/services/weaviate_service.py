# src/services/weaviate_service.py

import os
import aiohttp
import json
from typing import Dict, Any, Optional, List

class WeaviateQueryAgentService:
    """Service für die Interaktion mit dem Weaviate Query Agent"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialisiert den Service für den Weaviate Query Agent.
        
        Args:
            api_url: Die URL zum Query Agent Endpoint. Falls None, wird WEAVIATE_QUERY_AGENT_URL aus den Umgebungsvariablen verwendet.
            api_key: Der API-Key für den Query Agent. Falls None, wird WEAVIATE_QUERY_AGENT_KEY aus den Umgebungsvariablen verwendet.
        """
        self.api_url = api_url or os.getenv("WEAVIATE_QUERY_AGENT_URL")
        self.api_key = api_key or os.getenv("WEAVIATE_QUERY_AGENT_KEY")
        
        if not self.api_url:
            raise RuntimeError("WEAVIATE_QUERY_AGENT_URL nicht gesetzt")
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def query(self, query: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Sendet eine natürlichsprachliche Anfrage an den Weaviate Query Agent
        
        Args:
            query: Die Anfrage in natürlicher Sprache
            collection_name: Optional - Name der Collection, falls die Anfrage auf eine bestimmte Collection beschränkt werden soll
            
        Returns:
            Die Antwort des Query Agents
        """
        payload = {
            "query": query
        }
        
        if collection_name:
            payload["collection"] = collection_name
        
        print(f"🤖 Weaviate Query Agent Anfrage: '{query}'")
        print(f"🔗 Endpoint: {self.api_url}")
        if collection_name:
            print(f"📚 Collection: {collection_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=self.headers,
                    json=payload,
                    timeout=30  # 30 Sekunden Timeout
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise Exception(f"Fehler bei der Anfrage an den Weaviate Query Agent: {response.status} - {text}")
                    
                    result = await response.json()
                    print(f"✅ Query Agent Antwort erhalten: {result}")
                    return result
        except aiohttp.ClientError as e:
            print(f"⚠️ Fehler bei der Verbindung zum Weaviate Query Agent: {e}")
            raise Exception(f"Verbindungsfehler: {e}")
        except Exception as e:
            print(f"⚠️ Unerwarteter Fehler bei der Anfrage: {e}")
            raise


async def get_diagnosis(symptom: str, context: str, query_agent: WeaviateQueryAgentService) -> Dict[str, Any]:
    """
    Generiert eine Diagnose mithilfe des Weaviate Query Agents
    
    Args:
        symptom: Das beschriebene Hundeverhalten
        context: Zusätzlicher Kontext zur Situation
        query_agent: Eine Instanz des WeaviateQueryAgentService
        
    Returns:
        Ein Dictionary mit Instinkt, Erklärung und ggf. weiteren Informationen
    """
    try:
        query = f"Welcher Instinkt ist bei folgendem Hundeverhalten aktiv: '{symptom}'. Zusätzlicher Kontext: '{context}'"
        
        result = await query_agent.query(
            query=query,
            collection_name="Instinkt"  # Anpassen an deine Collection-Namen
        )
        
        # Standardrückgabe, falls keine aussagekräftigen Daten zurückkommen
        diagnosis = {
            "instinct": "unbekannter Instinkt",
            "explanation": "Ich kann nicht genau bestimmen, welcher Instinkt hier aktiv ist.",
            "confidence": 0.0
        }
        
        # Extrahiere relevante Daten aus dem Ergebnis
        if "data" in result and result["data"]:
            # Passe dies an das tatsächliche Format der Antwort an
            diagnosis = {
                "instinct": result["data"].get("instinct", diagnosis["instinct"]),
                "explanation": result["data"].get("explanation", diagnosis["explanation"]),
                "confidence": result["data"].get("confidence", 0.7)  # Default-Wert, falls nicht vorhanden
            }
        
        return diagnosis
    
    except Exception as e:
        print(f"⚠️ Fehler bei der Diagnose-Generierung: {e}")
        return {
            "instinct": "unbekannter Instinkt",
            "explanation": "Ich konnte keine Diagnose erstellen aufgrund eines technischen Problems.",
            "confidence": 0.0
        }


async def get_exercise(instinct: str, symptom: str, query_agent: WeaviateQueryAgentService) -> Dict[str, Any]:
    """
    Generiert einen Übungsvorschlag mithilfe des Weaviate Query Agents
    
    Args:
        instinct: Der identifizierte Instinkt
        symptom: Das beschriebene Hundeverhalten
        query_agent: Eine Instanz des WeaviateQueryAgentService
        
    Returns:
        Ein Dictionary mit der Übung und weiteren Informationen
    """
    try:
        query = f"Gib mir eine passende Übung für einen Hund mit aktivem {instinct}, der folgendes Verhalten zeigt: '{symptom}'"
        
        result = await query_agent.query(
            query=query,
            collection_name="Uebung"  # Anpassen an deine Collection-Namen
        )
        
        # Standardrückgabe, falls keine aussagekräftigen Daten zurückkommen
        exercise_result = {
            "exercise": f"Eine gute Übung bei aktivem {instinct} ist generell, mit dem Hund an seiner Impulskontrolle zu arbeiten.",
            "confidence": 0.5
        }
        
        # Extrahiere relevante Daten aus dem Ergebnis
        if "data" in result and result["data"]:
            # Passe dies an das tatsächliche Format der Antwort an
            exercise = result["data"].get("exercise", "")
            if exercise:
                exercise_result["exercise"] = exercise
                exercise_result["confidence"] = result["data"].get("confidence", 0.7)  # Default-Wert, falls nicht vorhanden
        
        return exercise_result
    
    except Exception as e:
        print(f"⚠️ Fehler bei der Übungs-Generierung: {e}")
        return {
            "exercise": "Ich empfehle, mit einem Hundetrainer zu sprechen, um eine passende Übung für dieses Verhalten zu finden.",
            "confidence": 0.0
        }