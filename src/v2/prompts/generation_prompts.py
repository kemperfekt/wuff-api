# src/v2/prompts/generation_prompts.py
"""
GPT generation prompts for WuffChat V2.

These templates are used to generate responses via GPT-4, taking
Weaviate content and making it more conversational.
"""

# ============================================================================
# DOG PERSPECTIVE GENERATION
# ============================================================================

# Takes Weaviate content and makes it more conversational from dog's perspective
DOG_PERSPECTIVE_TEMPLATE = """
Ich bin ein Hund und habe dieses Verhalten gezeigt:
'{symptom}'

Hier ist eine Beschreibung aus ähnlichen Situationen:
{match}

Du bist ein Hund. Beschreibe ruhig und klar, wie du dieses Verhalten aus deiner Sicht erlebt hast. 
Sprich nicht über Menschen oder Trainingsmethoden. Nenne keine Instinkte beim Namen. Keine Fantasie. Keine Fachbegriffe.
"""

# ============================================================================
# INSTINCT DIAGNOSIS GENERATION
# ============================================================================

# Analyzes which instinct drives the behavior
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

# ============================================================================
# EXERCISE GENERATION
# ============================================================================

# Generates a practical exercise for the dog owner
EXERCISE_TEMPLATE = """
Für folgendes Hundeverhalten:
'{symptom}'

Und folgende Beschreibung:
{match}

Generiere eine kurze, praktische Übung (2-3 Sätze), die einem Hundebesitzer helfen kann, 
dieses Verhalten besser zu verstehen oder positiv zu beeinflussen.
"""

# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

# Base system prompt for dog agent
DOG_AGENT_SYSTEM = """Du bist ein hilfreicher, empathischer Assistent."""

# System prompt for exercise generation
EXERCISE_SYSTEM = """Du bist ein erfahrener Hundetrainer, der praktische und umsetzbare Übungen erstellt."""