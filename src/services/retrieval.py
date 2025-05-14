# src/services/retrieval.py

from src.services.weaviate_service import search_relevant_chunks
import json

def get_symptom_info(symptom_text: str) -> str:
    """
    Fragt relevante Informationen zum Symptom über Weaviate ab und gibt sie als Klartext zurück.
    """
    print("▶ get_symptom_info:", symptom_text)
    chunks = search_relevant_chunks(symptom_text, class_name="Symptom")
    print("🧠 Treffer (Symptom):", chunks)
    return chunks[0] if chunks else ""

def get_hundeperspektive(symptom_text: str) -> str:
    """
    Fragt relevante Hundeperspektive-Inhalte über Weaviate ab und gibt sie als Klartext zurück.
    """
    print("▶ get_hundeperspektive:", symptom_text)
    chunks = search_relevant_chunks(symptom_text, class_name="Hundeperspektive")
    print("🧠 Treffer (Hundeperspektive):", chunks)
    return "\n".join(chunks)

def get_instinktvarianten_for_symptom(symptom_text: str) -> dict:
    """
    Gibt die Instinktvarianten (jagd, rudel, territorial, sexual) zum Symptom als Dictionary zurück.
    """
    print("▶ get_instinktvarianten_for_symptom:", symptom_text)
    chunks = search_relevant_chunks(symptom_text, class_name="Symptom")
    if not chunks:
        print("⚠️ Kein Treffer.")
        return {}
    try:
        return json.loads(chunks[0])["instinkt_varianten"]
    except Exception as e:
        print("❌ Fehler beim Parsen:", e)
        return {}
