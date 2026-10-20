"""FoodSure AI Analyst.

Explains supplied model outputs and evidence.
Does not train models or generate adulteration predictions.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ai_layer.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class AnalystInputError(ValueError):
    """Raised when the analyst receives an invalid evidence payload."""


class AnalystError(RuntimeError):
    """Raised when analysis cannot produce a valid result."""


OUTPUT_FIELDS = (
    "summary",
    "model_result",
    "supporting_evidence",
    "interpretation",
    "uncertainty_notes",
    "limitations",
    "recommended_verification",
)


def validate_payload(payload: dict[str, Any]) -> None:
    """Validate the minimum evidence contract before analysis."""

    if not isinstance(payload, dict):
        raise AnalystInputError("Payload must be a dictionary.")

    if not isinstance(payload.get("model_result"), dict):
        raise AnalystInputError(
            "'model_result' must be a dictionary containing actual model output."
        )

    if not isinstance(payload.get("model_version"), str):
        raise AnalystInputError("'model_version' must be a string.")

    if not isinstance(payload.get("modalities_used"), list):
        raise AnalystInputError("'modalities_used' must be a list.")

    if not all(isinstance(item, str) for item in payload["modalities_used"]):
        raise AnalystInputError("Every modality name must be a string.")

    if "evidence" in payload and not isinstance(payload["evidence"], list):
        raise AnalystInputError("'evidence' must be a list.")

    if "uncertainty_flags" in payload and not isinstance(
        payload["uncertainty_flags"], list
    ):
        raise AnalystInputError("'uncertainty_flags' must be a list.")

    # Ensure the payload can be serialized safely as JSON.
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AnalystInputError(
            "Payload must contain JSON-compatible finite values."
        ) from exc


def _as_text(value: Any, default: str = "Not provided.") -> str:
    """Convert supported scalar values into readable text."""
    if value is None:
        return default
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def deterministic_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a conservative explanation without using an LLM."""

    validate_payload(payload)

    result = payload["model_result"]
    modalities = payload["modalities_used"]
    evidence = payload.get("evidence", [])
    uncertainty_flags = payload.get("uncertainty_flags", [])
    limitations = payload.get("limitations", [])

    prediction = result.get("prediction")
    target_type = result.get("target_type", "unspecified")

    if prediction is None:
        summary = (
            "The supplied payload does not contain a prediction. "
            "No conclusion about adulteration can be drawn."
        )
    else:
        summary = (
            f"The supplied model reports a {target_type} prediction of "
            f"{_as_text(prediction)}. This is a model output, not an "
            "independent laboratory finding."
        )

    evidence_text = [
        _as_text(item) for item in evidence
    ] or ["No supporting evidence was supplied."]

    uncertainty_text = [
        _as_text(item) for item in uncertainty_flags
    ] or ["No explicit uncertainty flags were supplied; this does not mean uncertainty is absent."]

    limitation_text = [
        _as_text(item) for item in limitations
    ]

    # Always communicate the research-prototype limitation.
    limitation_text.append(
        "FoodSure AI is a research prototype and is not a substitute "
        "for validated laboratory testing."
    )

    if not modalities:
        interpretation = (
            "No modalities were identified in the payload. "
            "The analytical basis of the model result cannot be assessed."
        )
    else:
        interpretation = (
            "The payload identifies these modalities as used: "
            + ", ".join(modalities)
            + ". Their presence alone does not establish that the prediction "
            "is correct or that the model generalizes to new samples."
        )

    return {
        "summary": summary,
        "model_result": {
            "prediction": prediction,
            "target_type": target_type,
            "model_version": payload["model_version"],
            "modalities_used": modalities,
        },
        "supporting_evidence": evidence_text,
        "interpretation": interpretation,
        "uncertainty_notes": uncertainty_text,
        "limitations": limitation_text,
        "recommended_verification": (
            "For consequential decisions, verify the sample using an "
            "appropriate validated laboratory method and qualified personnel."
        ),
        "analysis_mode": "deterministic_fallback",
    }


def _parse_llm_output(response: str) -> dict[str, Any]:
    """Parse and validate the required JSON structure from an LLM."""

    def reject_non_finite(value: str) -> None:
        raise ValueError(f"Non-finite JSON value is not allowed: {value}")

    try:
        parsed = json.loads(response, parse_constant=reject_non_finite)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AnalystError("LLM response was not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise AnalystError("LLM response must be a JSON object.")

    missing = [field for field in OUTPUT_FIELDS if field not in parsed]
    if missing:
        raise AnalystError(
            f"LLM response is missing required fields: {', '.join(missing)}"
        )

    for field in (
        "summary",
        "interpretation",
        "recommended_verification",
    ):
        value = parsed[field]
        if not isinstance(value, str) or not value.strip():
            raise AnalystError(
                f"LLM output field '{field}' must be a non-empty string."
            )
    if not isinstance(parsed["model_result"], dict):
        raise AnalystError("LLM output field 'model_result' must be an object.")
    for field in ("supporting_evidence", "uncertainty_notes", "limitations"):
        value = parsed[field]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise AnalystError(
                f"LLM output field '{field}' must be a list of strings."
            )

    return parsed


def _call_llm(payload: dict[str, Any]) -> dict[str, Any]:
    """Call an optional OpenAI-compatible API when configured.

    The OpenAI SDK is imported only when an API key is available.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AnalystError("No LLM provider is configured.")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("FOODSURE_LLM_MODEL", "gpt-4.1-mini")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            evidence_payload=json.dumps(
                payload, ensure_ascii=False, allow_nan=False
            )
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        parsed = _parse_llm_output(content)
        model_result = parsed["model_result"]
        if model_result.get("prediction") != payload["model_result"].get("prediction"):
            raise AnalystError(
                "LLM response did not preserve the supplied model prediction."
            )
        parsed["model_result"] = payload["model_result"].copy()

        parsed["analysis_mode"] = "llm"
        parsed["model_version"] = payload["model_version"]
        return parsed

    except AnalystError:
        raise
    except Exception as exc:
        # Do not log credentials, raw requests, or sensitive payloads.
        raise AnalystError(
            f"LLM analysis failed ({type(exc).__name__})."
        ) from exc


def analyze(
    payload: dict[str, Any],
    *,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Analyze model evidence, falling back to deterministic templates."""

    validate_payload(payload)

    if use_llm:
        try:
            return _call_llm(payload)
        except AnalystError:
            # A transparent mode field identifies the fallback.
            result = deterministic_analysis(payload)
            result["analysis_mode"] = "deterministic_fallback"
            result["provider_note"] = (
                "LLM analysis was unavailable or invalid; "
                "deterministic analysis was used."
            )
            return result

    return deterministic_analysis(payload)