

# src/services/retrieval.py

from src.services.gpt_service import ask_gpt
from src.services.weaviate_service import search_relevant_chunks


def build_prompt_with_context(query: str, context_chunks: list[str]) -> str:
    """
    Baut einen Prompt aus einer Nutzerfrage und passenden Kontextstücken.
    """
    context = "\n\n".join(context_chunks)
    prompt = f"""Nutze die folgenden Informationen, um die Frage bestmöglich zu beantworten:

Kontext:
{context}

Frage:
{query}
"""
    return prompt


def ask_with_context(query: str, collection: str = "Symptom") -> str:
    """
    Holt passende Kontextinformationen aus Weaviate und stellt die Frage an GPT.
    """
    chunks = search_relevant_chunks(query, class_name=collection)
    if not chunks:
        return "[Fehler: Keine passenden Inhalte gefunden.]"

    prompt = build_prompt_with_context(query, chunks)
    return ask_gpt(prompt)
