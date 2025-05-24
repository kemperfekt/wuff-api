# src/v2/prompts/validation_prompts.py
"""
Validation and error prompts for WuffChat V2.

These prompts handle input validation, error messages, and 
filtering out inappropriate content.
"""

# ============================================================================
# INPUT VALIDATION
# ============================================================================

# Check if user input is related to dogs/dog training
VALIDATE_BEHAVIOR_TEMPLATE = """
Antworte mit 'ja' oder 'nein'. 
Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?

{text}
"""

# ============================================================================
# ERROR MESSAGES - TECHNICAL
# ============================================================================

# GPT service errors
GPT_ERROR = """Entschuldige, ich habe gerade technische Schwierigkeiten. Bitte versuche es gleich nochmal."""

# Weaviate/database errors
DATABASE_ERROR = """Ich kann gerade nicht auf mein Gedächtnis zugreifen. Bitte versuche es später noch einmal."""

# Redis/cache errors (non-critical)
CACHE_ERROR = """Es gibt ein Problem beim Speichern. Deine Eingabe wurde aber verarbeitet."""

# General technical error
TECHNICAL_ERROR = """Es ist ein unerwarteter Fehler aufgetreten. Bitte versuche es später noch einmal."""

# Configuration error
CONFIG_ERROR = """Es gibt ein technisches Problem. Bitte kontaktiere den Support."""

# ============================================================================
# ERROR MESSAGES - USER INPUT
# ============================================================================

# Input not understood
INPUT_NOT_UNDERSTOOD = """Ich habe deine Eingabe nicht verstanden. Kannst du es anders formulieren?"""

# Input too short
INPUT_TOO_SHORT = """Das ist etwas kurz. Kannst du mir mehr Details geben?"""

# Not dog-related
NOT_DOG_RELATED = """Das scheint nichts mit Hunden zu tun zu haben. Bitte beschreibe ein Hundeverhalten oder eine Situation mit deinem Hund."""

# Invalid yes/no response
INVALID_YES_NO = """Ich verstehe deine Antwort nicht. Bitte antworte mit 'Ja' oder 'Nein'."""

# ============================================================================
# FLOW ERRORS
# ============================================================================

# Lost context/confused state
FLOW_CONFUSED = """Ups, ich bin durcheinander gekommen. Lass uns nochmal von vorne anfangen."""

# No behavior match found
NO_BEHAVIOR_MATCH = """Ich konnte dieses Verhalten nicht einordnen. Magst du es anders beschreiben oder ein anderes Verhalten nennen?"""

# ============================================================================
# USER-FRIENDLY ERROR MAPPING
# ============================================================================

# Maps technical errors to user-friendly messages
ERROR_MESSAGE_MAP = {
    "GPTServiceError": GPT_ERROR,
    "WeaviateServiceError": DATABASE_ERROR,
    "RedisServiceError": CACHE_ERROR,
    "ValidationError": INPUT_NOT_UNDERSTOOD,
    "FlowError": FLOW_CONFUSED,
    "ConfigurationError": CONFIG_ERROR,
    "default": TECHNICAL_ERROR
}