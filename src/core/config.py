# src/core/config.py
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Grundlegende Anwendungseinstellungen"""
    APP_NAME: str = "HundeBot"
    DEBUG: bool = False
    
    # LLM-Einstellungen
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_APIKEY")
    
    # Vector-DB-Einstellungen
    WEAVIATE_URL: Optional[str] = Field(default=None)
    WEAVIATE_API_KEY: Optional[str] = Field(default=None)
    
    # Speicher-Einstellungen
    SESSION_LOG_PATH: str = "data"
    
    # RAG-Einstellungen
    DEFAULT_COLLECTION: str = "Symptom"
    TOP_K_RESULTS: int = 3
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Konfiguration als Singleton verfügbar machen
settings = Settings()

def validate_required_settings():
    """Prüft, ob alle notwendigen Einstellungen vorhanden sind"""
    missing = []
    
    if not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY/OPENAI_APIKEY")
    
    if not settings.WEAVIATE_URL:
        missing.append("WEAVIATE_URL")
    
    if not settings.WEAVIATE_API_KEY:
        missing.append("WEAVIATE_API_KEY")
    
    if missing:
        print(f"Warnung: Folgende Umgebungsvariablen fehlen: {', '.join(missing)}")
        print("Die Anwendung kann möglicherweise nicht alle Funktionen bereitstellen.")
        return False
    
    return True

# Beim Import prüfen
if not validate_required_settings():
    print("Überprüfe deine .zshrc oder setze die Umgebungsvariablen manuell.")