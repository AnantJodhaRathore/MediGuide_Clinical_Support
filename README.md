# MediGuide Clinical Support

A safety-first upgrade of the original symptom-based medical expert system.

## Architecture

- **Frontend:** Streamlit medical dashboard with responsive clinical theme
- **Backend:** FastAPI REST API with validation, model service, triage rules, and optional Ollama chat
- **Database:** SQLite with WAL mode for profiles, medications, assessment history, and chat messages
- **ML:** Random Forest trained from `dataset/Training.csv`, with held-out validation against `dataset/Testing.csv`

## Safety design

The result is an educational pattern match, **not a diagnosis**. Emergency warning signs override the model prediction. The app does not prescribe medication or advise changing existing treatment.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_all.py
```

Open:

- Frontend: `http://127.0.0.1:8501`
- API docs: `http://127.0.0.1:8000/docs`

Alternatively, use two terminals:

```bash
uvicorn backend.main:app --reload
streamlit run app.py
```

## Optional local AI

The chat works without Ollama using a safe fallback. To enable local generation:

```bash
ollama serve
ollama pull mistral
```

Environment variables:

- `MEDICAL_API_URL` — frontend API URL
- `MEDICAL_DATABASE_PATH` — custom SQLite file location
- `OLLAMA_API_URL` — Ollama generate endpoint
- `OLLAMA_MODEL` — local model name

## Tests

```bash
pytest -q
```

## Data

Application records are stored locally in `data/medical_expert.db`. Delete that file to reset all saved records.

## Import records from the original app

The original `analysis_history.json` is preserved as `legacy_analysis_history.json`. To import its symptom records into SQLite using the upgraded safety rules:

```bash
python scripts/import_legacy_history.py
```

Old generated medication suggestions and chat replies are intentionally not imported because they may contain unsafe or outdated treatment advice.
