from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ai_service import answer_question
from backend.clinical import FIRST_AID_GUIDES, guidance_for, triage
from backend.config import APP_NAME, APP_VERSION
from backend.database import Database
from backend.model_service import get_model
from backend.schemas import AssessmentRequest, ChatRequest, MedicationCreate, ProfileUpdate

app = FastAPI(
    title=f"{APP_NAME} API",
    version=APP_VERSION,
    description="Prediction, triage, profile, medication, history, and educational guidance API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()


@app.get("/")
def root() -> dict[str, str]:
    return {"name": APP_NAME, "version": APP_VERSION, "docs": "/docs"}


@app.get("/api/health")
def health() -> dict:
    model = get_model()
    return {
        "status": "ok",
        "version": APP_VERSION,
        "model": "RandomForestClassifier",
        "condition_count": len(model.encoder.classes_),
        "symptom_count": len(model.symptoms),
        "validation_accuracy": model.validation_accuracy,
    }


@app.get("/api/symptoms")
def symptoms() -> dict[str, list[str]]:
    return {"symptoms": get_model().symptoms}


@app.post("/api/assessments", status_code=201)
def create_assessment(payload: AssessmentRequest) -> dict:
    model = get_model()
    unknown = sorted(set(payload.symptoms) - set(model.symptoms))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown symptoms: {', '.join(unknown)}")
    prediction = model.predict(payload.symptoms)
    severity = {symptom: payload.severity.get(symptom, 5) for symptom in payload.symptoms}
    urgency, red_flags = triage(payload.symptoms, severity, prediction.probable_condition)
    result = {
        "symptoms": payload.symptoms,
        "severity": severity,
        "duration": payload.duration,
        "probable_condition": prediction.probable_condition,
        "confidence": prediction.confidence,
        "alternatives": prediction.alternatives,
        "urgency": urgency,
        "red_flags": red_flags,
        "guidance": guidance_for(urgency, prediction.probable_condition, payload.duration),
    }
    return db.create_assessment(result)


@app.get("/api/assessments")
def list_assessments(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return db.list_assessments(limit)


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: int) -> dict:
    result = db.get_assessment(assessment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return result


@app.delete("/api/assessments/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: int) -> None:
    if not db.delete_assessment(assessment_id):
        raise HTTPException(status_code=404, detail="Assessment not found")


@app.get("/api/profile")
def get_profile() -> dict:
    return db.get_profile()


@app.put("/api/profile")
def update_profile(payload: ProfileUpdate) -> dict:
    return db.save_profile(payload.model_dump())


@app.get("/api/medications")
def list_medications() -> list[dict]:
    return db.list_medications()


@app.post("/api/medications", status_code=201)
def add_medication(payload: MedicationCreate) -> dict:
    return db.add_medication(payload.model_dump())


@app.delete("/api/medications/{medication_id}", status_code=204)
def delete_medication(medication_id: int) -> None:
    if not db.delete_medication(medication_id):
        raise HTTPException(status_code=404, detail="Medication not found")


@app.get("/api/first-aid")
def first_aid() -> dict[str, list[str]]:
    return FIRST_AID_GUIDES


@app.get("/api/assessments/{assessment_id}/chat")
def list_chat(assessment_id: int) -> list[dict]:
    if not db.get_assessment(assessment_id):
        raise HTTPException(status_code=404, detail="Assessment not found")
    return db.list_chat_messages(assessment_id)


@app.post("/api/assessments/{assessment_id}/chat", status_code=201)
def chat(assessment_id: int, payload: ChatRequest) -> dict:
    assessment = db.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    db.add_chat_message(assessment_id, "user", payload.question)
    answer, source = answer_question(payload.question, assessment)
    message = db.add_chat_message(assessment_id, "assistant", answer)
    return {"message": message, "source": source}
