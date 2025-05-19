# src/agents/companion_agent.py
import json
import os
import base64
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional

# AgentMessage importieren
from src.models.flow_models import AgentMessage

class CompanionAgent:
    def __init__(self):
        self.role = "companion"
        self.feedback_questions = [
            "Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?",
            "Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?",
            "Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?",
            "Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?",
            "Magst Du Deine E-Mail oder Telefonnummer für Rückfragen dalassen?",
        ]

    async def save_feedback(self, session_id: str, responses: List[str], messages: List[AgentMessage]):
        """Speichert die Antworten als JSON-Datei im FS Bucket oder lokal"""
        try:
            base_path = os.environ.get("SESSION_LOG_PATH", "data")
            feedback_dir = Path(base_path)
            feedback_data = {
                "session_id": session_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "responses": [
                    {"question": q, "answer": a}
                    for q, a in zip(self.feedback_questions, responses)
                ],
                "messages": [msg.model_dump() for msg in messages], 
            }
            print(f"✅ Speichere Feedback für Session {session_id}")
            print(f"🔍 SESSION_LOG_PATH: {base_path}")
            
            # JSON-Daten vorbereiten
            json_content = json.dumps(feedback_data, ensure_ascii=False, indent=2)
            
            # Prüfen, ob FS Bucket konfiguriert ist
            bucket_host = os.environ.get("BUCKET_HOST")
            bucket_username = os.environ.get("BUCKET_FTP_USERNAME")
            bucket_password = os.environ.get("BUCKET_FTP_PASSWORD")
            
            # Umgebungsvariablen ausgeben (für Debugging)
            print(f"🔍 BUCKET_HOST: {bucket_host}")
            print(f"🔍 BUCKET_FTP_USERNAME: {'gesetzt' if bucket_username else 'nicht gesetzt'}")
            print(f"🔍 BUCKET_FTP_PASSWORD: {'gesetzt' if bucket_password else 'nicht gesetzt'}")
            
            if bucket_host and bucket_username and bucket_password:
                # FS Bucket Speicherung verwenden
                try:
                    print(f"🪣 Speichere in FS Bucket: {bucket_host}")
                    
                    # requests importieren (falls nicht installiert: pip install requests)
                    import requests
                    
                    # Auth Header erstellen
                    auth_string = f"{bucket_username}:{bucket_password}"
                    auth_encoded = base64.b64encode(auth_string.encode()).decode()
                    
                    # URL für die Speicherung
                    # Entferne führenden Slash, falls vorhanden
                    clean_base_path = base_path.lstrip("/")
                    path_in_bucket = f"{clean_base_path}/feedback_{session_id}.json"
                    url = f"https://{bucket_host}/{path_in_bucket}"
                    
                    print(f"🔗 Speicherpfad: {url}")
                    
                    # Datei hochladen
                    response = requests.put(
                        url,
                        data=json_content,
                        headers={
                            "Authorization": f"Basic {auth_encoded}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    print(f"📊 HTTP Status: {response.status_code}")
                    
                    if response.status_code not in [200, 201]:
                        raise Exception(f"HTTP-Fehler: {response.status_code} - {response.text}")
                    
                    print(f"✅ Feedback erfolgreich im FS Bucket gespeichert: {path_in_bucket}")
                    return
                except Exception as e:
                    print(f"⚠️ Fehler bei der FS Bucket Speicherung: {e}")
                    print("⚠️ Falle zurück auf lokale Speicherung...")
            else:
                if bucket_host:
                    print("⚠️ BUCKET_FTP_USERNAME und BUCKET_FTP_PASSWORD müssen als Umgebungsvariablen gesetzt sein!")
                    print("⚠️ Falle zurück auf lokale Speicherung...")
                else:
                    print("ℹ️ Kein FS Bucket konfiguriert, verwende lokale Speicherung")
            
            # Lokale Speicherung als Fallback
            try:
                # Verzeichnis erstellen, falls es nicht existiert
                feedback_dir.mkdir(parents=True, exist_ok=True)
                
                # Lokale Datei schreiben
                file_path = feedback_dir / f"feedback_{session_id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_content)
                
                print(f"✅ Feedback lokal gespeichert: {file_path}")
            except Exception as e:
                print(f"❌ Fehler bei der lokalen Speicherung: {e}")
                raise
        
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Feedbacks: {e} — Feedback wird nicht gespeichert.")

    def get_intro_messages(self) -> List[AgentMessage]:
        return [
            AgentMessage(sender=self.role, text="Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst."),
            *[
                AgentMessage(sender=self.role, text=question)
                for question in self.feedback_questions
            ],
        ]