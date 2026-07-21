from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AssessmentRequest(BaseModel):
    symptoms: list[str] = Field(min_length=2, max_length=25)
    severity: dict[str, int]
    duration: str = Field(min_length=1, max_length=80)

    @field_validator("symptoms")
    @classmethod
    def unique_symptoms(cls, value: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        if len(cleaned) < 2:
            raise ValueError("Select at least two unique symptoms.")
        return cleaned

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, value: dict[str, int]) -> dict[str, int]:
        if any(score < 1 or score > 10 for score in value.values()):
            raise ValueError("Severity must be between 1 and 10.")
        return value


class ProfileUpdate(BaseModel):
    full_name: str = Field(default="", max_length=120)
    age: int | None = Field(default=None, ge=0, le=120)
    sex: str = Field(default="Prefer not to say", max_length=40)
    blood_group: str = Field(default="Unknown", max_length=12)
    conditions: str = Field(default="", max_length=1000)
    allergies: str = Field(default="", max_length=1000)
    emergency_contact: str = Field(default="", max_length=160)


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dosage: str = Field(min_length=1, max_length=120)
    schedule: str = Field(min_length=1, max_length=160)
    notes: str = Field(default="", max_length=500)
    active: bool = True


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
