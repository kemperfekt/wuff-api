# src/v2/prompts/companion_prompts.py
"""
Companion agent prompts for WuffChat V2.

These prompts handle the feedback collection process at the end
of conversations. GDPR-compliant and user-friendly.
"""

# ============================================================================
# FEEDBACK INTRODUCTION
# ============================================================================

FEEDBACK_INTRO = """Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst."""

# ============================================================================
# FEEDBACK QUESTIONS
# ============================================================================

# Question 1: Overall helpfulness
FEEDBACK_Q1 = """Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?"""

# Question 2: Dog perspective experience
FEEDBACK_Q2 = """Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?"""

# Question 3: Exercise appropriateness
FEEDBACK_Q3 = """Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?"""

# Question 4: NPS (Net Promoter Score)
FEEDBACK_Q4 = """Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?"""

# Question 5: Contact info (GDPR-compliant)
FEEDBACK_Q5 = """Optional: Deine E-Mail oder Telefonnummer für eventuelle Rückfragen. Diese wird ausschließlich für Rückfragen zu deinem Feedback verwendet und nach 3 Monaten automatisch gelöscht."""

# ============================================================================
# FEEDBACK RESPONSES
# ============================================================================

# Thank you message after feedback completion
FEEDBACK_COMPLETE = """Danke für Dein Feedback! 🐾"""

# If user skips feedback
FEEDBACK_SKIPPED = """Kein Problem! Danke, dass du WuffChat genutzt hast. 🐾"""

# ============================================================================
# FEEDBACK COLLECTION LIST (for easy iteration)
# ============================================================================

FEEDBACK_QUESTIONS = [
    FEEDBACK_Q1,
    FEEDBACK_Q2,
    FEEDBACK_Q3,
    FEEDBACK_Q4,
    FEEDBACK_Q5
]