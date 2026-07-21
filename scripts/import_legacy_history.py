from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.clinical import guidance_for, triage
from backend.database import Database
from backend.model_service import get_model

LEGACY_FILE = ROOT / "legacy_analysis_history.json"


def main() -> int:
    if not LEGACY_FILE.exists():
        print(f"No legacy file found at {LEGACY_FILE}")
        return 1

    records = json.loads(LEGACY_FILE.read_text(encoding="utf-8"))
    model = get_model()
    valid_symptoms = set(model.symptoms)
    db = Database()
    imported = 0
    skipped = 0

    for record in records:
        symptoms = [item for item in record.get("symptoms", []) if item in valid_symptoms]
        if len(symptoms) < 2:
            skipped += 1
            continue
        severity = {name: int(record.get("severity", {}).get(name, 5)) for name in symptoms}
        prediction = model.predict(symptoms)
        urgency, red_flags = triage(symptoms, severity, prediction.probable_condition)
        raw_timestamp = record.get("timestamp", "")
        try:
            created_at = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S").isoformat()
        except ValueError:
            created_at = datetime.now().isoformat(timespec="seconds")
        db.create_assessment(
            {
                "symptoms": symptoms,
                "severity": severity,
                "duration": "Imported legacy record",
                "probable_condition": prediction.probable_condition,
                "confidence": prediction.confidence,
                "alternatives": prediction.alternatives,
                "urgency": urgency,
                "red_flags": red_flags,
                "guidance": guidance_for(urgency, prediction.probable_condition, "Imported legacy record"),
                "created_at": created_at,
            }
        )
        imported += 1

    print(f"Imported {imported} legacy assessments; skipped {skipped} invalid records.")
    print("Legacy medication suggestions and chat messages were intentionally not imported for safety.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
