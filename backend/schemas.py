"""Typed schemas and contracts for FoodSure AI integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    email: str
    full_name: str
    created_at: str
    role: str = "researcher"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SampleValidationResult:
    is_valid: bool
    sample_id: str | None = None
    feature_count: int = 0
    actual_level: float | None = None
    error_message: str | None = None
    features: Any = None  # pd.DataFrame
    source_label: str = ""


@dataclass
class PredictionOutput:
    predicted_class: str
    predicted_percentage: float | None
    model_version: str
    modality: str
    is_pure: bool
    status_label: str  # "PURE TURMERIC" or "ADULTERATED"
    confidence_note: str


@dataclass
class AnalysisResult:
    analysis_id: str
    user_id: str
    timestamp: str
    sample_id: str
    input_source: str
    modality_used: str
    prediction: PredictionOutput
    actual_level: float | None
    explanation_summary: str
    supporting_evidence: list[str]
    uncertainty_warnings: list[str]
    recommended_verification: str
    analysis_mode: str  # "gemini_ai" or "deterministic_fallback"
    raw_pipeline_output: dict[str, Any] = field(default_factory=dict)
    # New: 8-section structured explanation dict
    structured_explanation: dict[str, Any] = field(default_factory=dict)
    # Explanation depth: "quick" | "detailed" | "technical"
    explanation_depth: str = "detailed"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["prediction"] = asdict(self.prediction)
        return result
