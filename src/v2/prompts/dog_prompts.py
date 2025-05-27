# src/v2/prompts/dog_prompts.py
"""
Dog agent prompts for WuffChat V2.

These prompts handle the main conversation flow from the dog's perspective.
All content is in German as per the application requirements.
"""

# ============================================================================
# CONVERSATION FLOW PROMPTS
# ============================================================================

# Initial greeting when conversation starts
GREETING = """Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive."""

# Follow-up question to invite behavior description
GREETING_FOLLOWUP = """Erzähl mal, was ist denn bei euch los?"""

# When user input is too short or unclear
NEED_MORE_DETAIL = """Kannst Du das Verhalten bitte etwas ausführlicher beschreiben?"""

# After showing dog perspective, ask if user wants deeper analysis
ASK_FOR_MORE = """Magst Du mehr erfahren, warum ich mich so verhalte?"""

# When user confirms they want more information
ASK_FOR_CONTEXT = """Gut, dann brauche ich ein bisschen mehr Informationen. Bitte beschreibe, wie es zu der Situation kam, wer dabei war und was sonst noch wichtig sein könnte."""

# Not enough context provided
NEED_MORE_CONTEXT = """Ich brauch noch ein bisschen mehr Info… Wo war das genau, was war los?"""

# After diagnosis, offer exercise
ASK_FOR_EXERCISE = """Möchtest du eine Lernaufgabe, die dir in dieser Situation helfen kann?"""

# After providing exercise, ask if user wants to analyze another behavior
CONTINUE_OR_RESTART = """Möchtest du ein weiteres Hundeverhalten verstehen?"""

# Request yes/no clarification
REQUEST_YES_NO = """Magst du mir einfach 'Ja' oder 'Nein' sagen?"""

# Alternative yes/no requests for different contexts
REQUEST_YES_NO_EXERCISE = """Bitte antworte mit 'Ja' oder 'Nein' - möchtest du eine Lernaufgabe?"""
REQUEST_YES_NO_RESTART = """Sag einfach 'Ja' für ein neues Verhalten oder 'Nein' zum Beenden und Feedback geben."""

# ============================================================================
# RESPONSE COMPONENTS
# ============================================================================

# When no match found in Weaviate
NO_MATCH_FOUND = """Hmm, zu diesem Verhalten habe ich leider noch keine Antwort. Magst du ein anderes Hundeverhalten beschreiben?"""

# When behavior seems unrelated to dogs
NOT_DOG_RELATED = """Hm, das klingt für mich nicht nach typischem Hundeverhalten. Magst du es nochmal anders beschreiben?"""

# When ready to provide diagnosis
DIAGNOSIS_INTRO = """Danke. Wenn ich das mit meinem Instinkt vergleiche, sieht es so aus:"""

# Simple confirmation
OKAY_UNDERSTOOD = """Okay, kein Problem. Wenn du es dir anders überlegst, sag einfach Bescheid."""

# Another behavior request
ANOTHER_BEHAVIOR = """Super! Beschreibe mir bitte ein anderes Verhalten."""

# ============================================================================
# ERROR MESSAGES
# ============================================================================

# Technical error
TECHNICAL_ERROR = """Entschuldige, es ist ein Problem aufgetreten. Lass uns neu starten."""

# Processing error
PROCESSING_ERROR = """Entschuldige, ich hatte Schwierigkeiten, deine Anfrage zu verstehen. Magst du es noch einmal versuchen?"""

# ============================================================================
# SPECIAL CASES
# ============================================================================

# When user wants to restart
RESTART_CONFIRMED = """Okay, wir starten neu. Was möchtest du mir erzählen?"""

# Confused state fallback
CONFUSED_RESTART = """Ich bin kurz verwirrt… lass uns neu starten."""