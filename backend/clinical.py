from __future__ import annotations

from typing import Any

EMERGENCY_RULES: dict[str, str] = {
    "Chest Pain": "Chest pain can be a sign of a heart or lung emergency.",
    "Breathlessness": "Difficulty breathing requires urgent assessment.",
    "Weakness Of One Body Side": "One-sided weakness can be a stroke warning sign.",
    "Slurred Speech": "Slurred speech can be a stroke warning sign.",
    "Altered Sensorium": "Confusion or reduced awareness can be medically urgent.",
    "Coma": "Loss of consciousness is a medical emergency.",
    "Blood In Sputum": "Coughing blood needs urgent medical review.",
    "Stomach Bleeding": "Possible internal bleeding needs emergency care.",
    "Fast Heart Rate": "A very fast heart rate with symptoms can be urgent.",
}

HIGH_RISK_CONDITIONS = {
    "Heart attack",
    "Paralysis (brain hemorrhage)",
    "Pneumonia",
    "Tuberculosis",
    "Dengue",
    "Malaria",
}


def triage(symptoms: list[str], severity: dict[str, int], condition: str) -> tuple[str, list[str]]:
    reasons = [message for symptom, message in EMERGENCY_RULES.items() if symptom in symptoms]
    severe = [name for name, score in severity.items() if score >= 9]
    if severe:
        reasons.append(f"Very high severity was reported for: {', '.join(severe)}.")
    if reasons:
        return "Emergency", reasons
    if condition in HIGH_RISK_CONDITIONS or any(score >= 7 for score in severity.values()):
        return "Urgent", []
    if any(score >= 5 for score in severity.values()):
        return "Soon", []
    return "Routine", []


def guidance_for(urgency: str, condition: str, duration: str) -> dict[str, Any]:
    next_steps = {
        "Emergency": "Contact local emergency services now or go to the nearest emergency department. Do not drive yourself if you feel faint, confused, severely short of breath, or have chest pain.",
        "Urgent": "Arrange an in-person medical assessment today. Seek emergency help sooner if symptoms worsen or new red flags appear.",
        "Soon": "Book a clinician appointment within 24–72 hours, especially if symptoms persist, worsen, or interfere with normal activity.",
        "Routine": "Monitor your symptoms and arrange routine primary-care advice if they persist or concern you.",
    }[urgency]
    return {
        "next_steps": next_steps,
        "self_care": [
            "Rest, drink fluids if you are able, and keep a note of symptom changes.",
            f"Your reported duration is {duration.lower()}; seek care sooner if the pattern changes.",
            "Avoid strenuous activity while you feel unwell.",
        ],
        "medication_safety": (
            "This tool does not prescribe medicines. Do not start, stop, or change prescription medication based on this result. "
            "A pharmacist or clinician can check what is safe for you, including allergies and interactions."
        ),
        "interpretation": (
            f"The model pattern is most similar to {condition}, but this is not a diagnosis. "
            "Many conditions share symptoms and an examination or testing may be needed."
        ),
    }


FIRST_AID_GUIDES = {
    "Chest pain / suspected heart attack": [
        "Call local emergency services immediately.",
        "Help the person rest in a comfortable position and loosen tight clothing.",
        "Do not give food, drink, or medication unless instructed by a qualified professional.",
        "If they become unresponsive and are not breathing normally, begin CPR if trained.",
    ],
    "Stroke warning signs": [
        "Use FAST: Face drooping, Arm weakness, Speech difficulty, Time to call emergency services.",
        "Note the exact time symptoms began or the last time the person was known well.",
        "Do not give food, drink, or medication.",
    ],
    "Burns": [
        "Move away from the heat source and remove jewellery or loose clothing near the burn.",
        "Cool under clean, cool running water for 20 minutes.",
        "Do not use ice, butter, toothpaste, or creams.",
        "Cover loosely with a clean non-stick dressing and seek care for large, deep, electrical, chemical, facial, or airway burns.",
    ],
    "Choking": [
        "Encourage coughing if the person can cough or speak.",
        "If they cannot breathe or speak, call emergency services and provide age-appropriate back blows and abdominal/chest thrusts if trained.",
        "Begin CPR if they become unresponsive and are not breathing normally.",
    ],
    "Severe allergic reaction": [
        "Call emergency services immediately.",
        "Use the person's prescribed adrenaline auto-injector if available and you know how.",
        "Lay them flat with legs raised unless breathing is difficult; then allow them to sit up.",
        "A second prescribed injector may be needed according to its instructions while help is coming.",
    ],
    "Cuts and bleeding": [
        "Apply firm, continuous pressure with clean cloth or gauze.",
        "Add more layers if blood soaks through; do not remove the original layer.",
        "Seek urgent help for spurting blood, deep wounds, embedded objects, numbness, or bleeding that does not stop.",
    ],
}
