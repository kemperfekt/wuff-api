# src/core/config.py
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Grundlegende Anwendungseinstellungen"""
    APP_NAME: str = "WuffChat"
    DEBUG: bool = False
    
    # LLM-Einstellungen
    # Beachte die drei möglichen Umgebungsvariablen für den OpenAI API Key
    OPENAI_API_KEY: Optional[str] = Field(None, env=["OPENAI_API_KEY", "OPENAI_APIKEY", "OPENAIAPIKEY"])
    
    # Vector-DB-Einstellungen
    WEAVIATE_URL: Optional[str] = Field(None, env=["WEAVIATE_URL", "WEAVIATE_HOST"])
    WEAVIATE_API_KEY: Optional[str] = Field(None, env=["WEAVIATE_API_KEY", "WEAVIATE_APIKEY", "WEAVIATE_KEY"])
    
    # Speicher-Einstellungen
    SESSION_LOG_PATH: str = "data"
    
    # RAG-Einstellungen
    DEFAULT_COLLECTION: str = "Symptom"
    TOP_K_RESULTS: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Für zusätzliche Flexibilität

# Konfiguration als Singleton verfügbar machen
settings = Settings()

def validate_required_settings():
    """Prüft, ob alle notwendigen Einstellungen vorhanden sind"""
    missing = []
    
    if not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY/OPENAI_APIKEY/OPENAIAPIKEY")
    
    if not settings.WEAVIATE_URL:
        missing.append("WEAVIATE_URL/WEAVIATE_HOST")
    
    if not settings.WEAVIATE_API_KEY:
        missing.append("WEAVIATE_API_KEY/WEAVIATE_APIKEY/WEAVIATE_KEY")
    
    if missing:
        print(f"Warnung: Folgende Umgebungsvariablen fehlen: {', '.join(missing)}")
        print("Die Anwendung kann möglicherweise nicht alle Funktionen bereitstellen.")
        return False
    
    return True

# Beim Import prüfen
if not validate_required_settings():
    print("Überprüfe deine .zshrc oder setze die Umgebungsvariablen manuell.")