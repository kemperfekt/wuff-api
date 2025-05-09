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
| Feld `text` in `search_relevant_chunks` dynamisch machen | 🔜 | aktuell nur `"text"` → später evtl. `"beschreibung"`, `"antwort"` o. Ä. |
| Logging in GPT-/Weaviate-Service integrieren | ⏳ | optional für Debugging |
| Tests für `BaseAgent` schreiben | ⏳ | Fokus auf GPT + RAG Verhalten |

## 🔄 Phase 2 – Agentenlogik migrieren

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `CoachAgent` neu aufbauen (ohne Scoring) | ✅ | MVP-gerecht, nur Rückfragenlogik |
| `DogAgent` migrieren | ✅ | mit RAG-Reaktion |
| Begrüßung über `BaseAgent.greeting_text` steuern | ✅ | `flow_intro` nutzt diese Info |
| `SessionState` mit Pydantic modelliert | ✅ | `agent_status`, `symptoms`, `active_symptom` |
| Agenten-Ein/Ausgabe Pydantic-Standardisierung | 🔜 | aktuell MVP-konform, später erweiterbar |
| RAG-Class `"Symptom"` konfigurierbar machen | 🔜 | aktuell hardcodiert |
| Unnötige Altlogik nicht übernehmen | 🔄 | selektiv übertragen, z. B. kein scoring |

## 🔁 Phase 3 – Flow / Orchestrierung

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `flow_orchestrator.py` MVP-fähig aufbauen | ✅ | Übergibt an Hund + Coach |
| `main.py` → FastAPI-Router `flow_endpoints.py` | ✅ | modularisiert |
| Begrüßung je Agent nur einmal | ✅ | `is_first_message` in State |
| Antwortformat frontendkompatibel gemacht | ✅ | `sender`/`text` statt `role`/`content` |
| Freier Gesprächsfluss mit Hund ermöglichen | 🔜 | z. B. über neue Endpunkte oder FSM |
| `CoachAgent` im Hintergrund beobachten lassen | 🔜 | Diagnose später ableitbar |
| FSM für freie Unterhaltung vorbereiten | 🔜 | aktuell nur simpler Handshake |

## 🧪 Phase 4 – Tests

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| `test_base_agent.py` schreiben | ⏳ | Fokus auf RAG + GPT-Fallback |
| `test_coach_agent.py` schreiben | ⏳ | nach vollständiger FSM |
| `test_retrieval.py` schreiben | ⏳ | Dummy-Weaviate-Response |
| Integrationstest FSM → Agent | ⏳ | nach FSM-Basislogik |

## 🌐 Optional / später

| Aufgabe | Status | Kommentar |
|--------|--------|----------|
| GPT-Modell konfigurierbar machen | ⏳ | aktuell `"gpt-4"` fest |
| Fallback bei Weaviate-Verbindungsfehlern | ⏳ | aktuell kein Try/Except |
| `retrieval.py`: Score-basierte Gewichtung | ⏳ | z. B. `metadata.distance` als Gewichtung |
| `BaseAgent`: tool_use vorbereiten | ⏳ | falls GPT-Funktionen nötig |
| `retrieval.py`: Prompt-Typen differenzieren | ⏳ | später für Diagnose vs. Training |
