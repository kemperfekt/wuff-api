# src/services/gpt_service.py

import os
from openai import OpenAI
import aiohttp
import json
from typing import Dict, Any, Optional, List

# Zugriff über Umgebungsvariable OPENAI_APIKEY
client = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))


def ask_gpt(prompt: str, model: str = "gpt-4") -> str:
    """
    Sendet einen einfachen Prompt an GPT und gibt die Antwort als String zurück.
    Geeignet für GPT-only-Anfragen ohne Kontext (kein RAG).
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher, empathischer Assistent."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT-Fehler] {str(e)}"


async def ask_gpt_async(prompt: str, model: str = "gpt-4") -> str:
    """
    Asynchrone Version von ask_gpt für die Verwendung in async-Funktionen.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher, empathischer Assistent."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT-Fehler] {str(e)}"


def diagnose_from_instinkte(symptom: str, varianten: dict) -> str:
    """
    Lässt GPT eine Einschätzung abgeben, welcher Instinkt am wahrscheinlichsten für das Verhalten verantwortlich ist.
    Fokus: einfache Sprache, keine Fachbegriffe, keine Instinktnamen nennen.
    """
    prompt = (
        "Ich bin ein Hund und habe folgendes Verhalten gezeigt:\n"
        f"{symptom}\n\n"
        "Mein Inneres erinnert sich an vier verschiedene Möglichkeiten, wie ich mich in so einer Situation fühlen könnte:\n\n"
        f"Jagd: {varianten.get('jagd', '')}\n"
        f"Rudel: {varianten.get('rudel', '')}\n"
        f"Territorial: {varianten.get('territorial', '')}\n"
        f"Sexual: {varianten.get('sexual', '')}\n\n"
        "Du bist ich – ein Hund. Erkläre dem Menschen, welcher dieser Impulse dich am besten beschreibt und warum. "
        "Vermeide Fachbegriffe, bleib bei deinem Gefühl. Keine Instinktnamen nennen. Sprich nicht über Menschen oder Training."
    )
    return ask_gpt(prompt)


# --- Neue Funktion zur Validierung von Nutzereingaben ---
def validate_user_input(text: str) -> bool:
    """
    Prüft, ob der Text etwas mit Hundeverhalten oder Hundetraining zu tun hat.
    Antwortet mit True, wenn ja – sonst False.
    """
    prompt = (
        "Antworte mit 'ja' oder 'nein'. "
        "Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?\n\n"
        f"{text}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().lower()
        return "ja" in answer
    except Exception as e:
        print(f"[GPT-Fehler bei Validierung] {e}")
        return True  # Fallback: lieber zulassen als blockieren


# -------------------------------------------------------------
# Weaviate Query Agent - Integration
# -------------------------------------------------------------
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


# -------------------------------------------------------------
# Kombinierte Funktionen - Weaviate Query Agent + GPT
# -------------------------------------------------------------
async def get_instinct_explanation(symptom: str, context: str, query_agent: WeaviateQueryAgentService) -> Dict[str, Any]:
    """
    Ermittelt den aktiven Instinkt mithilfe des Weaviate Query Agents und 
    lässt GPT eine hundefreundliche Erklärung generieren.
    
    Args:
        symptom: Das beschriebene Hundeverhalten
        context: Zusätzlicher Kontext zur Situation
        query_agent: Eine Instanz des WeaviateQueryAgentService
        
    Returns:
        Ein Dictionary mit Instinkt, Erklärung und weiteren Informationen
    """
    try:
        # 1. Instinkt-Informationen aus Weaviate holen
        query = f"Identifiziere den aktiven Instinkt bei diesem Hundeverhalten: '{symptom}'. Kontext: '{context}'"
        
        result = await query_agent.query(
            query=query,
            collection_name="Instinkt"  # Anpassen an deine Collection-Namen
        )
        
        # Standardwerte
        instinct_data = {
            "instinct": "unbekannter Instinkt",
            "description": "Ich kann nicht genau sagen, welcher Instinkt hier aktiv ist.",
            "confidence": 0.0
        }
        
        # Extrahiere Daten aus dem Ergebnis
        if "data" in result and result["data"]:
            instinct_data = {
                "instinct": result["data"].get("instinct", instinct_data["instinct"]),
                "description": result["data"].get("description", instinct_data["description"]),
                "confidence": result["data"].get("confidence", 0.7)
            }
        
        # 2. Instinktbeschreibungen für die verschiedenen Instinkte abrufen
        varianten = {}
        
        # Für den erkannten Instinkt und mögliche andere relevante Instinkte
        instinct_names = ["jagd", "rudel", "territorial", "sexual"]
        for instinct in instinct_names:
            try:
                query = f"Gib mir eine Beschreibung für den {instinct}-Instinkt bei Hunden"
                instinct_result = await query_agent.query(
                    query=query,
                    collection_name="Instinkt"
                )
                
                if "data" in instinct_result and instinct_result["data"]:
                    varianten[instinct] = instinct_result["data"].get("description", "")
            except Exception as e:
                print(f"⚠️ Fehler beim Abrufen der Beschreibung für {instinct}: {e}")
                varianten[instinct] = ""
        
        # 3. GPT nutzen, um die Erklärung in Hundesprache zu generieren
        # (deine bestehende Funktion diagnose_from_instinkte verwenden)
        dog_view = diagnose_from_instinkte(symptom, varianten)
        
        # Ergebnis zusammenstellen
        return {
            "instinct": instinct_data["instinct"],
            "technical_description": instinct_data["description"],
            "dog_view": dog_view,
            "confidence": instinct_data["confidence"]
        }
    
    except Exception as e:
        print(f"⚠️ Fehler bei der Instinkterklärung: {e}")
        return {
            "instinct": "unbekannter Instinkt",
            "technical_description": "Ich konnte keine Diagnose erstellen aufgrund eines technischen Problems.",
            "dog_view": "Es fällt mir schwer zu sagen, was in mir vorgeht. Manchmal sind meine Gefühle kompliziert.",
            "confidence": 0.0
        }


async def get_exercise_recommendation(instinct: str, symptom: str, query_agent: WeaviateQueryAgentService) -> Dict[str, Any]:
    """
    Generiert einen Übungsvorschlag für ein bestimmtes Hundeverhalten und einen identifizierten Instinkt
    
    Args:
        instinct: Der identifizierte Instinkt
        symptom: Das beschriebene Hundeverhalten
        query_agent: Eine Instanz des WeaviateQueryAgentService
        
    Returns:
        Ein Dictionary mit Übungsvorschlag und weiteren Informationen
    """
    try:
        # 1. Übung aus Weaviate abrufen
        query = f"Gib mir eine passende Übung für einen Hund mit aktivem {instinct}-Instinkt, der folgendes Verhalten zeigt: '{symptom}'"
        
        result = await query_agent.query(
            query=query,
            collection_name="Uebung"  # Anpassen an deine Collection-Namen
        )
        
        # Standardwerte
        exercise_data = {
            "exercise": f"Eine gute Übung bei aktivem {instinct}-Instinkt ist generell, mit dem Hund an seiner Impulskontrolle zu arbeiten.",
            "confidence": 0.5
        }
        
        # Extrahiere Daten aus dem Ergebnis
        if "data" in result and result["data"]:
            exercise = result["data"].get("exercise", "")
            if exercise:
                exercise_data["exercise"] = exercise
                exercise_data["confidence"] = result["data"].get("confidence", 0.7)
        
        # 2. GPT verwenden, um die Übung zu verbessern oder zu personalisieren
        if exercise_data["exercise"]:
            # Optional: GPT verwenden, um die Übung zu verbessern
            prompt = (
                f"Du bist ein erfahrener Hundetrainer. Ein Hund zeigt folgendes Verhalten: {symptom}.\n"
                f"Der {instinct}-Instinkt wurde als aktiv identifiziert.\n"
                f"Hier ist ein Übungsvorschlag: {exercise_data['exercise']}\n\n"
                "Formatiere diesen Übungsvorschlag so, dass er klar, freundlich und in 2-3 konkreten Schritten umsetzbar ist. "
                "Verwende einfache Sprache, aber achte auf fachliche Korrektheit."
            )
            
            improved_exercise = await ask_gpt_async(prompt)
            exercise_data["exercise"] = improved_exercise
        
        return exercise_data
    
    except Exception as e:
        print(f"⚠️ Fehler bei der Übungsgenerierung: {e}")
        return {
            "exercise": f"Eine bewährte Übung bei einem Hund mit aktivem {instinct} ist, dem Hund alternative, artgerechte Beschäftigungsmöglichkeiten anzubieten und klare Grenzen zu setzen.",
            "confidence": 0.0
        }