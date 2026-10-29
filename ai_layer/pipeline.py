"""Orchestration of the saved FoodSure predictor and the AI reporting layer."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai_layer.analyst import analyze, deterministic_analysis
from ai_layer.evidence import build_evidence_payload
from ai_layer.report_generator import generate_report, report_to_json
from ai_layer.uncertainty import assess_uncertainty
from ml_service.predictor import DEFAULT_MODEL_PATH, predict_sample


class PipelineInputError(ValueError):
    """Raised when a prediction request or assessment context is malformed."""


class PipelineOutputError(ValueError):
    """Raised when a predictor or analyst result violates its saved contract."""


_PREDICTOR_INPUTS = {
    "color_features",
    "ftir_features",
    "image_features",
}
_MODALITY_NAMES = {
    "Color": "color",
    "FTIR": "ftir",
    "Image": "image",
}
_PREDICTION_FIELDS = {
    "predicted_class",
    "predicted_percentage",
    "modality_configuration",
    "model_version",
    "probabilities",
}
_ANALYSIS_TEXT_FIELDS = (
    "executive_summary",
    "result_interpretation",
    "scientific_explanation",
    "confidence_and_uncertainty",
    "practical_implications",
)


def _artifact_metadata_path(model_path: str | Path) -> Path:
    artifact = Path(model_path)
    return artifact.with_name(f"{artifact.stem}_metadata.json")


def _load_optional_metadata(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineOutputError(
            f"Could not read model metadata sidecar: {path}"
        ) from exc
    if not isinstance(metadata, dict):
        raise PipelineOutputError("Model metadata sidecar must contain a JSON object.")
    return metadata


def _validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise PipelineInputError("request must be a mapping of predictor input names to features.")
    unknown = set(request) - _PREDICTOR_INPUTS
    if unknown:
        raise PipelineInputError(
            f"Unsupported predictor request fields: {', '.join(sorted(unknown))}"
        )
    supplied = {key: value for key, value in request.items() if value is not None}
    if not supplied:
        raise PipelineInputError("At least one modality feature input is required.")
    return supplied


def _validate_prediction(
    prediction: Any,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(prediction, dict):
        raise PipelineOutputError("Predictor output must be a dictionary.")
    missing = _PREDICTION_FIELDS - prediction.keys()
    if missing:
        raise PipelineOutputError(
            f"Predictor output is missing fields: {', '.join(sorted(missing))}"
        )
    if not isinstance(prediction["predicted_class"], str) or not prediction["predicted_class"].strip():
        raise PipelineOutputError("'predicted_class' must be a non-empty string.")
    if prediction["probabilities"] is not None:
        raise PipelineOutputError(
            "Predictor returned probabilities, but this model has no verified calibration contract."
        )
    percentage = prediction["predicted_percentage"]
    if (
        percentage is None
        or isinstance(percentage, bool)
        or not isinstance(percentage, (int, float))
        or not math.isfinite(percentage)
    ):
        raise PipelineOutputError(
            "'predicted_percentage' must be a finite numeric regression estimate."
        )

    modalities = prediction["modality_configuration"]
    if (
        not isinstance(modalities, list)
        or not modalities
        or not all(
            isinstance(item, str) and item in _MODALITY_NAMES
            for item in modalities
        )
        or len(modalities) != len(set(modalities))
    ):
        raise PipelineOutputError(
            "'modality_configuration' must contain unique supported modality names."
        )
    version = prediction["model_version"]
    if not isinstance(version, str) or not version.strip():
        raise PipelineOutputError("'model_version' must be a non-empty string.")

    if metadata is not None:
        if metadata.get("model_version") != version:
            raise PipelineOutputError(
                "Predictor model version does not match the saved metadata sidecar."
            )
        if metadata.get("modality_configuration") != modalities:
            raise PipelineOutputError(
                "Predictor modalities do not match the saved metadata sidecar."
            )
        feature_order = metadata.get("feature_order")
        if not isinstance(feature_order, dict):
            raise PipelineOutputError(
                "Saved model metadata has no valid feature_order mapping."
            )
        for modality in modalities:
            columns = feature_order.get(modality)
            if (
                not isinstance(columns, list)
                or not columns
                or not all(isinstance(column, str) for column in columns)
                or len(columns) != len(set(columns))
            ):
                raise PipelineOutputError(
                    f"Saved model metadata has no valid feature order for {modality}."
                )
        pca_details = metadata.get("pca_components_and_explained_variance", {})
        if not isinstance(pca_details, dict):
            raise PipelineOutputError(
                "Saved model metadata has invalid PCA preprocessing details."
            )
        supported_labels = metadata.get("class_labels_percentage")
        if (
            not isinstance(supported_labels, list)
            or not supported_labels
            or any(
                isinstance(label, bool)
                or not isinstance(label, (int, float))
                or not math.isfinite(label)
                for label in supported_labels
            )
            or len(set(supported_labels)) != len(supported_labels)
        ):
            raise PipelineOutputError(
                "Saved model metadata has no valid class_labels_percentage list."
            )
        expected_labels = {f"{float(label):g}%" for label in supported_labels}
        if prediction["predicted_class"] not in expected_labels:
            raise PipelineOutputError(
                "Predictor returned a classification label not supported by "
                "the saved model metadata."
            )
    return prediction


def _metadata_summary(
    metadata: dict[str, Any] | None,
    modalities: list[str],
) -> dict[str, Any] | None:
    if metadata is None:
        return None
    feature_order = metadata["feature_order"]
    pca_details = metadata.get("pca_components_and_explained_variance", {})
    return {
        "model_version": metadata["model_version"],
        "classification_model": metadata.get("classification_model"),
        "regression_model": metadata.get("regression_model"),
        "modality_configuration": list(metadata["modality_configuration"]),
        "feature_order": {name: list(feature_order[name]) for name in modalities},
        "pca_components_and_explained_variance": {
            name: pca_details.get(name)
            for name in modalities
        },
        "training_split": metadata.get("training_split"),
        "probability_calibration": metadata.get("probability_calibration"),
    }


def _assessment_context(
    detector_result: Mapping[str, Any] | None,
    calibration_info: Mapping[str, Any] | None,
) -> tuple[bool | None, float | None, bool]:
    out_of_distribution = None
    if detector_result is not None:
        if not isinstance(detector_result, Mapping):
            raise PipelineInputError("detector_result must be a mapping or None.")
        unknown = set(detector_result) - {"out_of_distribution", "detector_name"}
        if unknown:
            raise PipelineInputError(
                f"Unsupported detector result fields: {', '.join(sorted(unknown))}"
            )
        out_of_distribution = detector_result.get("out_of_distribution")
        if not isinstance(out_of_distribution, bool):
            raise PipelineInputError(
                "detector_result must explicitly supply a boolean out_of_distribution value."
            )
        if "detector_name" in detector_result and (
            not isinstance(detector_result["detector_name"], str)
            or not detector_result["detector_name"].strip()
        ):
            raise PipelineInputError("detector_name must be a non-empty string.")

    confidence = None
    confidence_calibrated = False
    if calibration_info is not None:
        if not isinstance(calibration_info, Mapping):
            raise PipelineInputError("calibration_info must be a mapping or None.")
        unknown = set(calibration_info) - {"confidence", "calibrated"}
        if unknown:
            raise PipelineInputError(
                f"Unsupported calibration fields: {', '.join(sorted(unknown))}"
            )
        confidence = calibration_info.get("confidence")
        confidence_calibrated = calibration_info.get("calibrated", False)
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
            or not isinstance(confidence_calibrated, bool)
        ):
            raise PipelineInputError(
                "calibration_info must include a finite confidence from 0 to 1 "
                "and a boolean calibrated flag."
            )
    return out_of_distribution, confidence, confidence_calibrated


def run_pipeline(
    request: Mapping[str, Any],
    *,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    use_llm: bool = False,
    detector_result: Mapping[str, Any] | None = None,
    calibration_info: Mapping[str, Any] | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the real predictor, uncertainty checks, analyst, and report builder.

    ``request`` uses the predictor's keyword names and feature ordering. Image
    data, when requested by a model, must be precomputed EfficientNet-B0
    embeddings. LLM output is never included in the report unless it can be
    independently substantiated; currently the report uses deterministic
    analysis while allowing the analyst provider to be probed when opted in.
    """
    if not isinstance(use_llm, bool):
        raise PipelineInputError("use_llm must be boolean.")
    supplied = _validate_request(request)
    if evidence_items is not None and (
        not isinstance(evidence_items, list)
        or not all(isinstance(item, dict) for item in evidence_items)
    ):
        raise PipelineInputError("evidence_items must be a list of evidence dictionaries.")
    for item in evidence_items or []:
        if not isinstance(item.get("description"), str) or not item[
            "description"
        ].strip():
            raise PipelineInputError(
                "Each evidence item requires a non-empty string description."
            )
        source = item.get("source")
        if source is not None and (
            not isinstance(source, str) or not source.strip()
        ):
            raise PipelineInputError(
                "Evidence item source must be a non-empty string when supplied."
            )
    out_of_distribution, confidence, confidence_calibrated = _assessment_context(
        detector_result, calibration_info
    )

    artifact_path = Path(model_path).resolve()
    metadata = _load_optional_metadata(_artifact_metadata_path(artifact_path))
    raw_prediction = predict_sample(**supplied, model_path=artifact_path)
    prediction = _validate_prediction(raw_prediction, metadata)
    modalities = prediction["modality_configuration"]
    version = prediction["model_version"]
    classification = {
        "prediction": prediction["predicted_class"],
        "target_type": "classification label",
        "classification_label": prediction["predicted_class"],
        "classification_label_is_measurement": False,
        "regression_estimate": prediction["predicted_percentage"],
        "regression_target_type": (
            "continuous model estimate"
            if prediction["predicted_percentage"] is not None
            else None
        ),
        "probabilities": None,
    }

    verified_evidence = [
        {
            **item,
            "source": (
                "caller-supplied and not independently verified"
                if not item.get("source")
                else (
                    f"caller-supplied and not independently verified; "
                    f"claimed source: {item['source']}"
                )
            ),
        }
        for item in (evidence_items or [])
    ]
    external_validation_available = None
    if metadata is not None:
        training_split = metadata.get("training_split", {})
        if (
            version == "foodsure-ml-v1"
            and isinstance(training_split, dict)
            and training_split.get("training_sample_count") == 280
            and training_split.get("heldout_sample_count") == 70
        ):
            external_validation_available = False
            external_validation_limit = (
                "This model was evaluated on the project's controlled 350-sample dataset; "
                "independent external validation is not established."
            )
        else:
            external_validation_limit = (
                "Independent external validation status is not recorded in the available model metadata."
            )
    else:
        external_validation_limit = (
            "Model metadata is unavailable; independent external validation status was not verified."
        )
    limitations = [
        external_validation_limit,
        "A classification label is a model class, not a laboratory measurement; any regression output is a separate continuous model estimate.",
        "The saved model does not provide calibrated class probabilities or sample-specific feature explanations.",
    ]
    uncertainty_flags: list[str] = []
    if metadata is not None:
        model_name = metadata.get("classification_model")
        if isinstance(model_name, str) and model_name:
            verified_evidence.append({
                "description": (
                    f"Saved model metadata identifies {model_name} for "
                    f"{', '.join(modalities)}."
                ),
                "source": "saved model metadata",
            })
        training_split = metadata.get("training_split", {})
        if isinstance(training_split, dict):
            train_count = training_split.get("training_sample_count")
            heldout_count = training_split.get("heldout_sample_count")
            if isinstance(train_count, int) and isinstance(heldout_count, int):
                verified_evidence.append({
                    "description": (
                        f"Saved model metadata records {train_count} training and "
                        f"{heldout_count} held-out samples from the project dataset."
                    ),
                    "source": "saved model metadata",
                })
    else:
        uncertainty_flags.append(
            "The model metadata sidecar is unavailable; model details and feature names were omitted."
        )

    uncertainty_flags.append(
        "No sample-specific feature attribution was generated; caller-provided evidence is not independently verified."
    )

    evidence_payload = build_evidence_payload(
        model_version=version,
        modalities_used=[_MODALITY_NAMES[name] for name in modalities],
        model_result=classification,
        evidence_items=verified_evidence,
        uncertainty_flags=uncertainty_flags,
        limitations=limitations,
    )
    uncertainty = assess_uncertainty(
        model_result=classification,
        modalities_used=evidence_payload["modalities_used"],
        evidence=evidence_payload["evidence"],
        confidence=confidence,
        confidence_calibrated=confidence_calibrated,
        out_of_distribution=out_of_distribution,
        external_validation_available=external_validation_available,
        model_scope_supported=None,
        existing_flags=evidence_payload["uncertainty_flags"],
    )

    analysis_candidate = analyze(evidence_payload, use_llm=use_llm)
    if not isinstance(analysis_candidate, dict):
        raise PipelineOutputError("Analyst output must be a dictionary.")
    if analysis_candidate.get("analysis_mode") in ("llm", "gemini_llm"):
        analysis = deterministic_analysis(evidence_payload)
        analysis["provider_note"] = (
            "LLM narrative was excluded because its factual claims were not "
            "independently verifiable from the supplied evidence."
        )
        uncertainty["flags"].append(
            "LLM-generated narrative was excluded pending independent evidence validation."
        )
        uncertainty["status"] = "caution"
    else:
        analysis = analysis_candidate
    for field in _ANALYSIS_TEXT_FIELDS:
        if not isinstance(analysis.get(field), str):
            raise PipelineOutputError(
                f"Analyst output requires string field '{field}'."
            )
    # Validate list fields in new 8-section schema
    for field in ("recommended_next_steps", "limitations"):
        if not isinstance(analysis.get(field), list) or not all(
            isinstance(item, str) for item in analysis[field]
        ):
            raise PipelineOutputError(
                f"Analyst output field '{field}' must be a list of strings."
            )
    # Validate evidence_and_reasoning list
    ear = analysis.get("evidence_and_reasoning", [])
    if not isinstance(ear, list):
        raise PipelineOutputError("Analyst output 'evidence_and_reasoning' must be a list.")

    report = generate_report(
        evidence_payload=evidence_payload,
        analyst_result=analysis,
        uncertainty_result=uncertainty,
    )
    report_to_json(report, indent=2)

    return {
        "prediction": prediction.copy(),
        "explanation": analysis,
        "evidence": evidence_payload,
        "uncertainty_warnings": list(uncertainty["flags"]),
        "uncertainty": uncertainty,
        "model_version": version,
        "modalities_used": list(modalities),
        "model_metadata": _metadata_summary(metadata, modalities),
        "report": report,
    }
