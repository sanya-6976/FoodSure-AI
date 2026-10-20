"""Prediction interface for the validated FoodSure multimodal model.

Image inputs are EfficientNet-B0 feature vectors, not raw images.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "models" / "foodsure_multimodal_v1.joblib"
)
SUPPORTED_MODALITIES = {"Color", "FTIR", "Image"}


def _contains_non_numeric_scalars(values: np.ndarray) -> bool:
    return values.dtype.kind in "Mm" or any(
        isinstance(
            value,
            (
                bool,
                np.bool_,
                complex,
                np.complexfloating,
                str,
                bytes,
                date,
                timedelta,
                np.datetime64,
                np.timedelta64,
            ),
        )
        for value in values.astype(object, copy=False).flat
    )


def _has_masked_values(values: Any) -> bool:
    return np.ma.isMaskedArray(values) and bool(np.ma.getmaskarray(values).any())


@lru_cache(maxsize=4)
def _load_cached_model(
    model_path: str,
    model_digest: str,
    metadata_digest: str,
) -> dict[str, Any]:
    path = Path(model_path)
    try:
        is_file = path.is_file()
    except OSError as exc:
        raise ValueError(f"Could not inspect FoodSure model artifact: {path}") from exc
    if not is_file:
        raise FileNotFoundError(f"FoodSure model artifact not found: {path}")
    if _sha256_file(path) != model_digest:
        raise ValueError(f"FoodSure model artifact changed while loading: {path}")
    metadata_path = path.with_name(f"{path.stem}_metadata.json")
    try:
        metadata_exists = metadata_path.exists()
    except OSError as exc:
        raise ValueError(
            f"Could not inspect FoodSure model metadata sidecar: {metadata_path}"
        ) from exc
    if metadata_exists != bool(metadata_digest):
        raise ValueError(f"FoodSure model metadata changed while loading: {metadata_path}")
    if metadata_digest and _sha256_file(metadata_path) != metadata_digest:
        raise ValueError(f"FoodSure model metadata changed while loading: {metadata_path}")
    try:
        bundle = joblib.load(path)
    except Exception as exc:
        raise ValueError(f"Could not load FoodSure model artifact: {path}") from exc
    _validate_model_bundle(bundle, path)
    _validate_metadata_sidecar(bundle, path)
    return bundle


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(
            f"Could not read artifact to validate its contents: {path}"
        ) from exc
    return digest.hexdigest()


def _finite_numeric_labels(values: Any, field: str) -> list[float]:
    if not isinstance(values, (list, tuple, np.ndarray)):
        raise ValueError(f"Model artifact '{field}' must be a non-empty sequence.")
    if isinstance(values, np.ndarray) and values.ndim != 1:
        raise ValueError(f"Model artifact '{field}' must be a non-empty sequence.")
    if len(values) == 0:
        raise ValueError(f"Model artifact '{field}' must be a non-empty sequence.")
    labels: list[float] = []
    for value in values:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, float, np.integer, np.floating)
        ):
            raise ValueError(f"Model artifact '{field}' must contain numeric labels.")
        try:
            numeric = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Model artifact '{field}' must contain finite labels."
            ) from exc
        if not math.isfinite(numeric):
            raise ValueError(f"Model artifact '{field}' must contain finite labels.")
        labels.append(numeric)
    if len(set(labels)) != len(labels):
        raise ValueError(f"Model artifact '{field}' contains duplicate labels.")
    return labels


def _is_feature_count(value: Any, expected: int) -> bool:
    return (
        not isinstance(value, (bool, np.bool_))
        and isinstance(value, (int, np.integer))
        and value == expected
    )


def _metadata_value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(
                _metadata_value_matches(actual[key], expected[key])
                for key in expected
            )
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(
                _metadata_value_matches(actual_value, expected_value)
                for actual_value, expected_value in zip(actual, expected)
            )
        )
    if isinstance(actual, (bool, np.bool_)) or isinstance(
        expected, (bool, np.bool_)
    ):
        return (
            isinstance(actual, (bool, np.bool_))
            and isinstance(expected, (bool, np.bool_))
            and actual == expected
        )
    return actual == expected


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _validate_model_bundle(bundle: Any, path: Path) -> None:
    if not isinstance(bundle, dict):
        raise ValueError(f"FoodSure model artifact must contain a dictionary: {path}")
    required_keys = {
        "model_version",
        "modality_configuration",
        "feature_columns",
        "preprocessors",
        "classifier",
        "regressor",
    }
    missing_keys = required_keys.difference(bundle)
    if missing_keys:
        raise ValueError(
            f"Model artifact is missing required fields: {sorted(missing_keys)}"
        )

    version = bundle["model_version"]
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Model artifact 'model_version' must be a non-empty string.")
    configuration = bundle["modality_configuration"]
    if (
        not isinstance(configuration, list)
        or not configuration
        or not all(
            isinstance(modality, str) and modality in SUPPORTED_MODALITIES
            for modality in configuration
        )
        or len(configuration) != len(set(configuration))
    ):
        raise ValueError(
            "Model artifact 'modality_configuration' must list unique supported modalities."
        )

    columns_by_modality = bundle["feature_columns"]
    preprocessors = bundle["preprocessors"]
    if not isinstance(columns_by_modality, dict) or not isinstance(preprocessors, dict):
        raise ValueError(
            "Model artifact feature_columns and preprocessors must be dictionaries."
        )
    try:
        classifier_predict = getattr(bundle["classifier"], "predict", None)
    except (RuntimeError, TypeError) as exc:
        raise ValueError("Could not inspect classifier predict method.") from exc
    if not callable(classifier_predict):
        raise ValueError("Model artifact classifier must provide predict().")
    try:
        regressor_predict = getattr(bundle["regressor"], "predict", None)
    except (RuntimeError, TypeError) as exc:
        raise ValueError("Could not inspect regressor predict method.") from exc
    if not callable(regressor_predict):
        raise ValueError("Model artifact regressor must provide predict().")

    class_labels = _finite_numeric_labels(bundle.get("class_labels"), "class_labels")
    try:
        raw_classifier_classes = getattr(bundle["classifier"], "classes_", None)
    except (RuntimeError, TypeError) as exc:
        raise ValueError("Could not read classifier class labels.") from exc
    classifier_classes = _finite_numeric_labels(
        raw_classifier_classes, "classifier.classes_"
    )
    if set(class_labels) != set(classifier_classes):
        raise ValueError(
            "Model artifact class_labels do not match classifier.classes_."
        )

    expected_transformed_features = 0
    for modality in configuration:
        columns = columns_by_modality.get(modality)
        if (
            not isinstance(columns, list)
            or not columns
            or not all(isinstance(column, str) and column for column in columns)
            or len(columns) != len(set(columns))
        ):
            raise ValueError(
                f"Model artifact has invalid or duplicate feature columns for {modality}."
            )
        preprocessing = preprocessors.get(modality)
        if not isinstance(preprocessing, dict):
            raise ValueError(
                f"Model artifact has no preprocessing bundle for {modality}."
            )
        scaler = preprocessing.get("scaler")
        try:
            scaler_transform = getattr(scaler, "transform", None)
        except (RuntimeError, TypeError) as exc:
            raise ValueError(
                f"Could not inspect scaler transform for {modality}."
            ) from exc
        if not callable(scaler_transform):
            raise ValueError(f"Model artifact scaler for {modality} has no transform().")
        try:
            scaler_features = getattr(scaler, "n_features_in_", None)
        except (RuntimeError, TypeError) as exc:
            raise ValueError(
                f"Could not read scaler feature count for {modality}."
            ) from exc
        if not _is_feature_count(scaler_features, len(columns)):
            raise ValueError(
                f"Model artifact scaler feature count for {modality} does not match feature_columns."
            )
        pca = preprocessing.get("pca")
        if pca is not None:
            try:
                pca_transform = getattr(pca, "transform", None)
            except (RuntimeError, TypeError) as exc:
                raise ValueError(
                    f"Could not inspect PCA transform for {modality}."
                ) from exc
            if not callable(pca_transform):
                raise ValueError(f"Model artifact PCA for {modality} has no transform().")
            try:
                pca_features = getattr(pca, "n_features_in_", None)
                component_count = getattr(pca, "n_components_", None)
            except (RuntimeError, TypeError) as exc:
                raise ValueError(
                    f"Could not read PCA dimensions for {modality}."
                ) from exc
            if not _is_feature_count(pca_features, len(columns)):
                raise ValueError(
                    f"Model artifact PCA input feature count for {modality} is incompatible."
                )
            if (
                isinstance(component_count, (bool, np.bool_))
                or not isinstance(component_count, (int, np.integer))
                or component_count < 1
            ):
                raise ValueError(f"Model artifact PCA for {modality} has invalid components.")
            if component_count > len(columns):
                raise ValueError(
                    f"Model artifact PCA component count for {modality} exceeds "
                    "the input feature count."
                )
            expected_transformed_features += int(component_count)
        else:
            expected_transformed_features += len(columns)

    for estimator_name in ("classifier", "regressor"):
        try:
            estimator_features = getattr(
                bundle[estimator_name], "n_features_in_", None
            )
        except (RuntimeError, TypeError) as exc:
            raise ValueError(
                f"Could not read {estimator_name} input dimension."
            ) from exc
        if not _is_feature_count(estimator_features, expected_transformed_features):
            raise ValueError(
                f"Model artifact {estimator_name} input dimension "
                "does not match the saved preprocessing pipeline."
            )


def _validate_metadata_sidecar(bundle: dict[str, Any], artifact_path: Path) -> None:
    metadata_path = artifact_path.with_name(
        f"{artifact_path.stem}_metadata.json"
    )
    if not metadata_path.exists():
        return
    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(
            f"Could not read model metadata sidecar: {metadata_path}"
        ) from exc
    except ValueError as exc:
        raise ValueError(f"Invalid model metadata sidecar: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("Model metadata sidecar must contain a JSON object.")

    expected_fields = {
        "model_version": bundle["model_version"],
        "modality_configuration": bundle["modality_configuration"],
        "feature_order": bundle["feature_columns"],
        "class_labels_percentage": _finite_numeric_labels(
            bundle["class_labels"], "class_labels"
        ),
    }
    for key, expected in expected_fields.items():
        if not _metadata_value_matches(metadata.get(key), expected):
            raise ValueError(
                f"Model metadata field '{key}' does not match the saved model artifact."
            )

    if not isinstance(metadata.get("classification_model"), str) or not metadata[
        "classification_model"
    ].strip():
        raise ValueError(
            "Model metadata 'classification_model' must be a non-empty string."
        )
    if not isinstance(metadata.get("regression_model"), str) or not metadata[
        "regression_model"
    ].strip():
        raise ValueError(
            "Model metadata 'regression_model' must be a non-empty string."
        )
    classifier_names = {
        "LogisticRegression": "Logistic Regression",
        "SVC": "SVM (RBF)",
        "RandomForestClassifier": "Random Forest",
    }
    regressor_names = {
        "RandomForestRegressor": "Random Forest Regressor",
        "Ridge": "Ridge Regression",
    }
    classifier_name = classifier_names.get(type(bundle["classifier"]).__name__)
    regressor_name = regressor_names.get(type(bundle["regressor"]).__name__)
    if classifier_name is None or metadata["classification_model"] != classifier_name:
        raise ValueError(
            "Model metadata classification_model does not match the saved estimator."
        )
    if regressor_name is None or metadata["regression_model"] != regressor_name:
        raise ValueError(
            "Model metadata regression_model does not match the saved estimator."
        )

    pca_details = metadata.get("pca_components_and_explained_variance")
    if not isinstance(pca_details, dict):
        raise ValueError(
            "Model metadata must include pca_components_and_explained_variance."
        )
    for modality in bundle["modality_configuration"]:
        details = pca_details.get(modality)
        if not isinstance(details, dict):
            raise ValueError(
                f"Model metadata has no PCA details for {modality}."
            )
        pca = bundle["preprocessors"][modality].get("pca")
        if pca is None:
            if details.get("components") is not None or details.get(
                "explained_variance"
            ) is not None:
                raise ValueError(
                    f"Model metadata reports PCA for untransformed {modality} features."
                )
            continue
        components = details.get("components")
        explained = details.get("explained_variance")
        variance_ratios = getattr(pca, "explained_variance_ratio_", None)
        if _has_masked_values(variance_ratios):
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            )
        try:
            variance_ratios = np.asarray(variance_ratios)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            ) from exc
        if (
            variance_ratios.shape != (int(pca.n_components_),)
            or _contains_non_numeric_scalars(variance_ratios)
        ):
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            )
        try:
            variance_ratios = variance_ratios.astype(np.float64)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            ) from exc
        except OverflowError as exc:
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            ) from exc
        if not np.isfinite(variance_ratios).all():
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            )
        expected_explained = float(variance_ratios.sum())
        if (
            np.any(variance_ratios < 0)
            or np.any(variance_ratios > 1)
            or expected_explained <= 0
            or expected_explained > 1 + 1e-9
        ):
            raise ValueError(
                f"Model artifact PCA explained variance ratio for {modality} is invalid."
            )
        try:
            explained_value = float(explained)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Model metadata PCA details for {modality} do not match the saved estimator."
            ) from exc
        if (
            isinstance(components, bool)
            or not isinstance(components, int)
            or components != int(pca.n_components_)
            or isinstance(explained, bool)
            or not isinstance(explained, (int, float))
            or not math.isfinite(explained_value)
            or not math.isclose(
                explained_value, expected_explained, rel_tol=1e-9, abs_tol=1e-12
            )
        ):
            raise ValueError(
                f"Model metadata PCA details for {modality} do not match the saved estimator."
            )


def _validated_row(
    values: Any,
    modality: str,
    feature_columns: list[str],
) -> pd.DataFrame | None:
    if values is None:
        return None

    if not isinstance(values, (pd.DataFrame, pd.Series, np.ndarray, list, tuple)):
        raise ValueError(
            f"{modality} must be a one-dimensional vector, single-row matrix, Series, or DataFrame."
        )
    if _has_masked_values(values):
        raise ValueError(f"{modality} features must not contain masked feature values.")
    if isinstance(values, pd.Series):
        series_index = list(values.index)
        if any(isinstance(column, str) for column in series_index) and (
            not all(isinstance(column, str) for column in series_index)
            or not values.index.is_unique
            or series_index != feature_columns
        ):
            raise ValueError(
                f"{modality} feature names must match the saved order exactly "
                f"({len(feature_columns)} columns expected)"
            )
        raw_values = values.to_numpy().reshape(1, -1)
    elif isinstance(values, pd.DataFrame):
        if values.shape[0] != 1:
            raise ValueError(
                f"{modality} must contain exactly one sample; got {values.shape[0]} rows"
            )
        if list(values.columns) != feature_columns:
            raise ValueError(
                f"{modality} feature columns must match the saved order exactly "
                f"({len(feature_columns)} columns expected)"
            )
        raw_values = values.to_numpy()
    else:
        try:
            raw_values = np.asarray(values)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{modality} must be a rectangular numeric array.") from exc
        if raw_values.ndim == 1:
            raw_values = raw_values.reshape(1, -1)
        if raw_values.ndim != 2 or raw_values.shape[0] != 1:
            raise ValueError(
                f"{modality} must be a one-dimensional vector or a single-row matrix"
            )

    if raw_values.shape[1] != len(feature_columns):
        raise ValueError(
            f"{modality} requires {len(feature_columns)} features in the saved order; "
            f"received {raw_values.shape[1]}"
        )
    if _contains_non_numeric_scalars(raw_values):
        raise ValueError(
            f"{modality} features must be real numeric values, not text, temporal, "
            "or boolean"
        )
    try:
        numeric_values = raw_values.astype(np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{modality} features must all be numeric") from exc
    except OverflowError as exc:
        raise ValueError(f"{modality} features must contain finite numeric values") from exc
    if not np.isfinite(numeric_values).all():
        raise ValueError(f"{modality} features must not contain NaN or infinite values")
    return pd.DataFrame(numeric_values, columns=feature_columns)


def _validated_transformation(
    values: Any,
    modality: str,
    expected_features: int,
) -> np.ndarray:
    if _has_masked_values(values):
        raise ValueError(
            f"{modality} preprocessing must not return masked transformed feature values."
        )
    try:
        transformed = np.asarray(values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            f"{modality} preprocessing must return a rectangular transformed feature array."
        ) from exc
    if transformed.shape != (1, expected_features):
        raise ValueError(
            f"{modality} transformed feature shape must be "
            f"(1, {expected_features}); received {transformed.shape}."
        )
    if _contains_non_numeric_scalars(transformed):
        raise ValueError(
            f"{modality} preprocessing returned non-numeric transformed "
            "features (text, temporal, boolean, or complex values)."
        )
    try:
        numeric_values = transformed.astype(np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{modality} preprocessing returned non-numeric transformed features."
        ) from exc
    except OverflowError as exc:
        raise ValueError(
            f"{modality} preprocessing returned non-finite transformed features."
        ) from exc
    if not np.isfinite(numeric_values).all():
        raise ValueError(
            f"{modality} preprocessing returned non-finite transformed features."
        )
    return numeric_values


def predict_sample(
    color_features: Any = None,
    ftir_features: Any = None,
    image_features: Any = None,
    *,
    model_path: str | Path | None = None,
) -> dict[str, Any]:
    """Predict one sample using only modalities required by the selected model.

    Vectors must follow the feature order recorded in the model metadata. Image
    inputs are precomputed 1,280-dimensional EfficientNet-B0 embeddings.
    """
    try:
        path = (
            Path(model_path).resolve()
            if model_path is not None
            else DEFAULT_MODEL_PATH
        )
    except OSError as exc:
        raise ValueError("Could not resolve FoodSure model artifact path.") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid FoodSure model artifact path.") from exc
    try:
        path.stat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"FoodSure model artifact not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not access FoodSure model artifact: {path}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid FoodSure model artifact path: {path}") from exc
    try:
        model_is_file = path.is_file()
    except OSError as exc:
        raise ValueError(f"Could not inspect FoodSure model artifact: {path}") from exc
    if not model_is_file:
        raise ValueError(f"FoodSure model artifact path must be a file: {path}")
    metadata_path = path.with_name(f"{path.stem}_metadata.json")
    try:
        metadata_exists = metadata_path.exists()
    except OSError as exc:
        raise ValueError(
            f"Could not inspect FoodSure model metadata sidecar: {metadata_path}"
        ) from exc
    if metadata_exists:
        try:
            metadata_is_file = metadata_path.is_file()
        except OSError as exc:
            raise ValueError(
                f"Could not inspect FoodSure model metadata sidecar: {metadata_path}"
            ) from exc
    else:
        metadata_is_file = True
    if not metadata_is_file:
        raise ValueError(f"FoodSure model metadata sidecar path must be a file: {metadata_path}")
    try:
        metadata_digest = _sha256_file(metadata_path)
    except FileNotFoundError:
        metadata_digest = ""
    bundle = _load_cached_model(
        str(path),
        _sha256_file(path),
        metadata_digest,
    )
    supplied = {
        "Color": color_features,
        "FTIR": ftir_features,
        "Image": image_features,
    }

    validated: dict[str, pd.DataFrame] = {}
    for modality, values in supplied.items():
        columns = bundle["feature_columns"].get(modality)
        if values is not None and columns is not None:
            row = _validated_row(values, modality, columns)
            if row is not None:
                validated[modality] = row

    configuration = bundle["modality_configuration"]
    missing = [name for name in configuration if name not in validated]
    if missing:
        raise ValueError(f"Missing required model input modality/modalities: {', '.join(missing)}")

    representations = []
    for modality in configuration:
        preprocessor = bundle["preprocessors"][modality]
        transformed = preprocessor["scaler"].transform(validated[modality])
        transformed = _validated_transformation(
            transformed,
            modality,
            len(bundle["feature_columns"][modality]),
        )
        if preprocessor.get("pca") is not None:
            transformed = preprocessor["pca"].transform(transformed)
            transformed = _validated_transformation(
                transformed,
                modality,
                int(preprocessor["pca"].n_components_),
            )
        representations.append(transformed)
    fused = np.concatenate(representations, axis=1)

    classifier_output = bundle["classifier"].predict(fused)
    if _has_masked_values(classifier_output):
        raise ValueError(
            "FoodSure classifier must not return a masked class prediction."
        )
    try:
        classifier_prediction = np.asarray(classifier_output)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "FoodSure classifier must return exactly one class for one input sample."
        ) from exc
    if classifier_prediction.shape != (1,):
        raise ValueError(
            "FoodSure classifier must return exactly one class for one input sample."
        )
    predicted_class = classifier_prediction[0]
    if isinstance(predicted_class, (bool, np.bool_)) or not isinstance(
        predicted_class, (int, float, np.integer, np.floating)
    ):
        raise ValueError("FoodSure classifier returned a non-numeric class label.")
    try:
        predicted_class_value = float(predicted_class)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(
            f"FoodSure classifier returned unsupported class label: {predicted_class!r}"
        ) from exc
    if not math.isfinite(predicted_class_value) or predicted_class_value not in bundle[
        "class_labels"
    ]:
        raise ValueError(
            f"FoodSure classifier returned unsupported class label: {predicted_class!r}"
        )
    regression_output = bundle["regressor"].predict(fused)
    if _has_masked_values(regression_output):
        raise ValueError(
            "FoodSure regressor must not return a masked regression estimate."
        )
    try:
        regression_prediction = np.asarray(regression_output)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "FoodSure regressor must return exactly one estimate for one input sample."
        ) from exc
    if regression_prediction.shape != (1,):
        raise ValueError(
            "FoodSure regressor must return exactly one estimate for one input sample."
        )
    predicted_value = regression_prediction[0]
    if isinstance(predicted_value, (bool, np.bool_)) or not isinstance(
        predicted_value, (int, float, np.integer, np.floating)
    ):
        raise ValueError("FoodSure regressor returned a non-numeric estimate.")
    try:
        predicted_percentage = float(predicted_value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(
            "FoodSure regressor returned a non-finite estimate."
        ) from exc
    if not math.isfinite(predicted_percentage):
        raise ValueError("FoodSure regressor returned a non-finite estimate.")

    output: dict[str, Any] = {
        "predicted_class": f"{predicted_class_value:g}%",
        "predicted_percentage": predicted_percentage,
        "modality_configuration": list(configuration),
        "model_version": bundle["model_version"],
        "probabilities": None,
        "probability_note": "Not reported; classifier probabilities were not calibrated.",
    }
    output["regression_note"] = (
        "Unconstrained continuous research estimate; it may fall outside observed target levels."
    )
    return output
