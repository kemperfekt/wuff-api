# src/services/retrieval.py

from src.services.weaviate_service import search_relevant_chunks

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
