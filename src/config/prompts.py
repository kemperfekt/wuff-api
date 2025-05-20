# src/config/prompts.py

# GPT-Prompts
DOG_PERSPECTIVE_TEMPLATE = """
Ich bin ein Hund und habe dieses Verhalten gezeigt:
'{symptom}'

Hier ist eine Beschreibung aus ähnlichen Situationen:
{match}

Du bist ein Hund. Beschreibe ruhig und klar, wie du dieses Verhalten aus deiner Sicht erlebt hast. 
Sprich nicht über Menschen oder Trainingsmethoden. Nenne keine Instinkte beim Namen. Keine Fantasie. Keine Fachbegriffe.
"""

EXERCISE_TEMPLATE = """
Für folgendes Hundeverhalten:
'{symptom}'

Und folgende Beschreibung:
{match}

Generiere eine kurze, praktische Übung (2-3 Sätze), die einem Hundebesitzer helfen kann, 
dieses Verhalten besser zu verstehen oder positiv zu beeinflussen.
"""

INSTINCT_DIAGNOSIS_TEMPLATE = """
Ich bin ein Hund und habe folgendes Verhalten gezeigt:
{symptom}

Mein Inneres erinnert sich an vier verschiedene Möglichkeiten, wie ich mich in so einer Situation fühlen könnte:

Jagd: {jagd}
Rudel: {rudel}
Territorial: {territorial}
Sexual: {sexual}

Du bist ich – ein Hund. Erkläre dem Menschen, welcher dieser Impulse dich am besten beschreibt und warum. 
Vermeide Fachbegriffe, bleib bei deinem Gefühl. Keine Instinktnamen nennen. Sprich nicht über Menschen oder Training.
"""

VALIDATE_BEHAVIOR_TEMPLATE = """
Antworte mit 'ja' oder 'nein'. 
Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?

{text}
"""

# Weaviate Query Templates
SYMPTOM_QUERY_TEMPLATE = "Beschreibe das folgende Hundeverhalten: {symptom}"

INSTINCT_QUERY_TEMPLATE = "Beschreibe den folgenden Hundeinstinkt: {instinct}"

EXERCISE_QUERY_TEMPLATE = """
Finde eine passende Übung für einen Hund mit aktivem {instinct}-Instinkt, 
der folgendes Verhalten zeigt: {symptom}
"""

# Erweiterter Query für effizientere RAG
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