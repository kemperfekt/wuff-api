# src/v2/core/logging_config.py
"""Logging configuration for V2 - copied from V1 to remove dependency"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


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
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Spezielle Logger-Konfigurationen
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root_logger