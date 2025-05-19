# src/agents/companion_agent.py
import json
import os
import requests
import base64
from datetime import datetime, UTC
from pathlib import Path
from src.models.flow_models import AgentMessage
from src.core.config import settings  # Falls du die config.py wie vorgeschlagen implementiert hast

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

    async def save_feedback(self, session_id: str, responses: list[str], messages: list[AgentMessage]):
        """Speichert die Antworten im FS-Bucket oder lokal, je nach Konfiguration"""
        
        # Feedback-Daten erstellen
        feedback_data = {
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "responses": [
                {"question": q, "answer": a}
                for q, a in zip(self.feedback_questions, responses)
            ],
            "messages": [msg.model_dump() for msg in messages], 
        }
        
        # JSON-String erstellen
        json_data = json.dumps(feedback_data, ensure_ascii=False, indent=2)
        
        # Log-Informationen
        print(f"✅ Speichere Feedback für Session {session_id}")
        
        # Clever Cloud Bucket oder lokaler Pfad?
        fs_bucket = os.environ.get("CC_FS_BUCKET")
        base_path = os.environ.get("SESSION_LOG_PATH", "data")
        print(f"🔍 SESSION_LOG_PATH: {base_path}")
        print(f"🔍 CC_FS_BUCKET: {fs_bucket}")
        
        # Dateiname
        filename = f"feedback_{session_id}.json"
        
        try:
            if fs_bucket:
                # Speichern im Clever Cloud FS Bucket
                await self._save_to_fs_bucket(base_path, filename, json_data)
            else:
                # Lokale Speicherung
                await self._save_locally(base_path, filename, json_data)
                
            return True
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Feedbacks: {e} — Feedback wird nicht gespeichert.")
            return False
            
    async def _save_locally(self, base_path: str, filename: str, json_data: str):
        """Speichert Feedback lokal"""
        feedback_dir = Path(base_path)
        
        try:
            # Verzeichnis erstellen, falls es nicht existiert
            feedback_dir.mkdir(parents=True, exist_ok=True)
            
            # Datei schreiben
            file_path = feedback_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_data)
                
            print(f"✓ Feedback lokal gespeichert unter: {file_path}")
        except PermissionError as e:
            raise PermissionError(f"Kein Schreibzugriff auf {feedback_dir}: {e}")
        except Exception as e:
            raise Exception(f"Fehler beim lokalen Speichern: {e}")
    
    async def _save_to_fs_bucket(self, base_path: str, filename: str, json_data: str):
        """Speichert Feedback im Clever Cloud FS Bucket"""
        import aiohttp
        
        # FS Bucket URL und Credentials
        fs_bucket = os.environ.get("CC_FS_BUCKET")
        bucket_host = fs_bucket.split("://")[1] if "://" in fs_bucket else fs_bucket
        
        # API-Schlüssel und Secret aus Umgebungsvariablen holen
        # Diese müssen bei Clever Cloud konfiguriert sein!
        api_key = os.environ.get("BUCKET_KEY")
        api_secret = os.environ.get("BUCKET_PASSWORD")
        
        if not (api_key and api_secret):
            raise Exception("BUCKET_KEY und BUCKET_PASSWORD müssen als Umgebungsvariablen gesetzt sein!")
        
        # Auth-Header erstellen
        auth_string = f"{api_key}:{api_secret}"
        basic_auth = base64.b64encode(auth_string.encode()).decode()
        
        # Vollständigen Pfad im Bucket erstellen
        # Entferne führenden / falls vorhanden
        path_in_bucket = base_path[1:] if base_path.startswith("/") else base_path
        full_path = f"{path_in_bucket}/{filename}"
        
        url = f"https://{bucket_host}/{full_path}"
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/json"
        }
        
        print(f"🔍 Versuche zu speichern unter: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, data=json_data, headers=headers) as response:
                if response.status != 200 and response.status != 201:
                    error_text = await response.text()
                    raise Exception(f"Fehler beim Speichern im FS Bucket (Status {response.status}): {error_text}")
                    
        print(f"✓ Feedback im FS Bucket gespeichert unter: {full_path}")

    def get_intro_messages(self) -> list[AgentMessage]:
        return [
            AgentMessage(sender=self.role, text="Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst."),
            *[
                AgentMessage(sender=self.role, text=question)
                for question in self.feedback_questions
            ],
        ]