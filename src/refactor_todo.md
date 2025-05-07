# 📋 DogBot Refactoring – Offene Aufgaben (ToDo-Liste)

## ✅ Phase 1 – Clean Core (Agenten, GPT, RAG)

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| Neue Projektstruktur `src/` angelegt | ✅ | erledigt |
| `BaseAgent` erstellt | ✅ | mit RAG + GPT-Option |
| `AgentMessage` erstellt | ✅ | `flow_models.py` |
| `gpt_service.py` erstellt | ✅ | GPT-Call abstrahiert |
| `retrieval.py` erstellt | ✅ | RAG-Wrapper mit Fallback |
| `weaviate_service.py` erstellt | ✅ | Verbindung + Suche aktiv |
| `search_relevant_chunks`: Feld 'text' dynamisch machen | 🔜 | aktuell nur `"text"` → später evtl. `"beschreibung"`, `"antwort"` o. Ä. |
| Tests für `BaseAgent` schreiben | ⏳ | folgt nach `CoachAgent` |
| Logging in GPT-/Weaviate-Service integrieren | ⏳ | optional für Debugging |

## 🔄 Phase 2 – Agentenlogik migrieren

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `CoachAgent` neu aufbauen (ohne Scoring) | 🔜 | MVP-gerecht, nur Rückfragenlogik |
| Agenten-Ein/Ausgabe mit Pydantic vereinheitlichen | ⏳ | später hilfreich für Validierung, aber aktuell nicht notwendig |
| `DogAgent` migrieren | ⏳ | folgt nach `CoachAgent` |
| Unnötige Altlogik in Coach/Dog nicht übernehmen | 🔄 | wird selektiv entschieden |
| RAG-Class „Symptom“ konfigurierbar machen | ⏳ | aktuell hardcodiert |

## 🔁 Phase 3 – Flow / Orchestrierung

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `flow_orchestrator.py` neu schreiben | ⏳ | minimaler FSM mit Agent-Auswahl |
| `state_store.py` vereinfachen/neu denken | ⏳ | MVP-fähig, testbar |
| Session-State mit Pydantic sichern | ⏳ | Testbarkeit + Logging |
| Begrüßung je Agent nur einmal ausgeben | ⏳ | Flag im State nötig (`is_first_message`) |

## 🧪 Phase 4 – Tests

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `test_base_agent.py` schreiben | ⏳ | Fokus auf RAG + GPT-Fallback |
| `test_coach_agent.py` schreiben | ⏳ | nach Migration |
| `test_retrieval.py` schreiben | ⏳ | Dummy-Weaviate-Response |
| Integrationstest FSM → Agent | ⏳ | nach FSM-Basislogik |

## 🌐 Optional / später

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| GPT-Modell konfigurierbar machen | ⏳ | aktuell `"gpt-4"` fest |
| Fallback bei Weaviate-Verbindungsfehlern | ⏳ | aktuell kein Try/Except |
| `retrieval.py`: Score-basierte Gewichtung einbauen | ⏳ | z. B. `metadata.distance` als Info |
| `BaseAgent`: tool_use vorbereiten | ⏳ | falls GPT-Funktionen später ergänzt werden |
| `retrieval.py`: Prompt-Typen differenzieren (z. B. Diagnose vs. Training) | ⏳ | später für Modularität |
