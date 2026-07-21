from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDICAL_DATABASE_PATH", str(tmp_path / "test.db"))
    import backend.config
    import backend.database
    import backend.main

    importlib.reload(backend.config)
    importlib.reload(backend.database)
    importlib.reload(backend.main)
    with TestClient(backend.main.app) as test_client:
        yield test_client


def test_health_and_symptoms(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["condition_count"] == 41
    symptoms = client.get("/api/symptoms").json()["symptoms"]
    assert "Headache" in symptoms
    assert len(symptoms) > 100


def test_assessment_persists(client: TestClient) -> None:
    response = client.post(
        "/api/assessments",
        json={
            "symptoms": ["Headache", "Nausea", "Vomiting"],
            "severity": {"Headache": 6, "Nausea": 5, "Vomiting": 5},
            "duration": "2–3 days",
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["id"] > 0
    assert result["probable_condition"]
    assert result["urgency"] in {"Emergency", "Urgent", "Soon", "Routine"}
    assert client.get("/api/assessments").json()[0]["id"] == result["id"]


def test_red_flag_sets_emergency(client: TestClient) -> None:
    response = client.post(
        "/api/assessments",
        json={
            "symptoms": ["Chest Pain", "Breathlessness"],
            "severity": {"Chest Pain": 8, "Breathlessness": 8},
            "duration": "Less than 6 hours",
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["urgency"] == "Emergency"
    assert result["red_flags"]


def test_profile_and_medications(client: TestClient) -> None:
    profile = client.put(
        "/api/profile",
        json={"full_name": "Test User", "age": 31, "sex": "Prefer not to say", "blood_group": "O+", "conditions": "", "allergies": "", "emergency_contact": ""},
    )
    assert profile.status_code == 200
    assert client.get("/api/profile").json()["full_name"] == "Test User"

    med = client.post(
        "/api/medications",
        json={"name": "Example", "dosage": "As prescribed", "schedule": "Daily", "notes": "", "active": True},
    )
    assert med.status_code == 201
    med_id = med.json()["id"]
    assert client.delete(f"/api/medications/{med_id}").status_code == 204


def test_generated_medication_instruction_filter() -> None:
    from backend.ai_service import response_is_safe

    assert response_is_safe("This is not a diagnosis. Please discuss the result with a clinician.")
    assert not response_is_safe("Take 500 mg twice daily.")
    assert not response_is_safe("Increase your medication dose today.")
