"""Structured report generation for FoodSure AI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class ReportValidationError(ValueError):
    """Raised when report input is malformed."""


def _validate_object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ReportValidationError(f"'{name}' must be a dictionary.")
    return value


def _validate_text_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ReportValidationError(f"'{name}' must be a list.")

    if not all(isinstance(item, str) for item in value):
        raise ReportValidationError(
            f"Every item in '{name}' must be a string."
        )

    return value.copy()


def generate_report(
    *,
    evidence_payload: dict[str, Any],
    analyst_result: dict[str, Any],
    uncertainty_result: dict[str, Any],
) -> dict[str, Any]:
    """Create a report from supplied, validated pipeline outputs."""

    _validate_object(evidence_payload, "evidence_payload")
    _validate_object(analyst_result, "analyst_result")
    _validate_object(uncertainty_result, "uncertainty_result")

    model_result = _validate_object(
        evidence_payload.get("model_result"),
        "evidence_payload.model_result",
    )

    if not isinstance(evidence_payload.get("model_version"), str):
        raise ReportValidationError("'model_version' must be a string.")
    if not evidence_payload["model_version"].strip():
        raise ReportValidationError("'model_version' must be non-empty.")

    modalities = evidence_payload.get("modalities_used")
    if not isinstance(modalities, list) or not all(
        isinstance(item, str) for item in modalities
    ):
        raise ReportValidationError("'modalities_used' must be a list of strings.")
    if len(modalities) != len(set(modalities)):
        raise ReportValidationError("'modalities_used' must not contain duplicates.")

    required_analyst_fields = (
        "summary",
        "interpretation",
        "recommended_verification",
    )
    for field in required_analyst_fields:
        if (
            not isinstance(analyst_result.get(field), str)
            or not analyst_result[field].strip()
        ):
            raise ReportValidationError(
                f"Analyst result requires a non-empty string field '{field}'."
            )

    supporting_evidence = _validate_text_list(
        analyst_result.get("supporting_evidence", []),
        "analyst_result.supporting_evidence",
    )
    analysis_mode = analyst_result.get("analysis_mode", "unspecified")
    if not isinstance(analysis_mode, str) or not analysis_mode.strip():
        raise ReportValidationError("'analysis_mode' must be a non-empty string.")
    status = uncertainty_result.get("status", "unspecified")
    if not isinstance(status, str) or not status.strip():
        raise ReportValidationError("'uncertainty_result.status' must be a non-empty string.")
    uncertainty_flags = _validate_text_list(
        uncertainty_result.get("flags", []),
        "uncertainty_result.flags",
    )
    recommendations = _validate_text_list(
        uncertainty_result.get("recommendations", []),
        "uncertainty_result.recommendations",
    )

    # Ensure the assembled report can be serialized without NaN/Infinity.
    report = {
        "report_schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": evidence_payload["model_version"],
        "modalities_used": modalities.copy(),
        "model_result": model_result.copy(),
        "analysis": {
            "summary": analyst_result["summary"],
            "interpretation": analyst_result["interpretation"],
            "supporting_evidence": supporting_evidence,
            "analysis_mode": analysis_mode,
        },
        "uncertainty": {
            "status": status,
            "flags": uncertainty_flags,
            "recommendations": recommendations,
        },
        "limitations": _validate_text_list(
            analyst_result.get("limitations", []),
            "analyst_result.limitations",
        ),
        "recommended_verification": analyst_result[
            "recommended_verification"
        ],
        "disclaimer": (
            "FoodSure AI is a research prototype for AI-assisted screening. "
            "Its outputs are model estimates, not laboratory-confirmed findings "
            "or evidence of regulatory certification. Use an appropriate "
            "validated laboratory method for consequential decisions."
        ),
    }

    try:
        json.dumps(report, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ReportValidationError(
            "Report contains non-JSON-compatible values."
        ) from exc

    return report


def report_to_json(report: dict[str, Any], *, indent: int = 2) -> str:
    """Serialize a report to JSON."""

    _validate_object(report, "report")

    if not isinstance(indent, int) or isinstance(indent, bool) or indent < 0:
        raise ReportValidationError("'indent' must be a non-negative integer.")

    try:
        return json.dumps(
            report,
            indent=indent,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ReportValidationError(
            "Report cannot be serialized as valid JSON."
        ) from exc