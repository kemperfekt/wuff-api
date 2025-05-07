# src/services/gpt_service.py

import os
from openai import OpenAI

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