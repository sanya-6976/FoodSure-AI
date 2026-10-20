"""Run the saved FoodSure model through the public AI pipeline.

The all-zero FTIR row is synthetic input for a software smoke test only. It
does not represent a measured spectrum or contribute to model evaluation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_layer.pipeline import run_pipeline
from ml_service.predictor import DEFAULT_MODEL_PATH, predict_sample


def main() -> int:
    metadata_path = DEFAULT_MODEL_PATH.with_name(
        f"{DEFAULT_MODEL_PATH.stem}_metadata.json"
    )
    if not DEFAULT_MODEL_PATH.is_file():
        raise FileNotFoundError(f"Required model artifact is missing: {DEFAULT_MODEL_PATH}")
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Required model metadata is missing: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    feature_order = metadata.get("feature_order")
    ftir_columns = feature_order.get("FTIR") if isinstance(feature_order, dict) else None
    if (
        not isinstance(ftir_columns, list)
        or not ftir_columns
        or not all(isinstance(column, str) for column in ftir_columns)
    ):
        raise ValueError("Model metadata does not contain a usable FTIR feature order.")

    # Named columns let the real predictor check the exact saved ordering.
    synthetic_ftir = pd.DataFrame(
        np.zeros((1, len(ftir_columns)), dtype=np.float64),
        columns=ftir_columns,
    )
    request = {"ftir_features": synthetic_ftir}

    prediction = predict_sample(**request)
    repeated_prediction = predict_sample(**request)
    if prediction != repeated_prediction:
        raise RuntimeError("Repeated prediction for the same input was not deterministic.")

    # Force the documented provider-unavailable path without reading or exposing
    # any caller API key and without making a network request.
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        result = run_pipeline(request, use_llm=True)

    if result["prediction"] != prediction:
        raise RuntimeError("Pipeline output does not match the real predictor output.")
    if result["explanation"].get("analysis_mode") != "deterministic_fallback":
        raise RuntimeError("Provider-unavailable path did not use deterministic fallback.")
    if result["uncertainty_warnings"] != result["report"]["uncertainty"]["flags"]:
        raise RuntimeError("Report did not preserve pipeline uncertainty warnings.")
    if result["report"]["model_version"] != prediction["model_version"]:
        raise RuntimeError("Report model version does not match the predictor.")
    if result["report"]["model_result"].get("prediction") != prediction["predicted_class"]:
        raise RuntimeError("Report did not preserve the classifier label.")
    if result["report"]["model_result"].get("regression_estimate") != prediction[
        "predicted_percentage"
    ]:
        raise RuntimeError("Report did not preserve the separate regression estimate.")
    if not result["report"].get("disclaimer", "").startswith(
        "FoodSure AI is a research prototype"
    ):
        raise RuntimeError("Research-prototype disclaimer is missing from the report.")

    invalid_input_rejection: dict[str, str | bool]
    wrong_width = pd.DataFrame(
        np.zeros((1, len(ftir_columns) - 1), dtype=np.float64),
        columns=ftir_columns[:-1],
    )
    try:
        run_pipeline({"ftir_features": wrong_width})
    except ValueError as exc:
        invalid_input_rejection = {
            "passed": True,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
    else:
        raise RuntimeError("Invalid feature dimensions were not rejected.")

    payload = {
        "demonstration_notice": (
            "Synthetic all-zero feature input; software demonstration only. "
            "This is not a measured sample or an accuracy evaluation."
        ),
        "input": {
            "modality": "FTIR",
            "shape": list(synthetic_ftir.shape),
            "feature_order_source": "saved model metadata",
        },
        "checks": {
            "model_artifact_loaded": True,
            "metadata_loaded": True,
            "same_input_prediction_repeatable": True,
            "pipeline_prediction_matches_predictor": True,
            "provider_unavailable_uses_deterministic_fallback": True,
            "uncertainty_warnings_preserved_in_report": True,
            "invalid_feature_dimensions_rejected": invalid_input_rejection,
            "research_disclaimer_present": True,
        },
        "prediction": prediction,
        "pipeline_result": result,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, ValueError, RuntimeError) as exc:
        print(f"FoodSure backend smoke demo failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
