"""Uncertainty and verification warnings for FoodSure AI.

This module flags known limitations. It does not calculate statistical
uncertainty unless a validated upstream method supplies that information.
"""

from __future__ import annotations

import math
from typing import Any


class UncertaintyInputError(ValueError):
    """Raised when uncertainty input is malformed."""


def _validate_probability(value: Any, field: str) -> float:
    """Validate a probability in the range [0, 1]."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UncertaintyInputError(f"'{field}' must be numeric.")

    if not math.isfinite(value) or not 0 <= value <= 1:
        raise UncertaintyInputError(
            f"'{field}' must be finite and between 0 and 1."
        )

    return float(value)


def assess_uncertainty(
    *,
    model_result: dict[str, Any],
    modalities_used: list[str],
    evidence: list[Any] | None = None,
    confidence: float | None = None,
    confidence_calibrated: bool = False,
    out_of_distribution: bool | None = None,
    external_validation_available: bool | None = None,
    model_scope_supported: bool | None = None,
    existing_flags: list[str] | None = None,
) -> dict[str, Any]:
    """Return transparent caution flags based on supplied information.

    This function does not infer uncertainty from a prediction alone.
    Statistical uncertainty and OOD status must come from validated
    upstream methods.
    """

    if not isinstance(model_result, dict):
        raise UncertaintyInputError("'model_result' must be a dictionary.")

    if not isinstance(modalities_used, list) or not all(
        isinstance(item, str) for item in modalities_used
    ):
        raise UncertaintyInputError(
            "'modalities_used' must be a list of strings."
        )

    if evidence is not None and not isinstance(evidence, list):
        raise UncertaintyInputError("'evidence' must be a list.")

    if existing_flags is not None and (
        not isinstance(existing_flags, list)
        or not all(isinstance(flag, str) for flag in existing_flags)
    ):
        raise UncertaintyInputError("'existing_flags' must be a list of strings.")

    if not isinstance(confidence_calibrated, bool):
        raise UncertaintyInputError("'confidence_calibrated' must be boolean.")

    if external_validation_available is not None and not isinstance(
        external_validation_available, bool
    ):
        raise UncertaintyInputError(
            "'external_validation_available' must be true, false, or None."
        )

    if model_scope_supported is not None and not isinstance(
        model_scope_supported, bool
    ):
        raise UncertaintyInputError(
            "'model_scope_supported' must be true, false, or None."
        )

    if out_of_distribution is not None and not isinstance(
        out_of_distribution, bool
    ):
        raise UncertaintyInputError(
            "'out_of_distribution' must be true, false, or None."
        )

    if confidence is not None:
        confidence = _validate_probability(confidence, "confidence")

    flags = list(existing_flags or [])
    recommendations: list[str] = []

    if model_result.get("prediction") is None:
        flags.append("No model prediction was supplied.")

    if not modalities_used:
        flags.append("No input modalities were identified.")

    if not evidence:
        flags.append("No supporting evidence was supplied.")

    if confidence is None:
        flags.append("No model confidence value was supplied.")
    elif not confidence_calibrated:
        flags.append(
            "The supplied confidence value is not documented as calibrated."
        )

    if out_of_distribution is None:
        flags.append(
            "Out-of-distribution status was not assessed by a supplied detector."
        )
    elif out_of_distribution:
        flags.append(
            "The supplied detector flagged this sample as out-of-distribution."
        )
        recommendations.append(
            "Do not rely on this prediction without additional investigation."
        )

    if not model_scope_supported:
        if model_scope_supported is False:
            flags.append(
                "The sample or input conditions are outside the documented model scope."
            )
            recommendations.append(
                "Use an appropriate validated method for this sample."
            )
        else:
            flags.append(
                "Compatibility with the documented model scope was not assessed."
            )

    if external_validation_available is False:
        flags.append(
            "Independent external validation has not been established."
        )
    elif external_validation_available is None:
        flags.append(
            "Independent external validation availability was not supplied."
        )

    recommendations.append(
        "For consequential decisions, verify results with an appropriate "
        "validated laboratory method."
    )

    # Remove duplicate flags while preserving their original order.
    flags = list(dict.fromkeys(flags))

    if not flags:
        status = "no_known_flags"
    elif (
        out_of_distribution is True
        or model_scope_supported is False
        or model_result.get("prediction") is None
    ):
        status = "high_caution"
    else:
        status = "caution"

    return {
        "status": status,
        "flags": flags,
        "recommendations": list(dict.fromkeys(recommendations)),
        "confidence": confidence,
        "confidence_calibrated": confidence_calibrated,
        "out_of_distribution": out_of_distribution,
        "external_validation_available": external_validation_available,
    }