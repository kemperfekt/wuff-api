# src/services/retrieval.py

from src.services.weaviate_service import search_relevant_chunks

def get_symptom_info(symptom_text: str) -> str:
    """
    Fragt relevante Informationen zum Symptom über Weaviate ab und gibt sie als Klartext zurück.
    """
    chunks = search_relevant_chunks(symptom_text, class_name="Symptom")
    return "\n".join(chunks)
