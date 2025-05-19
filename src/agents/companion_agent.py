# src/agents/companion_agent.py
import json
import os
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import List, Dict, Any
from src.models.flow_models import AgentMessage
from src.services.redis_service import RedisService

class CompanionAgent:
    def __init__(self):
        self.role = "companion"
        # DSGVO-konformere Formulierung der letzten Frage
        self.feedback_questions = [
            "Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?",
            "Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?",
            "Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?",
            "Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?",
            "Optional: Deine E-Mail oder Telefonnummer für eventuelle Rückfragen. Diese wird ausschließlich für Rückfragen zu deinem Feedback verwendet und nach 3 Monaten automatisch gelöscht.",
        ]
        # Redis-Service initialisieren
        self.redis_service = RedisService.get_instance()
        
        # Aufbewahrungsdauer in Tagen (z.B. 90 Tage = 3 Monate)
        self.retention_days = 90
        
    def _prepare_feedback_data(self, session_id: str, responses: List[str], messages: List[AgentMessage]) -> Dict[str, Any]:
        """
        Bereitet die Feedback-Daten zur Speicherung vor.
        """
        # Ablaufdatum berechnen (DSGVO-konform)
        expiration_date = (datetime.now(UTC) + timedelta(days=self.retention_days)).isoformat()
        
        # Feedback-Antworten vorbereiten
        prepared_responses = []
        
        for question, answer in zip(self.feedback_questions, responses):
            prepared_responses.append({
                "question": question,
                "answer": answer
            })
        
        # Feedback-Daten zusammenstellen
        return {
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "expiration_date": expiration_date,  # DSGVO-Löschfrist
            "responses": prepared_responses,
            "messages": [msg.model_dump() for msg in messages], 
        }

    async def save_feedback(self, session_id: str, responses: List[str], messages: List[AgentMessage]):
        """Speichert die Antworten in Redis mit DSGVO-konformer Ablaufzeit"""
        try:
            # Feedback-Daten vorbereiten
            feedback_data = self._prepare_feedback_data(session_id, responses, messages)
            
            print(f"✅ Speichere Feedback für Session {session_id}")
            
            # Redis-Schlüssel definieren
            redis_key = f"feedback:{session_id}"
            
            # Ablaufzeit in Sekunden berechnen (für Redis-Schlüsselablauf)
            expire_seconds = self.retention_days * 24 * 60 * 60
            
            # In Redis speichern MIT Ablaufzeit
            if self.redis_service.is_connected():
                success = self.redis_service.set(redis_key, feedback_data, expire=expire_seconds)
                
                if success:
                    print(f"✅ Feedback erfolgreich in Redis gespeichert: {redis_key}")
                    print(f"✅ Automatische Löschung nach {self.retention_days} Tagen eingestellt")
                    
                    # Zum Feedback-Index hinzufügen für einfache Abfrage aller Feedbacks
                    all_feedback_key = "all_feedback_ids"
                    all_ids = self.redis_service.get(all_feedback_key) or []
                    if session_id not in all_ids:
                        all_ids.append(session_id)
                        self.redis_service.set(all_feedback_key, all_ids)
                    
                    return
                else:
                    print("⚠️ Fehler beim Speichern in Redis")
            else:
                print("⚠️ Redis nicht verbunden, Feedback kann nicht gespeichert werden")
            
            # Lokale Speicherung als Fallback
            base_path = os.environ.get("SESSION_LOG_PATH", "data")
            feedback_dir = Path(base_path)
            
            try:
                # Verzeichnis erstellen, falls es nicht existiert
                feedback_dir.mkdir(parents=True, exist_ok=True)
                
                # Feedback als JSON speichern
                file_path = feedback_dir / f"feedback_{session_id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(feedback_data, f, ensure_ascii=False, indent=2)
                
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
        
    async def cleanup_expired_feedback(self):
        """Löscht abgelaufene Feedback-Daten (DSGVO-Compliance)"""
        if not self.redis_service.is_connected():
            print("⚠️ Redis nicht verbunden, Bereinigung nicht möglich")
            return
            
        all_ids = self.redis_service.get("all_feedback_ids") or []
        current_date = datetime.now(UTC)
        removed_ids = []
        
        for session_id in all_ids:
            feedback = self.redis_service.get(f"feedback:{session_id}")
            if not feedback:
                removed_ids.append(session_id)
                continue
                
            # Prüfen, ob das Ablaufdatum erreicht ist
            expiration_date = feedback.get("expiration_date")
            if expiration_date:
                try:
                    exp_date = datetime.fromisoformat(expiration_date)
                    if current_date > exp_date:
                        # Feedback löschen
                        self.redis_service.delete(f"feedback:{session_id}")
                        removed_ids.append(session_id)
                        print(f"🗑️ Abgelaufenes Feedback gelöscht: {session_id}")
                except (ValueError, TypeError):
                    pass
        
        # Bereinigte IDs aus dem Index entfernen
        if removed_ids:
            updated_ids = [id for id in all_ids if id not in removed_ids]
            self.redis_service.set("all_feedback_ids", updated_ids)
            print(f"🧹 {len(removed_ids)} abgelaufene Feedback-Einträge bereinigt")