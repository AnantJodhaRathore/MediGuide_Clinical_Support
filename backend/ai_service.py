from __future__ import annotations

import json
import re
from typing import Any

import requests

from backend.config import OLLAMA_API_URL, OLLAMA_MODEL

UNSAFE_MEDICATION_PATTERNS = (
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b",
    r"\b(?:start|stop|increase|decrease|double)\b.{0,50}\b(?:medicine|medication|dose|dosage|tablet|capsule)\b",
    r"\btake\s+\d+\b",
)


def response_is_safe(text: str) -> bool:
    lowered = text.lower()
    return not any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in UNSAFE_MEDICATION_PATTERNS)


def safe_fallback(question: str, assessment: dict[str, Any]) -> str:
    urgency = assessment.get("urgency", "Routine")
    condition = assessment.get("probable_condition", "the predicted pattern")
    if urgency == "Emergency":
        return (
            "Your recorded symptoms include emergency warning signs. Please contact local emergency services now. "
            "This chat cannot safely assess or treat an emergency."
        )
    return (
        f"The assessment pattern was most similar to {condition}, but it is not a diagnosis. "
        "A clinician can review your history, examine you, and decide whether tests are needed. "
        "Seek urgent help if you develop chest pain, severe breathing difficulty, fainting, confusion, one-sided weakness, heavy bleeding, or rapidly worsening symptoms."
    )


def answer_question(question: str, assessment: dict[str, Any]) -> tuple[str, str]:
    prompt = f"""
You are a cautious health education assistant. Never diagnose, prescribe, or recommend changing medication.
Assessment context: {json.dumps(assessment, ensure_ascii=False)}
User question: {question}
Give a concise response with: what the result means, safe next step, and emergency warning signs.
Explicitly state that the result is not a diagnosis.
""".strip()
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=12)
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        if text and response_is_safe(text):
            if "not a diagnosis" not in text.lower():
                text = "This result is not a diagnosis. " + text
            return text, "ollama"
    except (requests.RequestException, ValueError):
        pass
    return safe_fallback(question, assessment), "fallback"
