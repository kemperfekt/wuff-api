# src/core/config.py
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

class Settings(BaseSettings):
    """Grundlegende Anwendungseinstellungen"""
    APP_NAME: str = "WuffChat"
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
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Fehlende Umgebungsvariablen: {', '.join(missing)}")
        logger.warning("Die Anwendung kann möglicherweise nicht alle Funktionen bereitstellen.")
        return False
    
    return True

# Logging-Funktionen
def setup_logging():
    """Konfiguriert das Logging-System"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = Path(os.getenv("LOG_DIR", "logs"))

    # Sicherstellen, dass der Log-Ordner existiert (auch wenn er schon da ist)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Formatter erstellen
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console-Handler (einmalig anhängen)
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File-Handler (rotierend, max. 5 MB pro Datei, max. 5 Dateien)
    log_file = log_dir / 'wuffchat.log'
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_file) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Zusätzliche Logger für externe Bibliotheken einstellen
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    return root_logger

# Logger initialisieren
logger = setup_logging()
