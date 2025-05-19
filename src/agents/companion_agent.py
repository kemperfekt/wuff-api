# In companion_agent.py (angepasste save_feedback-Methode)

async def save_feedback(self, session_id: str, responses: list[str], messages: list[AgentMessage]):
    """Speichert die Antworten als JSON-Datei im durch SESSION_LOG_PATH definierten Verzeichnis"""
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
        fs_bucket = os.environ.get("CC_FS_BUCKET")
        fs_username = os.environ.get("CC_FS_USERNAME")  # Geändert von BUCKET_KEY
        fs_password = os.environ.get("CC_FS_PASSWORD")   # Geändert von BUCKET_PASSWORD
        
        # Umgebungsvariablen ausgeben (für Debugging)
        print(f"🔍 FS Bucket: {fs_bucket}")
        print(f"🔍 FS Username: {'gesetzt' if fs_username else 'nicht gesetzt'}")
        print(f"🔍 FS Password: {'gesetzt' if fs_password else 'nicht gesetzt'}")
        
        if fs_bucket and fs_username and fs_password:
            # FS Bucket Speicherung verwenden
            try:
                print(f"🪣 Speichere in FS Bucket: {fs_bucket}")
                
                import requests
                import base64
                
                # Auth Header erstellen
                auth_string = f"{fs_username}:{fs_password}"
                auth_encoded = base64.b64encode(auth_string.encode()).decode()
                
                # URL für die Speicherung
                # Entferne führenden Slash, falls vorhanden
                clean_base_path = base_path.lstrip("/")
                path_in_bucket = f"{clean_base_path}/feedback_{session_id}.json"
                url = f"https://{fs_bucket}/{path_in_bucket}"
                
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
            if fs_bucket:
                print("⚠️ CC_FS_USERNAME und CC_FS_PASSWORD müssen als Umgebungsvariablen gesetzt sein!")
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