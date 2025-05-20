# src/services/gpt_service.py
import os
from openai import AsyncOpenAI  # AsyncOpenAI statt OpenAI importieren
import aiohttp
import json
from typing import Dict, Any, Optional, List

# Zugriff über Umgebungsvariable OPENAI_APIKEY
client = AsyncOpenAI(api_key=os.getenv("OPENAI_APIKEY"))

# Synchrone Funktion komplett durch asynchrone Version ersetzen
async def ask_gpt(prompt: str, model: str = "gpt-4") -> str:
    """
    Sendet einen einfachen Prompt an GPT und gibt die Antwort als String zurück.
    Asynchrone Implementierung für bessere Performance.
    """
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher, empathischer Assistent."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ GPT-Fehler: {e}")
        return f"[GPT-Fehler] {str(e)}"

# Alte ask_gpt_async Funktion kann entfernt werden, da wir jetzt die Hauptfunktion asynchron gemacht haben

# diagnose_from_instinkte muss auch asynchron werden
async def diagnose_from_instinkte(symptom: str, varianten: dict) -> str:
    """
    Lässt GPT eine Einschätzung abgeben, welcher Instinkt am wahrscheinlichsten für das Verhalten verantwortlich ist.
    Asynchrone Implementierung.
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
    return await ask_gpt(prompt)

# validate_user_input auch asynchron machen
async def validate_user_input(text: str) -> bool:
    """
    Prüft, ob der Text etwas mit Hundeverhalten oder Hundetraining zu tun hat.
    Asynchrone Implementierung.
    """
    prompt = (
        "Antworte mit 'ja' oder 'nein'. "
        "Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?\n\n"
        f"{text}"
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().lower()
        return "ja" in answer
    except Exception as e:
        print(f"⚠️ GPT-Fehler bei Validierung: {e}")
        return True  # Fallback: lieber zulassen als blockieren