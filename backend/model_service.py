from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

from backend.config import DATASET_DIR


def display_name(raw: str) -> str:
    cleaned = re.sub(r"\s+", " ", raw.replace("_", " ")).strip()
    return cleaned.title()


@dataclass(frozen=True)
class Prediction:
    probable_condition: str
    confidence: float
    alternatives: list[dict[str, Any]]


class MedicalModel:
    def __init__(self) -> None:
        training = pd.read_csv(DATASET_DIR / "Training.csv").dropna(axis=1, how="all")
        testing = pd.read_csv(DATASET_DIR / "Testing.csv").dropna(axis=1, how="all")
        if "prognosis" not in training.columns:
            raise RuntimeError("Training dataset does not contain a prognosis column.")

        self.feature_names = [column for column in training.columns if column != "prognosis"]
        self.display_to_raw = {display_name(raw): raw for raw in self.feature_names}
        self.raw_to_display = {raw: display_name(raw) for raw in self.feature_names}
        self.encoder = LabelEncoder()
        y_train = self.encoder.fit_transform(training["prognosis"].astype(str).str.strip())
        x_train = training[self.feature_names].astype(int)
        self.model = RandomForestClassifier(
            n_estimators=280,
            max_features="sqrt",
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample",
        )
        self.model.fit(x_train, y_train)
        self.validation_accuracy = self._evaluate(testing)

    def _evaluate(self, testing: pd.DataFrame) -> float | None:
        if testing.empty or "prognosis" not in testing.columns:
            return None
        x_test = testing.reindex(columns=self.feature_names, fill_value=0).astype(int)
        known = testing["prognosis"].astype(str).str.strip().isin(self.encoder.classes_)
        if not known.any():
            return None
        y_true = self.encoder.transform(testing.loc[known, "prognosis"].astype(str).str.strip())
        y_pred = self.model.predict(x_test.loc[known])
        return float(accuracy_score(y_true, y_pred))

    @property
    def symptoms(self) -> list[str]:
        return sorted(self.display_to_raw)

    def predict(self, symptoms: list[str]) -> Prediction:
        vector = np.zeros(len(self.feature_names), dtype=int)
        for symptom in symptoms:
            raw = self.display_to_raw.get(symptom)
            if raw is not None:
                vector[self.feature_names.index(raw)] = 1
        frame = pd.DataFrame([vector], columns=self.feature_names)
        probabilities = self.model.predict_proba(frame)[0]
        ranked = np.argsort(probabilities)[::-1][:4]
        alternatives: list[dict[str, Any]] = []
        for index in ranked[1:]:
            alternatives.append(
                {
                    "condition": str(self.encoder.inverse_transform([index])[0]).strip(),
                    "confidence": round(float(probabilities[index]), 4),
                }
            )
        best = int(ranked[0])
        return Prediction(
            probable_condition=str(self.encoder.inverse_transform([best])[0]).strip(),
            confidence=round(float(probabilities[best]), 4),
            alternatives=alternatives,
        )


@lru_cache(maxsize=1)
def get_model() -> MedicalModel:
    return MedicalModel()
