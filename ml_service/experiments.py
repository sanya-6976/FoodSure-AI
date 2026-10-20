"""Leakage-safe classification and regression workflow for Notebook 9."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

RAW_SPECS = {
    "Color": (Path("Color Measurement") / "Hunter_Lab_colorimeter.csv", "Sample_ID"),
    "FTIR": (Path("FTIR Spectroscopy") / "FTIR_Data.csv", "Sample ID"),
    "Image": (
        Path("Image")
        / "EfficientNetB0_Image_Features"
        / "EfficientNetB0_Image_Features.csv",
        "Sample_ID",
    ),
}
EXPECTED_FEATURES = {"Color": 46, "FTIR": 2522, "Image": 1280}
CONFIGURATIONS = [
    ("Color", ("Color",)),
    ("FTIR", ("FTIR",)),
    ("Image", ("Image",)),
    ("Color + FTIR", ("Color", "FTIR")),
    ("Color + Image", ("Color", "Image")),
    ("FTIR + Image", ("FTIR", "Image")),
    ("Color + FTIR + Image", ("Color", "FTIR", "Image")),
]
CLASSIFIERS = ("Logistic Regression", "SVM (RBF)", "Random Forest")


def _locate_raw_root(project_root: Path) -> Path:
    candidates = (
        project_root / "dataset",
        project_root.parent / "Multimodal Dataset for Turmeric Adulteration Detec",
    )
    for candidate in candidates:
        if all((candidate / relative_path).is_file() for relative_path, _ in RAW_SPECS.values()):
            return candidate
    raise FileNotFoundError(
        f"Could not locate all raw modality CSVs under {[str(path) for path in candidates]}"
    )


def _load_data(project_root: Path) -> dict[str, Any]:
    notebook_dir = project_root / "notebook"
    raw_root = _locate_raw_root(project_root)
    train_ids = pd.read_csv(notebook_dir / "train_sample_ids.csv")["Sample_ID"].astype(str).str.strip()
    test_ids = pd.read_csv(notebook_dir / "test_sample_ids.csv")["Sample_ID"].astype(str).str.strip()
    if len(train_ids) != 280 or len(test_ids) != 70:
        raise ValueError(f"Expected the preserved 280/70 split, found {len(train_ids)}/{len(test_ids)}")
    if train_ids.nunique() != 280 or test_ids.nunique() != 70 or set(train_ids) & set(test_ids):
        raise ValueError("The saved split IDs contain duplicates or overlap")

    features: dict[str, pd.DataFrame] = {}
    targets: dict[str, pd.Series] = {}
    paths: dict[str, Path] = {}
    for modality, (relative_path, id_column) in RAW_SPECS.items():
        csv_path = raw_root / relative_path
        table = pd.read_csv(csv_path)
        if id_column not in table.columns or "Target" not in table.columns:
            raise ValueError(f"Missing required ID or Target column in {csv_path}")
        table[id_column] = table[id_column].astype(str).str.strip()
        if table[id_column].duplicated().any():
            raise ValueError(f"Duplicate sample IDs in {csv_path}")
        table = table.set_index(id_column)
        target = pd.to_numeric(
            table["Target"].astype(str).str.replace("%", "", regex=False), errors="raise"
        )
        x = table.drop(columns=["Target"]).dropna(axis=1, how="all")
        x = x.apply(pd.to_numeric, errors="raise")
        if x.isna().any().any() or not np.isfinite(x.to_numpy(dtype=float)).all():
            raise ValueError(f"Missing or non-finite features in {csv_path}")
        if x.shape[1] != EXPECTED_FEATURES[modality]:
            raise ValueError(
                f"{modality}: expected {EXPECTED_FEATURES[modality]} features, found {x.shape[1]}"
            )
        features[modality] = x
        targets[modality] = target
        paths[modality] = csv_path

    reference = targets["Color"]
    expected_ids = set(train_ids) | set(test_ids)
    if set(reference.index) != expected_ids:
        raise ValueError("The saved train/test IDs do not partition the raw dataset")
    for modality in ("FTIR", "Image"):
        if set(targets[modality].index) != expected_ids:
            raise ValueError(f"{modality} IDs differ from Color IDs")
        aligned = targets[modality].reindex(reference.index)
        if not np.array_equal(aligned.to_numpy(dtype=float), reference.to_numpy(dtype=float)):
            raise ValueError(f"{modality} targets disagree with Color after joining by sample ID")

    y_train = reference.loc[train_ids.tolist()].reset_index(drop=True)
    y_test = reference.loc[test_ids.tolist()].reset_index(drop=True)
    if set(y_train.unique()) != {0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 9.0}:
        raise ValueError(f"Unexpected training classes: {sorted(y_train.unique())}")
    if not (y_train.value_counts().sort_index() == 40).all():
        raise ValueError("Training set does not contain 40 samples per class")
    if not (y_test.value_counts().sort_index() == 10).all():
        raise ValueError("Test set does not contain 10 samples per class")

    preprocessed = project_root / "preprocessed"
    saved_y_train = pd.to_numeric(
        pd.read_csv(preprocessed / "y_train.csv").iloc[:, 0].astype(str).str.replace("%", "", regex=False)
    )
    saved_y_test = pd.to_numeric(
        pd.read_csv(preprocessed / "y_test.csv").iloc[:, 0].astype(str).str.replace("%", "", regex=False)
    )
    train_export = reference.loc[reference.index.isin(set(train_ids))].reset_index(drop=True)
    test_export = reference.loc[reference.index.isin(set(test_ids))].reset_index(drop=True)
    if not np.array_equal(saved_y_train.to_numpy(dtype=float), train_export.to_numpy(dtype=float)):
        raise ValueError("Saved y_train does not match original-row-order membership export")
    if not np.array_equal(saved_y_test.to_numpy(dtype=float), test_export.to_numpy(dtype=float)):
        raise ValueError("Saved y_test does not match original-row-order membership export")

    return {
        "raw_root": raw_root,
        "paths": paths,
        "features": features,
        "train_ids": train_ids,
        "test_ids": test_ids,
        "X_train": {name: x.loc[train_ids.tolist()].copy() for name, x in features.items()},
        "X_test": {name: x.loc[test_ids.tolist()].copy() for name, x in features.items()},
        "y_train": y_train,
        "y_test": y_test,
        "saved_train_mismatches": int((saved_y_train.to_numpy() != y_train.to_numpy()).sum()),
        "saved_test_mismatches": int((saved_y_test.to_numpy() != y_test.to_numpy()).sum()),
    }


def _new_classifier(name: str) -> Any:
    if name == "Logistic Regression":
        return LogisticRegression(max_iter=2000, random_state=42)
    if name == "SVM (RBF)":
        return SVC(kernel="rbf", C=1.0, gamma="scale")
    return RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=1)


def _new_regressor(name: str) -> Any:
    if name == "Ridge Regression":
        return Ridge(alpha=1.0)
    return RandomForestRegressor(
        n_estimators=300, random_state=42, min_samples_leaf=2, n_jobs=1
    )


def _metric_values(actual: Any, predicted: Any) -> dict[str, float]:
    return {
        "Accuracy": float(accuracy_score(actual, predicted)),
        "Macro Precision": float(precision_score(actual, predicted, average="macro", zero_division=0)),
        "Macro Recall": float(recall_score(actual, predicted, average="macro", zero_division=0)),
        "Macro F1": float(f1_score(actual, predicted, average="macro", zero_division=0)),
    }


def run_workflow(project_root: str | Path) -> dict[str, Any]:
    """Execute Notebook 9 experiments and save validation/model artifacts."""
    root = Path(project_root).resolve()
    data = _load_data(root)
    results_dir = root / "results" / "notebook_09"
    model_dir = root / "models"
    results_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    x_train = data["X_train"]
    x_test = data["X_test"]
    y_train = data["y_train"]
    y_test = data["y_test"]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    fold_cache: list[dict[str, Any]] = []
    preprocessing_rows: list[dict[str, Any]] = []
    with threadpool_limits(limits=2):
        for fold_number, (fit_idx, valid_idx) in enumerate(cv.split(x_train["Color"], y_train), start=1):
            train_repr: dict[str, np.ndarray] = {}
            valid_repr: dict[str, np.ndarray] = {}
            preprocessing_seconds: dict[str, float] = {}
            pca_components: dict[str, int | None] = {}
            for modality in RAW_SPECS:
                started = time.perf_counter()
                scaler = StandardScaler()
                train_scaled = scaler.fit_transform(x_train[modality].iloc[fit_idx])
                valid_scaled = scaler.transform(x_train[modality].iloc[valid_idx])
                pca = None
                component_count = None
                explained_variance = None
                if modality in {"FTIR", "Image"}:
                    pca = PCA(n_components=0.90, random_state=42)
                    train_repr[modality] = pca.fit_transform(train_scaled)
                    valid_repr[modality] = pca.transform(valid_scaled)
                    component_count = int(pca.n_components_)
                    explained_variance = float(pca.explained_variance_ratio_.sum())
                else:
                    train_repr[modality] = train_scaled
                    valid_repr[modality] = valid_scaled
                elapsed = time.perf_counter() - started
                preprocessing_seconds[modality] = elapsed
                pca_components[modality] = component_count
                preprocessing_rows.append({
                    "Fold": fold_number,
                    "Modality": modality,
                    "Input Features": x_train[modality].shape[1],
                    "PCA Components": component_count,
                    "PCA Explained Variance": explained_variance,
                    "Fit And Transform Seconds": elapsed,
                    "Fit Rows": len(fit_idx),
                    "Validation Rows": len(valid_idx),
                })
            fold_cache.append({
                "fold": fold_number, "fit_idx": fit_idx, "valid_idx": valid_idx,
                "train_repr": train_repr, "valid_repr": valid_repr,
                "preprocessing_seconds": preprocessing_seconds,
                "pca_components": pca_components,
            })

    cv_rows: list[dict[str, Any]] = []
    oof_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    with threadpool_limits(limits=2):
        for config_name, modalities in CONFIGURATIONS:
            for model_name in CLASSIFIERS:
                for cache in fold_cache:
                    started = time.perf_counter()
                    train_matrix = np.concatenate([cache["train_repr"][m] for m in modalities], axis=1)
                    valid_matrix = np.concatenate([cache["valid_repr"][m] for m in modalities], axis=1)
                    estimator = _new_classifier(model_name)
                    estimator.fit(train_matrix, y_train.iloc[cache["fit_idx"]])
                    predicted = estimator.predict(valid_matrix)
                    classifier_seconds = time.perf_counter() - started
                    actual = y_train.iloc[cache["valid_idx"]]
                    row = {
                        "Modalities": config_name, "Model": model_name, "Fold": cache["fold"],
                        "Fit Samples": len(cache["fit_idx"]), "Validation Samples": len(cache["valid_idx"]),
                        "Classifier Fit/Predict Seconds": classifier_seconds,
                        "Preprocessing Seconds": sum(cache["preprocessing_seconds"][m] for m in modalities),
                        "PCA Components FTIR": cache["pca_components"]["FTIR"] if "FTIR" in modalities else np.nan,
                        "PCA Components Image": cache["pca_components"]["Image"] if "Image" in modalities else np.nan,
                    }
                    row.update(_metric_values(actual, predicted))
                    cv_rows.append(row)
                    runtime_rows.append({
                        "Modalities": config_name, "Model": model_name, "Fold": cache["fold"],
                        "Classifier Fit/Predict Seconds": classifier_seconds,
                        "Included-Modality Preprocessing Seconds": row["Preprocessing Seconds"],
                        "Total Pipeline Seconds": classifier_seconds + row["Preprocessing Seconds"],
                    })
                    for sample_id, true, prediction in zip(data["train_ids"].iloc[cache["valid_idx"]], actual, predicted):
                        oof_rows.append({
                            "Modalities": config_name, "Model": model_name, "Sample_ID": sample_id,
                            "Actual": true, "Predicted": prediction, "Fold": cache["fold"],
                        })
    cv_folds = pd.DataFrame(cv_rows)
    runtime = pd.DataFrame(runtime_rows)
    oof = pd.DataFrame(oof_rows)
    prep_details = pd.DataFrame(preprocessing_rows)
    metric_names = ("Accuracy", "Macro Precision", "Macro Recall", "Macro F1")
    cv_summary_rows = []
    for (config_name, model_name), group in cv_folds.groupby(["Modalities", "Model"], sort=False):
        row: dict[str, Any] = {"Modalities": config_name, "Model": model_name}
        for metric in metric_names:
            row[f"{metric} Mean"] = group[metric].mean()
            row[f"{metric} Std"] = group[metric].std(ddof=0)
        timing = runtime[(runtime["Modalities"] == config_name) & (runtime["Model"] == model_name)]
        row["Classifier Fit/Predict Seconds"] = timing["Classifier Fit/Predict Seconds"].sum()
        row["Preprocessing Seconds (shared fold cache)"] = timing["Included-Modality Preprocessing Seconds"].sum()
        row["Total Pipeline Seconds (measured stages)"] = timing["Total Pipeline Seconds"].sum()
        modalities = dict(CONFIGURATIONS)[config_name]
        for modality in ("FTIR", "Image"):
            row[f"PCA Components {modality} Mean"] = (
                prep_details.loc[prep_details["Modality"] == modality, "PCA Components"].mean()
                if modality in modalities else np.nan
            )
        cv_summary_rows.append(row)
    cv_summary = pd.DataFrame(cv_summary_rows)
    if len(cv_folds) != 105 or len(oof) != 7 * 3 * len(y_train):
        raise AssertionError("The requested 7 x 3 x 5-fold CV evaluation is incomplete")

    model_order = {"Logistic Regression": 0, "SVM (RBF)": 1, "Random Forest": 2}
    selection = cv_summary.copy()
    selection["_modality_count"] = selection["Modalities"].str.split(" + ").str.len()
    selection["_model_priority"] = selection["Model"].map(model_order)
    selection = selection.sort_values(
        ["Macro F1 Mean", "Macro F1 Std", "Accuracy Mean", "Accuracy Std", "_modality_count", "_model_priority"],
        ascending=[False, True, False, True, True, True], kind="stable",
    )
    chosen = selection.iloc[0]
    singles = cv_summary[~cv_summary["Modalities"].str.contains(" + ", regex=False)]
    fusions = cv_summary[cv_summary["Modalities"].str.contains(" + ", regex=False)]
    best_individual = singles.sort_values(
        ["Macro F1 Mean", "Macro F1 Std", "Accuracy Mean", "Accuracy Std"],
        ascending=[False, True, False, True], kind="stable",
    ).iloc[0]
    best_fusion = fusions.sort_values(
        ["Macro F1 Mean", "Macro F1 Std", "Accuracy Mean", "Accuracy Std"],
        ascending=[False, True, False, True], kind="stable",
    ).iloc[0]
    fusion_improves = bool(best_fusion["Macro F1 Mean"] > best_individual["Macro F1 Mean"] + 1e-12)

    regression_configs = list(dict.fromkeys([
        best_individual["Modalities"], best_fusion["Modalities"], chosen["Modalities"]
    ]))
    regression_rows: list[dict[str, Any]] = []
    regression_oof_rows: list[dict[str, Any]] = []
    with threadpool_limits(limits=2):
        for config_name in regression_configs:
            modalities = dict(CONFIGURATIONS)[config_name]
            for model_name in ("Ridge Regression", "Random Forest Regressor"):
                for cache in fold_cache:
                    train_matrix = np.concatenate([cache["train_repr"][m] for m in modalities], axis=1)
                    valid_matrix = np.concatenate([cache["valid_repr"][m] for m in modalities], axis=1)
                    estimator = _new_regressor(model_name)
                    started = time.perf_counter()
                    estimator.fit(train_matrix, y_train.iloc[cache["fit_idx"]])
                    prediction = estimator.predict(valid_matrix)
                    elapsed = time.perf_counter() - started
                    actual = y_train.iloc[cache["valid_idx"]].to_numpy(dtype=float)
                    regression_rows.append({
                        "Modalities": config_name, "Model": model_name, "Fold": cache["fold"],
                        "MAE": mean_absolute_error(actual, prediction),
                        "RMSE": np.sqrt(mean_squared_error(actual, prediction)),
                        "R2": r2_score(actual, prediction), "Fit/Predict Seconds": elapsed,
                        "PCA Components FTIR": cache["pca_components"]["FTIR"] if "FTIR" in modalities else np.nan,
                        "PCA Components Image": cache["pca_components"]["Image"] if "Image" in modalities else np.nan,
                    })
                    for sample_id, true, pred in zip(data["train_ids"].iloc[cache["valid_idx"]], actual, prediction):
                        regression_oof_rows.append({
                            "Modalities": config_name, "Model": model_name, "Sample_ID": sample_id,
                            "Actual Percentage": true, "Predicted Percentage": pred, "Fold": cache["fold"],
                        })
    regression_folds = pd.DataFrame(regression_rows)
    regression_oof = pd.DataFrame(regression_oof_rows)
    regression_summary_rows = []
    for (config_name, model_name), group in regression_folds.groupby(["Modalities", "Model"], sort=False):
        row = {"Modalities": config_name, "Model": model_name}
        for metric in ("MAE", "RMSE", "R2"):
            row[f"{metric} Mean"] = group[metric].mean()
            row[f"{metric} Std"] = group[metric].std(ddof=0)
        row["Fit/Predict Seconds"] = group["Fit/Predict Seconds"].sum()
        regression_summary_rows.append(row)
    regression_summary = pd.DataFrame(regression_summary_rows)
    selected_regression = regression_summary[
        regression_summary["Modalities"] == chosen["Modalities"]
    ].sort_values(["MAE Mean", "MAE Std", "RMSE Mean"], ascending=True, kind="stable").iloc[0]

    selected_modalities = dict(CONFIGURATIONS)[chosen["Modalities"]]
    preprocessors: dict[str, dict[str, Any]] = {}
    train_representations: dict[str, np.ndarray] = {}
    test_representations: dict[str, np.ndarray] = {}
    pca_details: dict[str, dict[str, Any]] = {}
    with threadpool_limits(limits=2):
        for modality in selected_modalities:
            scaler = StandardScaler()
            train_scaled = scaler.fit_transform(x_train[modality])
            test_scaled = scaler.transform(x_test[modality])
            pca = None
            if modality in {"FTIR", "Image"}:
                pca = PCA(n_components=0.90, random_state=42)
                train_representations[modality] = pca.fit_transform(train_scaled)
                test_representations[modality] = pca.transform(test_scaled)
                pca_details[modality] = {
                    "components": int(pca.n_components_),
                    "explained_variance": float(pca.explained_variance_ratio_.sum()),
                }
            else:
                train_representations[modality] = train_scaled
                test_representations[modality] = test_scaled
                pca_details[modality] = {"components": None, "explained_variance": None}
            preprocessors[modality] = {"scaler": scaler, "pca": pca}
        train_matrix = np.concatenate([train_representations[m] for m in selected_modalities], axis=1)
        test_matrix = np.concatenate([test_representations[m] for m in selected_modalities], axis=1)
        classifier = _new_classifier(chosen["Model"]).fit(train_matrix, y_train)
        regression_model = _new_regressor(selected_regression["Model"]).fit(train_matrix, y_train)
        heldout_class_prediction = classifier.predict(test_matrix)
        heldout_regression_prediction = regression_model.predict(test_matrix)

    heldout_class_metrics = _metric_values(y_test, heldout_class_prediction)
    heldout_regression_metrics = {
        "MAE": float(mean_absolute_error(y_test, heldout_regression_prediction)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, heldout_regression_prediction))),
        "R2": float(r2_score(y_test, heldout_regression_prediction)),
    }
    heldout_summary = {
        "Modalities": chosen["Modalities"], "Classification Model": chosen["Model"],
        **{f"Test {key}": value for key, value in heldout_class_metrics.items()},
        "Regression Model": selected_regression["Model"],
        **{f"Regression Test {key}": value for key, value in heldout_regression_metrics.items()},
        "CV Accuracy Mean": float(chosen["Accuracy Mean"]),
        "CV Accuracy Std": float(chosen["Accuracy Std"]),
        "CV Macro F1 Mean": float(chosen["Macro F1 Mean"]),
        "CV Macro F1 Std": float(chosen["Macro F1 Std"]),
    }
    heldout_results = pd.DataFrame([heldout_summary])
    labels = sorted(y_train.unique().tolist())
    label_names = [f"{value:g}%" for value in labels]
    report = pd.DataFrame(classification_report(
        y_test, heldout_class_prediction, labels=labels, target_names=label_names,
        output_dict=True, zero_division=0,
    )).T
    classwise_oof = pd.DataFrame(classification_report(
        oof.loc[(oof["Modalities"] == chosen["Modalities"]) & (oof["Model"] == chosen["Model"]), "Actual"],
        oof.loc[(oof["Modalities"] == chosen["Modalities"]) & (oof["Model"] == chosen["Model"]), "Predicted"],
        labels=labels, target_names=label_names, output_dict=True, zero_division=0,
    )).T
    selected_oof_rows = oof[(oof["Modalities"] == chosen["Modalities"]) & (oof["Model"] == chosen["Model"])]
    heldout_confusion = confusion_matrix(y_test, heldout_class_prediction, labels=labels)

    cv_plot_path = results_dir / "fusion_cv_comparison.png"
    ordered = cv_summary.sort_values(["Modalities", "Model"])
    positions = np.arange(len(ordered))
    fig, axes = plt.subplots(1, 2, figsize=(15, 10), sharey=True)
    names = [f"{row.Modalities} / {row.Model}" for row in ordered.itertuples()]
    for axis, metric in zip(axes, ("Accuracy", "Macro F1")):
        axis.barh(positions, ordered[f"{metric} Mean"], xerr=ordered[f"{metric} Std"], capsize=2)
        axis.set_yticks(positions, names)
        axis.invert_yaxis()
        axis.set_xlim(0, 1.05)
        axis.set_xlabel("Five-fold mean +/- standard deviation")
        axis.set_title(metric)
        axis.grid(axis="x", alpha=0.25)
    fig.suptitle("Classification comparison (training CV only)")
    fig.tight_layout()
    fig.savefig(cv_plot_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    confusion_path = results_dir / "fusion_confusion_matrix.png"
    fig, axis = plt.subplots(figsize=(8, 6))
    image = axis.imshow(heldout_confusion, cmap="Blues")
    axis.set_xticks(np.arange(len(labels)), label_names)
    axis.set_yticks(np.arange(len(labels)), label_names)
    axis.set_xlabel("Predicted adulteration level")
    axis.set_ylabel("Actual adulteration level")
    axis.set_title(f"Held-out test: {chosen['Modalities']} / {chosen['Model']}")
    for i in range(len(labels)):
        for j in range(len(labels)):
            axis.text(j, i, str(heldout_confusion[i, j]), ha="center", va="center")
    fig.colorbar(image, ax=axis, label="Sample count")
    fig.tight_layout()
    fig.savefig(confusion_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    cv_summary.to_csv(results_dir / "fusion_cv_results.csv", index=False)
    cv_folds.to_csv(results_dir / "fusion_cv_fold_results.csv", index=False)
    runtime.to_csv(results_dir / "fusion_cv_runtime.csv", index=False)
    prep_details.to_csv(results_dir / "fusion_fold_preprocessing.csv", index=False)
    oof.to_csv(results_dir / "fusion_oof_predictions.csv", index=False)
    regression_summary.to_csv(results_dir / "regression_results.csv", index=False)
    regression_folds.to_csv(results_dir / "regression_fold_results.csv", index=False)
    regression_oof.to_csv(results_dir / "regression_oof_predictions.csv", index=False)
    heldout_results.to_csv(results_dir / "fusion_holdout_results.csv", index=False)
    report.to_csv(results_dir / "fusion_classification_report.csv")
    classwise_oof.to_csv(results_dir / "fusion_classwise_oof_report.csv")
    pd.DataFrame(heldout_confusion, index=label_names, columns=label_names).to_csv(
        results_dir / "fusion_confusion_matrix.csv"
    )
    pd.DataFrame({
        "Sample_ID": data["test_ids"],
        "Actual Class": y_test,
        "Predicted Class": heldout_class_prediction,
        "Actual Percentage": y_test,
        "Predicted Percentage": heldout_regression_prediction,
    }).to_csv(results_dir / "fusion_holdout_predictions.csv", index=False)

    model_version = "foodsure-ml-v1"
    train_hash = hashlib.sha256("\n".join(data["train_ids"].tolist()).encode("utf-8")).hexdigest()
    test_hash = hashlib.sha256("\n".join(data["test_ids"].tolist()).encode("utf-8")).hexdigest()
    bundle = {
        "model_version": model_version,
        "modality_configuration": list(selected_modalities),
        "feature_columns": {name: list(frame.columns) for name, frame in data["features"].items()},
        "preprocessors": preprocessors,
        "classifier": classifier,
        "regressor": regression_model,
        "class_labels": labels,
    }
    model_path = model_dir / "foodsure_multimodal_v1.joblib"
    joblib.dump(bundle, model_path)
    package_versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pandas", "scikit-learn", "joblib")
    }
    metadata = {
        "model_version": model_version,
        "modality_configuration": list(selected_modalities),
        "classification_model": chosen["Model"],
        "regression_model": selected_regression["Model"],
        "feature_order": {name: list(frame.columns) for name, frame in data["features"].items()},
        "pca_components_and_explained_variance": pca_details,
        "class_labels_percentage": labels,
        "training_split": {
            "training_sample_count": len(data["train_ids"]),
            "heldout_sample_count": len(data["test_ids"]),
            "training_ids_sha256_ordered": train_hash,
            "heldout_ids_sha256_ordered": test_hash,
            "cross_validation": "StratifiedKFold(n_splits=5, shuffle=True, random_state=42)",
        },
        "package_versions": package_versions,
        "classification_cv_metrics": {
            metric: {"mean": float(chosen[f"{metric} Mean"]), "std": float(chosen[f"{metric} Std"])}
            for metric in metric_names
        },
        "regression_cv_metrics": {
            metric: {"mean": float(selected_regression[f"{metric} Mean"]), "std": float(selected_regression[f"{metric} Std"])}
            for metric in ("MAE", "RMSE", "R2")
        },
        "heldout_metrics": heldout_summary,
        "probability_calibration": "Not assessed; inference does not return probabilities.",
        "image_input_requirement": "Precomputed EfficientNet-B0 embeddings; raw image extraction is not included.",
        "data_alignment": "Targets joined from raw CSVs by sample ID; saved target CSVs are in original-row membership order.",
    }
    metadata_path = model_dir / "foodsure_multimodal_v1_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    from ml_service.predictor import predict_sample

    sample_id = data["train_ids"].iloc[0]
    sample_inputs = {
        "Color": data["features"]["Color"].loc[sample_id].to_numpy(dtype=float),
        "FTIR": data["features"]["FTIR"].loc[sample_id].to_numpy(dtype=float),
        "Image": data["features"]["Image"].loc[sample_id].to_numpy(dtype=float),
    }
    valid_prediction = predict_sample(
        color_features=sample_inputs["Color"],
        ftir_features=sample_inputs["FTIR"],
        image_features=sample_inputs["Image"],
    )
    invalid_input_results = []
    required = selected_modalities[0]
    argument_name = {"Color": "color_features", "FTIR": "ftir_features", "Image": "image_features"}[required]
    malformed = {argument_name: np.zeros(len(sample_inputs[required]) - 1)}
    for inputs, expected in (({}, "Missing required model input"), (malformed, "requires")):
        try:
            predict_sample(**inputs)
        except ValueError as exc:
            if expected not in str(exc):
                raise AssertionError(f"Unexpected inference input validation error: {exc}") from exc
            invalid_input_results.append(str(exc))
        else:
            raise AssertionError("Invalid inference input was not rejected")

    best_fusion_improves = fusion_improves
    conclusion = (
        f"CV selected {chosen['Modalities']} / {chosen['Model']} (Macro F1 "
        f"{chosen['Macro F1 Mean']:.4f} +/- {chosen['Macro F1 Std']:.4f}; accuracy "
        f"{chosen['Accuracy Mean']:.4f} +/- {chosen['Accuracy Std']:.4f}). Best individual CV "
        f"Macro F1 was {best_individual['Macro F1 Mean']:.4f} for {best_individual['Modalities']} / "
        f"{best_individual['Model']}; best fusion CV Macro F1 was {best_fusion['Macro F1 Mean']:.4f} "
        f"for {best_fusion['Modalities']} / {best_fusion['Model']}. Fusion improves: "
        f"{best_fusion_improves}. Held-out Macro F1 was {heldout_class_metrics['Macro F1']:.4f}. "
        f"Selected regression was {selected_regression['Model']} (CV MAE "
        f"{selected_regression['MAE Mean']:.4f} +/- {selected_regression['MAE Std']:.4f}; test MAE "
        f"{heldout_regression_metrics['MAE']:.4f}). This controlled dataset requires independent "
        "external validation."
    )
    (results_dir / "conclusions.txt").write_text(conclusion + "\n", encoding="utf-8")

    return {
        "data": data,
        "cv_summary": cv_summary,
        "cv_folds": cv_folds,
        "cv_runtime": runtime,
        "preprocessing_details": prep_details,
        "oof_predictions": oof,
        "regression_summary": regression_summary,
        "regression_folds": regression_folds,
        "regression_oof": regression_oof,
        "heldout_results": heldout_results,
        "heldout_report": report,
        "heldout_classwise_oof": classwise_oof,
        "heldout_confusion": heldout_confusion,
        "selected_classifier": chosen,
        "best_individual": best_individual,
        "best_fusion": best_fusion,
        "fusion_improves": best_fusion_improves,
        "selected_regression": selected_regression,
        "valid_prediction": valid_prediction,
        "invalid_input_results": invalid_input_results,
        "conclusion": conclusion,
        "model_path": model_path,
        "metadata_path": metadata_path,
        "results_dir": results_dir,
        "cv_plot_path": cv_plot_path,
        "confusion_plot_path": confusion_path,
    }
