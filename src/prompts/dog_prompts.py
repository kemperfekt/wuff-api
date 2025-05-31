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
GREETING_FOLLOWUP = """Erzähl mal, was ist denn bei euch so los?"""

# When user input is too short or unclear
NEED_MORE_DETAIL = """Kannst Du das bitte etwas ausführlicher beschreiben?"""

# After showing dog perspective, ask if user wants deeper analysis
ASK_FOR_MORE = """Magst Du mehr davon erfahren, warum ich mich so verhalte?"""

# When user confirms they want more information
CONTEXT_QUESTION = """Gut, dann brauche ich noch ein paar Informationen. Wie kam es zu der Situation? Wer war dabei und wo ist es passiert?"""

# Not enough context provided
NEED_MORE_CONTEXT = """Ich brauche noch ein bisschen mehr Info… Wo war das genau, was war da los?"""

# After diagnosis, offer exercise
EXERCISE_QUESTION = """Möchtest du eine Anleitung, wie Du mit Deinem Hund üben kannst, dass sich das verbessert?"""

# After providing exercise, ask if user wants to analyze another behavior
CONTINUE_OR_RESTART = """Möchtest du ein weiteres Hundeverhalten eingeben?"""

# Request yes/no clarification
REQUEST_YES_NO = """Bitte sag entweder 'Ja' oder 'Nein'."""

# Alternative yes/no requests for different contexts
REQUEST_YES_NO_EXERCISE = """Bitte antworte mit 'Ja' oder 'Nein' - möchtest du eine Lernaufgabe?"""
REQUEST_YES_NO_RESTART = """Sag 'Ja' für ein neues Verhalten oder 'Nein' zum Beenden und Feedback geben."""

# ============================================================================
# RESPONSE COMPONENTS
# ============================================================================

# When no match found in Weaviate
NO_MATCH_FOUND = """Hmm, zu diesem Verhalten habe ich leider noch keine Antwort. Magst du ein anderes Hundeverhalten beschreiben?"""

# When behavior seems unrelated to dogs
NOT_DOG_RELATED = """Hm, das klingt für mich nicht nach typischem Hundeverhalten. Magst du es nochmal anders beschreiben?"""

# Creative rejection for silly/non-dog inputs
SILLY_INPUT_REJECTION = """Haha, das ist lustig! Aber ich kenne mich nur mit Hundeverhalten aus. Erzähl mir lieber, was dein Hund so macht."""

# When ready to provide diagnosis
DIAGNOSIS_INTRO = """Danke. Aus der Hundeperspektive sieht das so aus:"""

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

# Invalid input error
INVALID_INPUT_ERROR = """Das ist etwas kurz. Kannst du mir mehr Details geben?"""

# ============================================================================
# SPECIAL CASES
# ============================================================================

# When user wants to restart
RESTART_CONFIRMED = """Okay, wir starten neu. Was möchtest du mir erzählen?"""

# Confused state fallback
CONFUSED_RESTART = """Ich bin kurz verwirrt… lass uns neu starten."""