# Architecture

```text
Browser
  │
  ▼
Streamlit frontend (`app.py`, port 8501)
  │ HTTP/JSON
  ▼
FastAPI backend (`backend/main.py`, port 8000)
  ├── model_service.py  → trains and serves the Random Forest model
  ├── clinical.py       → deterministic red-flag triage and safe guidance
  ├── ai_service.py     → optional Ollama chat with a safe offline fallback
  └── database.py       → parameterized SQLite access in WAL mode
                              │
                              ▼
                         data/medical_expert.db
```

## Database tables

- `profiles`: one local health profile
- `medications`: user-entered medication organizer
- `assessments`: symptoms, severity, model output, triage, and guidance
- `chat_messages`: assessment-specific follow-up conversation

## Request flow

1. The frontend fetches the canonical symptom list from the API.
2. The backend validates symptom names, count, severity, and duration.
3. The model returns a ranked probability distribution.
4. Deterministic emergency rules evaluate red flags independently of the model.
5. Safe guidance is generated and the assessment is persisted to SQLite.
6. The frontend renders urgency before the probable condition.
