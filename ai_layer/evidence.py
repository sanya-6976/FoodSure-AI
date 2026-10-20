"""Evidence collection and validation for FoodSure AI."""

from __future__ import annotations

import json
import math
from typing import Any


class EvidenceValidationError(ValueError):
    """Raised when evidence contains invalid or unsupported values."""


SUPPORTED_MODALITIES = {"color", "ftir", "image"}


def _validate_finite_number(value: Any, field_name: str) -> None:
    """Validate a finite numeric value without accepting booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceValidationError(
            f"'{field_name}' must be a numeric value."
        )

    if not math.isfinite(value):
        raise EvidenceValidationError(
            f"'{field_name}' must be finite."
        )


def validate_modalities(modalities: list[str]) -> list[str]:
    """Validate and normalize the modalities actually used by a model."""

    if not isinstance(modalities, list):
        raise EvidenceValidationError("'modalities' must be a list.")

    if not all(isinstance(item, str) for item in modalities):
        raise EvidenceValidationError(
            "Every modality must be represented by a string."
        )

    normalized = [item.strip().lower() for item in modalities]

    if len(normalized) != len(set(normalized)):
        raise EvidenceValidationError("Duplicate modalities are not allowed.")

    unsupported = set(normalized) - SUPPORTED_MODALITIES
    if unsupported:
        raise EvidenceValidationError(
            f"Unsupported modalities: {', '.join(sorted(unsupported))}."
        )

    return normalized


def validate_feature_contribution(item: dict[str, Any]) -> dict[str, Any]:
    """Validate a feature contribution supplied by an explainer."""

    if not isinstance(item, dict):
        raise EvidenceValidationError(
            "Each feature contribution must be a dictionary."
        )

    required = {"feature_name", "value", "method"}
    missing = required - item.keys()

    if missing:
        raise EvidenceValidationError(
            f"Feature contribution is missing: {', '.join(sorted(missing))}."
        )

    if not isinstance(item["feature_name"], str) or not item["feature_name"].strip():
        raise EvidenceValidationError("'feature_name' must be a non-empty string.")

    if not isinstance(item["method"], str) or not item["method"].strip():
        raise EvidenceValidationError("'method' must be a non-empty string.")

    _validate_finite_number(item["value"], "value")

    result = {
        "feature_name": item["feature_name"].strip(),
        "value": item["value"],
        "method": item["method"].strip(),
    }

    if "modality" in item:
        modality = item["modality"]

        if not isinstance(modality, str):
            raise EvidenceValidationError("'modality' must be a string.")

        modality = modality.strip().lower()

        if modality not in SUPPORTED_MODALITIES:
            raise EvidenceValidationError(
                f"Unsupported modality: {modality}."
            )

        result["modality"] = modality

    if "interpretation" in item:
        if not isinstance(item["interpretation"], str):
            raise EvidenceValidationError(
                "'interpretation' must be a string."
            )

        result["interpretation"] = item["interpretation"].strip()

    return result


def build_evidence_payload(
    *,
    model_version: str,
    modalities_used: list[str],
    model_result: dict[str, Any],
    feature_contributions: list[dict[str, Any]] | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
    uncertainty_flags: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Build a validated evidence payload for the AI Analyst.

    All predictions and explanations must come from upstream components.
    This function does not run an ML model or an explainer.
    """

    if not isinstance(model_version, str) or not model_version.strip():
        raise EvidenceValidationError(
            "'model_version' must be a non-empty string."
        )

    if not isinstance(model_result, dict):
        raise EvidenceValidationError("'model_result' must be a dictionary.")
    try:
        json.dumps(model_result, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(
            "'model_result' must contain only finite JSON-compatible values."
        ) from exc

    modalities = validate_modalities(modalities_used)

    contributions = []
    for item in feature_contributions or []:
        contribution = validate_feature_contribution(item)

        if (
            "modality" in contribution
            and contribution["modality"] not in modalities
        ):
            raise EvidenceValidationError(
                "A feature contribution references a modality "
                "that the model did not use."
            )

        contributions.append(contribution)

    for field_name, values in (
        ("evidence_items", evidence_items),
        ("uncertainty_flags", uncertainty_flags),
        ("limitations", limitations),
    ):
        if values is not None and not isinstance(values, list):
            raise EvidenceValidationError(f"'{field_name}' must be a list.")

    flags = list(uncertainty_flags or [])
    known_limitations = list(limitations or [])

    if not modalities:
        flags.append("No modality was specified in the evidence payload.")

    if not contributions and not evidence_items:
        flags.append("No supporting explainability evidence was supplied.")

    if not isinstance(model_result, dict):
        raise EvidenceValidationError("'model_result' must be a dictionary.")

    for flag in flags:
        if not isinstance(flag, str):
            raise EvidenceValidationError("Uncertainty flags must be strings.")

    for limitation in known_limitations:
        if not isinstance(limitation, str):
            raise EvidenceValidationError("Limitations must be strings.")

    validated_items = []

    for item in evidence_items or []:
        if not isinstance(item, dict):
            raise EvidenceValidationError(
                "Each evidence item must be a dictionary."
            )

        if not isinstance(item.get("description"), str):
            raise EvidenceValidationError(
                "Each evidence item needs a string 'description'."
            )
        description = item["description"].strip()
        if not description:
            raise EvidenceValidationError(
                "Each evidence item needs a non-empty 'description'."
            )
        source = item.get("source", "unspecified")
        if not isinstance(source, str) or not source.strip():
            raise EvidenceValidationError(
                "Each evidence item 'source' must be a non-empty string."
            )

        validated_items.append({
            "description": description,
            "source": source.strip(),
        })

    return {
        "model_version": model_version.strip(),
        "modalities_used": modalities,
        "model_result": model_result.copy(),
        "evidence": validated_items + contributions,
        "uncertainty_flags": flags,
        "limitations": known_limitations,
    }