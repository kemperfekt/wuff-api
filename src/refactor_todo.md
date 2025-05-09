# 📋 DogBot Refactoring – Offene Aufgaben (ToDo-Liste)

## ✅ Phase 1 – Clean Core (Agenten, GPT, RAG)

| Aufgabe                                                    | Status | Kommentar                                                                 |
|------------------------------------------------------------|--------|--------------------------------------------------------------------------|
| Neue Projektstruktur `src/` angelegt                       | ✅     | erledigt                                                                 |
| `BaseAgent` erstellt                                       | ✅     | mit RAG + GPT-Option                                                     |
| `AgentMessage` erstellt                                    | ✅     | `flow_models.py`                                                         |
| `gpt_service.py` erstellt                                  | ✅     | GPT-Call abstrahiert                                                     |
| `retrieval.py` erstellt                                    | ✅     | RAG-Wrapper mit Fallback                                                 |
| `weaviate_service.py` erstellt                             | ✅     | Verbindung + Suche aktiv                                                 |
| `search_relevant_chunks`: Feld 'text' dynamisch machen     | 🔜     | aktuell nur `"text"` → später evtl. `"beschreibung"`, `"antwort"`       |
| Logging in GPT-/Weaviate-Service integrieren               | ⏳     | optional für Debugging                                                   |
| Tests für `BaseAgent` schreiben                            | ⏳     | folgt nach `CoachAgent`                                                  |

## ✅ Phase 2 – Agentenlogik migrieren

| Aufgabe                                                    | Status | Kommentar                                                                 |
|------------------------------------------------------------|--------|--------------------------------------------------------------------------|
| `CoachAgent` neu aufbauen (ohne Scoring)                   | ✅     | MVP-gerecht, nutzt Rückfragenlogik mit Weaviate                          |
| `DogAgent` migrieren                                       | ✅     | greeting_text + GPT-Reaktion implementiert                               |
| Agenten-Ein/Ausgabe mit Pydantic vereinheitlichen          | ⏳     | später hilfreich für Validierung, aktuell nicht notwendig                |
| Unnötige Altlogik in Coach/Dog nicht übernehmen            | 🔄     | wird selektiv entschieden                                                |
| RAG-Class „Symptom“ konfigurierbar machen                  | ⏳     | aktuell hardcodiert                                                      |

## 🔁 Phase 3 – Flow / Orchestrierung

| Aufgabe                                                    | Status | Kommentar                                                                 |
|------------------------------------------------------------|--------|--------------------------------------------------------------------------|
| `flow_orchestrator.py` neu schreiben                       | ✅     | FSM mit Agent-Auswahl implementiert                                      |
| `session_state.py` neu gedacht und angepasst               | ✅     | neue Struktur mit `SessionStore`, `SymptomState`, `AgentStatus`         |
| Begrüßung je Agent nur einmal ausgeben                     | ✅     | wird über `is_first_message` im State geregelt                           |
| Session-State mit Pydantic sichern                         | ✅     | bereits umgesetzt                                                        |

## 🧪 Phase 4 – Tests

| Aufgabe                                                    | Status | Kommentar                                                                 |
|------------------------------------------------------------|--------|--------------------------------------------------------------------------|
| `test_base_agent.py` schreiben                             | ⏳     | Fokus auf RAG + GPT-Fallback                                             |
| `test_coach_agent.py` schreiben                            | ⏳     | nach Migration                                                           |
| `test_retrieval.py` schreiben                              | ⏳     | Dummy-Weaviate-Response                                                  |
| Integrationstest FSM → Agent                               | ⏳     | nach FSM-Basislogik                                                      |

## 🌐 Optional / später

| Aufgabe                                                    | Status | Kommentar                                                                 |
|------------------------------------------------------------|--------|--------------------------------------------------------------------------|
| GPT-Modell konfigurierbar machen                           | ⏳     | aktuell `"gpt-4"` fest                                                   |
| Fallback bei Weaviate-Verbindungsfehlern                   | ⏳     | aktuell kein Try/Except                                                  |
| `retrieval.py`: Score-basierte Gewichtung einbauen         | ⏳     | z. B. `metadata.distance` als Info                                       |
| `BaseAgent`: tool_use vorbereiten                          | ⏳     | falls GPT-Funktionen später ergänzt werden                              |
| `retrieval.py`: Prompt-Typen differenzieren (Diagnose etc) | ⏳     | später für Modularität                                                   |
