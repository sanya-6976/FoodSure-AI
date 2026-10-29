"""Small adapters from UI inputs to the existing FoodSure pipeline."""

from __future__ import annotations

import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ai_layer.pipeline import run_pipeline
from ml_service.experiments import _load_data
from ml_service.predictor import DEFAULT_MODEL_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = DEFAULT_MODEL_PATH.with_name(
    f"{DEFAULT_MODEL_PATH.stem}_metadata.json"
)


def load_metadata() -> dict[str, Any]:
    if not DEFAULT_MODEL_PATH.is_file():
        raise FileNotFoundError("The saved FoodSure model artifact is not installed.")
    if not METADATA_PATH.is_file():
        raise FileNotFoundError("The saved FoodSure model metadata is not installed.")
    try:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("The saved FoodSure model metadata could not be read.") from exc
    if not isinstance(metadata, dict):
        raise ValueError("The saved FoodSure model metadata is malformed.")
    feature_order = metadata.get("feature_order")
    ftir_columns = feature_order.get("FTIR") if isinstance(feature_order, dict) else None
    if (
        not isinstance(ftir_columns, list)
        or not ftir_columns
        or not all(isinstance(column, str) for column in ftir_columns)
        or len(ftir_columns) != len(set(ftir_columns))
    ):
        raise ValueError("The model metadata has no valid FTIR feature order.")
    return metadata


def parse_ftir_csv(file_bytes: bytes, feature_columns: list[str]) -> tuple[str | None, pd.DataFrame]:
    try:
        table = pd.read_csv(io.BytesIO(file_bytes))
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        raise ValueError("The uploaded file is not a readable CSV.") from exc
    if len(table) != 1:
        raise ValueError("Upload a CSV containing exactly one sample row.")
    if not table.columns.is_unique:
        raise ValueError("The uploaded CSV contains duplicate column names.")
    if "Target" in table.columns or "Adulteration_Percent" in table.columns:
        raise ValueError("Remove target/label columns before uploading the spectrum.")

    sample_id: str | None = None
    if "Sample_ID" in table.columns:
        value = table.pop("Sample_ID").iloc[0]
        if pd.isna(value) or not str(value).strip():
            raise ValueError("Sample_ID must not be empty when provided.")
        sample_id = str(value).strip()

    missing = [column for column in feature_columns if column not in table.columns]
    extra = [column for column in table.columns if column not in feature_columns]
    if missing or extra:
        details = []
        if missing:
            details.append(f"{len(missing)} required feature column(s) are missing")
        if extra:
            details.append(f"{len(extra)} unexpected column(s) were found")
        raise ValueError(
            "The CSV columns must match the saved FTIR feature names exactly; "
            + " and ".join(details)
            + "."
        )

    features = table.loc[:, feature_columns].copy()
    try:
        features = features.apply(pd.to_numeric, errors="raise")
        values = features.to_numpy(dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("All FTIR feature values must be numeric.") from exc
    if not np.isfinite(values).all():
        raise ValueError("FTIR feature values must all be finite numbers.")
    return sample_id, pd.DataFrame(values, columns=feature_columns)


def load_dataset() -> dict[str, Any]:
    return _load_data(PROJECT_ROOT)


def dataset_sample(
    data: dict[str, Any],
    sample_id: str,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, float]:
    try:
        features = data["features"]["FTIR"]
        row = features.loc[[sample_id], feature_columns]
        target_by_id = dict(zip(data["train_ids"], data["y_train"]))
        target_by_id.update(dict(zip(data["test_ids"], data["y_test"])))
        actual = float(target_by_id[sample_id])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("The selected dataset sample could not be loaded.") from exc
    if row.shape != (1, len(feature_columns)) or not math.isfinite(actual):
        raise ValueError("The selected dataset sample has invalid features or target.")
    return row.reset_index(drop=True), actual


def predict_ftir(features: pd.DataFrame) -> dict[str, Any]:
    return run_pipeline({"ftir_features": features}, use_llm=False)
