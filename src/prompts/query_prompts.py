# src/v2/prompts/query_prompts.py
"""
Weaviate query prompts for WuffChat V2.

These templates are used for vector searches and the Query Agent.
They help retrieve relevant information from the Weaviate collections.
"""

# ============================================================================
# BASIC SEARCH QUERIES
# ============================================================================

# Basic symptom search in Weaviate
SYMPTOM_QUERY_TEMPLATE = """Beschreibe das folgende Hundeverhalten: {symptom}"""

# Search for instinct information
INSTINCT_QUERY_TEMPLATE = """Beschreibe den folgenden Hundeinstinkt: {instinct}"""

# Search for matching exercises
EXERCISE_QUERY_TEMPLATE = """
Finde eine passende Übung für einen Hund mit aktivem {instinct}-Instinkt, 
der folgendes Verhalten zeigt: {symptom}
"""

# ============================================================================
# QUERY AGENT TEMPLATES
# ============================================================================

# Semantic search for dog perspective (not exact match!)
DOG_PERSPECTIVE_QUERY_TEMPLATE = """
Suche in der Symptome-Collection nach einem passenden Match für dieses Verhalten:
'{symptom}'

Falls ein Match gefunden: Gib NUR die "schnelldiagnose" aus der Hundeperspektive wieder. Nichts hinzufügen oder ändern.

Falls kein Match gefunden: Antworte nur mit "Zu diesem Verhalten habe ich leider noch keine Antwort." - keine eigene Beschreibung generieren.
"""

# Analyze behavior with context to identify instincts
INSTINCT_ANALYSIS_QUERY_TEMPLATE = """
Vergleiche diese Kombination aus Verhalten und Kontext mit den vier Instinktvarianten:
Verhalten: {symptom}
Zusätzlicher Kontext: {context}

Identifiziere den oder die führenden Instinkte (Jagd, Rudel, Territorial, Sexual).
Erkläre dann aus Hundesicht (Ich-Form), warum dieser Instinkt/diese Instinkte in dieser Situation aktiv ist/sind.

Halte die Erklärung einfach, emotional und vermeide Fachbegriffe.
"""

# Find appropriate exercise from Erziehung collection
EXERCISE_SEARCH_QUERY_TEMPLATE = """
Finde in der Erziehung-Collection eine passende Lernaufgabe für dieses Verhalten:
'{symptom}'

Die Übung sollte:
- konkret und praktisch umsetzbar sein
- dem Hundehalter klare Anweisungen geben
- möglichst auf den dominanten Instinkt abgestimmt sein

Formuliere eine klare, prägnante Anleitung.
"""

# ============================================================================
# COMPREHENSIVE QUERIES (For potential optimization)
# ============================================================================

# Combined query to get all information in one request
COMBINED_INSTINCT_QUERY_TEMPLATE = """
Für das Hundeverhalten: '{symptom}' mit Kontext: '{context}'

Bitte liefere die folgenden Informationen:
1. Welcher Hundeinstinkt ist hier am wahrscheinlichsten aktiv? (jagd, rudel, territorial, sexual)
2. Detaillierte Beschreibung dieses Instinkts
3. Kurze Beschreibungen ALLER vier Instinkte (jagd, rudel, territorial, sexual)
4. Eine passende Übung für dieses Verhalten und den identifizierten Instinkt

Formatiere die Antwort als JSON mit den Schlüsseln:
- "primary_instinct": Der wichtigste identifizierte Instinkt
- "primary_description": Beschreibung des Hauptinstinkts
- "all_instincts": {{"jagd": "...", "rudel": "...", "territorial": "...", "sexual": "..."}}
- "exercise": Eine konkrete Übung für den Hundebesitzer
- "confidence": Eine Zahl zwischen 0 und 1, die angibt, wie sicher die Identifikation ist
"""

# ============================================================================
# SPECIAL PURPOSE QUERIES
# ============================================================================

# General information fallback
GENERAL_INFO_QUERY_TEMPLATE = """
Beschreibe als Hund, wie ich folgendes Verhalten erlebe: {query}
"""

# Specific instinct perspective query
INSTINCT_PERSPECTIVE_QUERY_TEMPLATE = """
Gib mir die Hundeperspektive für den Instinkt '{instinct}' bezogen auf '{symptom}'. 
Antworte aus der Sicht des Hundes in Ich-Form.
"""

# Exercise by instinct type
INSTINCT_BASED_EXERCISE_QUERY_TEMPLATE = """
Welche konkrete Erziehungsaufgabe passt am besten zu dem Hundeverhalten '{symptom}' 
mit Bezug zum {instinct}-Instinkt? Gib eine klare Anleitung für den Hundehalter.
"""