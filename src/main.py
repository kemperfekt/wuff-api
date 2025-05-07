# main.py

from orchestrator.flow_orchestrator import handle_symptom
from state.session_state import SessionState

# Beispiel-Sitzung
state = SessionState()

# Beispiel: Mensch beschreibt ein Symptom
symptom_input = "zieht an der Leine"
instinktvarianten = {
    "jagd": ["Fixiert dein Hund etwas in der Ferne?", "Zieht er los, wenn er eine Spur wittert?"],
    "rudel": ["Ist er besonders unruhig, wenn ihr getrennt seid?", "Läuft er gezielt zu bestimmten Menschen hin?"],
    "territorial": ["Reagiert er an bestimmten Orten besonders stark?", "Wirkt er wie ein 'Wächter'?"],
    "sexual": ["Ist er dabei angespannt gegenüber Hündinnen oder Rüden?", "Markiert er auffällig oft?"]
}

# FSM starten
messages = handle_symptom(symptom_input, instinktvarianten, state)

# Ausgabe
for msg in messages:
    print(f"[{msg.role}] {msg.content}")