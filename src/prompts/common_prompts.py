# src/v2/prompts/common_prompts.py
"""
Common prompts and patterns for WuffChat V2.

These are shared response fragments, patterns, and utilities
used across different agents and services.
"""

# ============================================================================
# YES/NO PATTERNS
# ============================================================================

# Patterns to detect positive responses
YES_PATTERNS = [
    "ja",
    "ja gerne", 
    "ja bitte",
    "gerne",
    "klar",
    "natürlich",
    "sicher",
    "ok",
    "okay",
    "jo",
    "jap",
    "jup",
    "jawohl",
    "auf jeden fall",
    "sehr gerne"
]

# Patterns to detect negative responses
NO_PATTERNS = [
    "nein",
    "ne", 
    "nee",
    "nicht",
    "lieber nicht",
    "nein danke",
    "auf keinen fall",
    "niemals",
    "nö",
    "lass mal",
    "kein interesse",
    "vielleicht später"
]

# ============================================================================
# RESTART COMMANDS
# ============================================================================

# Commands that trigger a conversation restart
RESTART_COMMANDS = [
    "neu",
    "restart",
    "von vorne",
    "neustart",
    "nochmal",
    "reset",
    "neu anfangen",
    "von vorn"
]

# ============================================================================
# COMMON TRANSITIONS
# ============================================================================

# Smooth transition phrases
TRANSITION_THANKS = """Danke."""
TRANSITION_GOOD = """Gut."""
TRANSITION_OKAY = """Okay."""
TRANSITION_UNDERSTOOD = """Verstehe."""
TRANSITION_INTERESTING = """Interessant."""

# ============================================================================
# FORMATTING HELPERS
# ============================================================================

# Emoji and special characters
DOG_EMOJI = "🐾"
HEART_EMOJI = "❤️"
THINKING_EMOJI = "🤔"
CHECKMARK_EMOJI = "✅"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_yes_response(text: str) -> bool:
    """Check if text contains a positive response."""
    text_lower = text.lower().strip()
    return any(pattern in text_lower for pattern in YES_PATTERNS)

def is_no_response(text: str) -> bool:
    """Check if text contains a negative response."""
    text_lower = text.lower().strip()
    return any(pattern in text_lower for pattern in NO_PATTERNS)

def is_restart_command(text: str) -> bool:
    """Check if text contains a restart command."""
    text_lower = text.lower().strip()
    return any(command in text_lower for command in RESTART_COMMANDS)

def normalize_user_input(text: str) -> str:
    """Normalize user input for consistent processing."""
    # Remove extra whitespace
    text = " ".join(text.split())
    # Remove leading/trailing whitespace
    text = text.strip()
    return text