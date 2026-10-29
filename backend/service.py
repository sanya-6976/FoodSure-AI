"""Unified backend service layer for FoodSure AI.

Orchestrates data loading, validation, ML inference, Gemini report generation,
and history persistence.
"""

from __future__ import annotations

import io
import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ai_layer.pipeline import run_pipeline
from ai_layer.explanation_engine import build_enriched_evidence, generate_structured_explanation
from backend.history import save_analysis
from backend.notifications import add_notification
from backend.settings import get_user_settings
from backend.schemas import (
    AnalysisResult,
    PredictionOutput,
    SampleValidationResult,
)
from ml_service.experiments import _load_data
from ml_service.predictor import DEFAULT_MODEL_PATH

LOGGER = logging.getLogger("foodsure.service")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = DEFAULT_MODEL_PATH.with_name(
    f"{DEFAULT_MODEL_PATH.stem}_metadata.json"
)


def load_resources() -> dict[str, Any]:
    """Check and return status of model artifacts, metadata, and dataset."""
    status = {
        "model_available": DEFAULT_MODEL_PATH.is_file(),
        "metadata_available": METADATA_PATH.is_file(),
        "dataset_available": False,
        "feature_count": 0,
        "classes": [],
        "model_version": "unknown",
        "supported_modalities": ["FTIR"],
    }

    if status["metadata_available"]:
        try:
            metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            status["model_version"] = metadata.get("model_version", "v1")
            status["classes"] = [f"{label:g}%" for label in metadata.get("class_labels_percentage", [])]
            status["feature_count"] = len(metadata.get("feature_order", {}).get("FTIR", []))
            status["supported_modalities"] = metadata.get("modality_configuration", ["FTIR"])
        except Exception as exc:
            LOGGER.warning("Could not read metadata sidecar: %s", exc)

    try:
        raw_candidates = (
            PROJECT_ROOT / "dataset",
            PROJECT_ROOT.parent / "Multimodal Dataset for Turmeric Adulteration Detec",
        )
        status["dataset_available"] = any(c.is_dir() for c in raw_candidates)
    except Exception:
        status["dataset_available"] = False

    return status


def get_metadata() -> dict[str, Any]:
    """Load model metadata JSON safely."""
    if not METADATA_PATH.is_file():
        raise FileNotFoundError("The saved FoodSure model metadata is not installed.")
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def load_raw_dataset() -> dict[str, Any]:
    """Load research dataset using ml_service loader."""
    return _load_data(PROJECT_ROOT)


def get_dataset_sample_ids() -> list[str]:
    """Return all available sample IDs from the research dataset."""
    try:
        data = load_raw_dataset()
        return data["features"]["FTIR"].index.astype(str).tolist()
    except Exception as exc:
        LOGGER.warning("Could not load dataset sample IDs: %s", exc)
        return []


def load_dataset_sample(
    sample_id: str,
) -> tuple[pd.DataFrame, float, dict[str, Any]]:
    """Load features and ground truth for an existing dataset sample ID."""
    metadata = get_metadata()
    feature_columns = metadata["feature_order"]["FTIR"]
    data = load_raw_dataset()

    features_df = data["features"]["FTIR"]
    if sample_id not in features_df.index:
        raise ValueError(f"Sample ID '{sample_id}' not found in dataset.")

    row = features_df.loc[[sample_id], feature_columns]
    target_by_id = dict(zip(data["train_ids"], data["y_train"]))
    target_by_id.update(dict(zip(data["test_ids"], data["y_test"])))
    actual = float(target_by_id[sample_id])

    sample_meta = {
        "sample_id": sample_id,
        "is_train": sample_id in set(data["train_ids"]),
        "actual_level": actual,
    }
    return row.reset_index(drop=True), actual, sample_meta


def validate_uploaded_ftir_csv(file_bytes: bytes) -> tuple[str | None, pd.DataFrame]:
    """Parse and validate uploaded CSV against saved FTIR feature contract."""
    metadata = get_metadata()
    feature_columns = metadata["feature_order"]["FTIR"]

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
        val = table.pop("Sample_ID").iloc[0]
        if pd.notna(val) and str(val).strip():
            sample_id = str(val).strip()
    elif "Sample ID" in table.columns:
        val = table.pop("Sample ID").iloc[0]
        if pd.notna(val) and str(val).strip():
            sample_id = str(val).strip()

    missing = [c for c in feature_columns if c not in table.columns]
    extra = [c for c in table.columns if c not in feature_columns]
    if missing or extra:
        details = []
        if missing:
            details.append(f"{len(missing)} required feature columns are missing")
        if extra:
            details.append(f"{len(extra)} unexpected columns found")
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


def get_spectrum_data(features: pd.DataFrame) -> dict[str, list[float]]:
    """Extract wavenumbers and absorbance values for interactive plotting."""
    try:
        cols = list(features.columns)
        wavenumbers: list[float] = []
        for c in cols:
            # FTIR columns are often wavenumber strings e.g. '3999.5'
            try:
                wavenumbers.append(float(c))
            except ValueError:
                wavenumbers.append(float(len(wavenumbers)))
        absorbance = [float(v) for v in features.iloc[0].values]
        return {"wavenumbers": wavenumbers, "absorbance": absorbance}
    except Exception:
        return {"wavenumbers": [], "absorbance": []}


def run_sample_analysis(
    features: pd.DataFrame,
    sample_id: str | None,
    actual_level: float | None,
    source_label: str,
    user_id: str,
    use_gemini: bool = True,
    depth: str = "detailed",
    sample_meta: dict[str, Any] | None = None,
    explanation_lang: str = "en",
) -> AnalysisResult:
    """Execute complete analysis pipeline, generate AI report, and persist to history."""
    pipeline_res = run_pipeline({"ftir_features": features}, use_llm=False)

    prediction = pipeline_res["prediction"]
    predicted_class = prediction["predicted_class"]
    predicted_percentage = prediction.get("predicted_percentage")
    model_version = pipeline_res.get("model_version", "foodsure-v1")

    try:
        level_val = float(predicted_class.rstrip("%"))
        is_pure = math.isclose(level_val, 0.0)
    except (TypeError, ValueError):
        is_pure = False

    status_label = "PURE TURMERIC" if is_pure else "ADULTERATED"
    confidence_note = (
        "The model does not supply calibrated posterior probabilities. "
        "Classification is based on decision boundary separation."
    )

    pred_output = PredictionOutput(
        predicted_class=predicted_class,
        predicted_percentage=predicted_percentage,
        model_version=model_version,
        modality="FTIR Spectroscopy",
        is_pure=is_pure,
        status_label=status_label,
        confidence_note=confidence_note,
    )

    clean_sample_id = sample_id or "Uploaded Sample"

    # Build enriched evidence payload with spectrum stats, PCA info, CV metrics
    try:
        metadata = get_metadata()
    except Exception:
        metadata = {}

    enriched_evidence = build_enriched_evidence(
        features_df=features,
        pipeline_result=pipeline_res,
        actual_level=actual_level,
        sample_meta=sample_meta,
        metadata=metadata,
    )
    enriched_evidence["language"] = explanation_lang

    # Generate structured 8-section explanation
    structured_explanation = generate_structured_explanation(
        enriched_evidence,
        depth=depth,
        use_gemini=use_gemini,
        lang=explanation_lang,
    )

    analysis_mode = structured_explanation.get("analysis_mode", "deterministic_fallback")
    summary = structured_explanation.get("executive_summary", "Analysis completed successfully.")
    uncertainty_warnings = pipeline_res.get("uncertainty_warnings", [])

    # Build supporting evidence list from evidence_and_reasoning for backward compat
    supporting_evidence: list[str] = []
    for item in structured_explanation.get("evidence_and_reasoning", []):
        if isinstance(item, dict):
            ev = item.get("evidence", "")
            if ev:
                supporting_evidence.append(ev)

    rec_verification_list = structured_explanation.get("recommended_next_steps", [])
    rec_verification = (
        rec_verification_list[0]
        if rec_verification_list
        else "Verify with an appropriate validated laboratory method."
    )

    # Persist to user's history
    analysis_id = save_analysis(
        user_id=user_id,
        sample_id=clean_sample_id,
        input_source=source_label,
        modality="FTIR",
        predicted_class=predicted_class,
        predicted_percentage=predicted_percentage,
        actual_level=actual_level,
        status=status_label,
        confidence_note=confidence_note,
        analysis_mode=analysis_mode,
        summary=summary,
        full_report=pipeline_res,
    )

    # Dispatch in-app notification if user enabled notifications
    try:
        user_pref = get_user_settings(user_id)
        if user_pref.get("notify_analysis", 1):
            category = "success" if is_pure else "warning"
            add_notification(
                user_id=user_id,
                title=f"Sample {clean_sample_id} Analyzed",
                message=f"Screening complete: predicted {predicted_class} ({status_label}).",
                category=category,
                action_link=f"analyze_{analysis_id}",
                dedupe_key=f"analysis_{analysis_id}",
            )
    except Exception as exc:
        LOGGER.warning("Could not dispatch analysis notification: %s", exc)

    timestamp_str = pipeline_res.get("report", {}).get("generated_at_utc")
    if not timestamp_str:
        from datetime import datetime, timezone
        timestamp_str = datetime.now(timezone.utc).isoformat()

    return AnalysisResult(
        analysis_id=analysis_id,
        user_id=user_id,
        timestamp=timestamp_str,
        sample_id=clean_sample_id,
        input_source=source_label,
        modality_used="FTIR Spectroscopy",
        prediction=pred_output,
        actual_level=actual_level,
        explanation_summary=summary,
        supporting_evidence=supporting_evidence,
        uncertainty_warnings=uncertainty_warnings,
        recommended_verification=rec_verification,
        analysis_mode=analysis_mode,
        raw_pipeline_output=pipeline_res,
        structured_explanation=structured_explanation,
        explanation_depth=depth,
    )


def get_model_performance_artifacts() -> dict[str, Any]:
    """Gather all evaluation tables, charts, and matrices from saved results."""
    results_root = PROJECT_ROOT / "results"
    nb9_dir = results_root / "notebook_09"
    nb8_dir = results_root / "notebook_08"

    artifacts: dict[str, Any] = {
        "cv_results": None,
        "holdout_results": None,
        "confusion_matrix_path": None,
        "cv_comparison_chart_path": None,
        "regression_results": None,
    }

    cv9 = nb9_dir / "fusion_cv_results.csv"
    if cv9.is_file():
        artifacts["cv_results"] = pd.read_csv(cv9)

    holdout = nb9_dir / "fusion_holdout_results.csv"
    if holdout.is_file():
        artifacts["holdout_results"] = pd.read_csv(holdout)

    reg_results = nb9_dir / "regression_results.csv"
    if reg_results.is_file():
        artifacts["regression_results"] = pd.read_csv(reg_results)

    cm_img = nb9_dir / "fusion_confusion_matrix.png"
    if cm_img.is_file():
        artifacts["confusion_matrix_path"] = str(cm_img)

    cv_chart = nb9_dir / "fusion_cv_comparison.png"
    if cv_chart.is_file():
        artifacts["cv_comparison_chart_path"] = str(cv_chart)

    return artifacts


def export_report_markdown(result: AnalysisResult) -> str:
    """Generate a clean, professional Markdown report for download."""
    import re

    def _strip_html(text: str) -> str:
        """Remove HTML tags for plain Markdown output."""
        return re.sub(r"<[^>]+>", "", text or "")

    p = result.prediction
    se = result.structured_explanation  # may be empty for legacy results

    md = [
        "# FoodSure AI — Turmeric Adulteration Analysis Report",
        "",
        f"**Analysis ID:** `{result.analysis_id}`  ",
        f"**Timestamp:** {result.timestamp}  ",
        f"**Sample Identifier:** {result.sample_id}  ",
        f"**Input Source:** {result.input_source}  ",
        f"**Modality Used:** {result.modality_used}  ",
        f"**Model Version:** {p.model_version}  ",
        f"**AI Mode:** {result.analysis_mode}  ",
        f"**Explanation Depth:** {result.explanation_depth}  ",
        "",
        "---",
        "",
        "## Predicted Result",
        "",
        f"- **Predicted Classification:** **{p.predicted_class}**",
    ]
    if p.predicted_percentage is not None:
        md.append(f"- **Regression Estimate:** **{p.predicted_percentage:g}%**")
    else:
        md.append("- **Regression Estimate:** Not available")
    md.append(f"- **Sample Status:** **{p.status_label}**")
    if result.actual_level is not None:
        md.append(f"- **Ground Truth Level (Dataset):** {result.actual_level:g}%")

    # ── Structured 8-section explanation ──────────────────────────────────
    if se:
        md.extend([
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            _strip_html(se.get("executive_summary", result.explanation_summary)),
            "",
            "## 2. Detailed Result Interpretation",
            "",
            _strip_html(se.get("result_interpretation", "")),
            "",
            "## 3. Evidence & Reasoning",
            "",
        ])
        for item in se.get("evidence_and_reasoning", []):
            if isinstance(item, dict):
                md.extend([
                    f"**Evidence:** {_strip_html(item.get('evidence', ''))}  ",
                    f"**Meaning:** {_strip_html(item.get('meaning', ''))}  ",
                    f"**Connection:** {_strip_html(item.get('connection', ''))}  ",
                    f"**Limitation:** {_strip_html(item.get('limitation', ''))}  ",
                    "",
                ])

        md.extend([
            "## 4. Scientific Explanation — Made Simple",
            "",
            _strip_html(se.get("scientific_explanation", "")),
            "",
            "## 5. Confidence & Uncertainty",
            "",
            _strip_html(se.get("confidence_and_uncertainty", "")),
            "",
            "## 6. Practical Implications",
            "",
            _strip_html(se.get("practical_implications", "")),
            "",
            "## 7. Recommended Next Steps",
            "",
        ])
        for step in se.get("recommended_next_steps", []):
            md.append(f"1. {_strip_html(step)}")

        md.extend([
            "",
            "## 8. Limitations & Transparency",
            "",
        ])
        for lim in se.get("limitations", []):
            md.append(f"- ⚠️ {_strip_html(lim)}")
    else:
        # Legacy fallback
        md.extend([
            "",
            "## AI Scientific Interpretation",
            "",
            f"> *Generated via {result.analysis_mode.replace('_', ' ').title()}*",
            "",
            result.explanation_summary,
            "",
            "## Supporting Evidence",
            "",
        ])
        for item in result.supporting_evidence:
            md.append(f"- {item}")

        md.extend(["", "## Uncertainty & Limitations", ""])
        for warn in result.uncertainty_warnings:
            md.append(f"- ⚠️ {warn}")

        md.extend([
            "",
            "## Recommended Verification",
            "",
            result.recommended_verification,
        ])

    md.extend([
        "",
        "---",
        "*Disclaimer: FoodSure AI is an AI-assisted research prototype. "
        "Results do not constitute certified food safety approval, regulatory compliance, "
        "or a replacement for accredited laboratory wet chemistry analysis.*",
    ])

    return "\n".join(md)


def generate_followup_answer(
    question: str,
    analysis_result: "AnalysisResult",
    use_gemini: bool = True,
) -> str:
    """Generate a follow-up question answer using the existing analysis context.

    Never re-runs the ML model.  Uses only the structured explanation and
    prediction already computed.
    """
    import os
    import json

    if not question or not question.strip():
        return "Please enter a question about the analysis."

    # Build a compact analysis context for the LLM
    structured = analysis_result.structured_explanation
    pred = analysis_result.prediction
    context_dict = {
        "sample_id": analysis_result.sample_id,
        "predicted_class": pred.predicted_class,
        "predicted_percentage": pred.predicted_percentage,
        "actual_level": analysis_result.actual_level,
        "analysis_mode": analysis_result.analysis_mode,
        "executive_summary": structured.get("executive_summary", ""),
        "result_interpretation": structured.get("result_interpretation", ""),
        "confidence_and_uncertainty": structured.get("confidence_and_uncertainty", ""),
        "practical_implications": structured.get("practical_implications", ""),
        "limitations": structured.get("limitations", []),
        "recommended_next_steps": structured.get("recommended_next_steps", []),
        "evidence_count": len(structured.get("evidence_and_reasoning", [])),
        "uncertainty_warnings": analysis_result.uncertainty_warnings,
    }
    analysis_context = json.dumps(context_dict, ensure_ascii=False, indent=2)

    if use_gemini:
        try:
            from ai_layer.analyst import _ensure_env_loaded, call_gemini_followup
            _ensure_env_loaded()
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key and not api_key.startswith("your_"):
                return call_gemini_followup(question.strip(), analysis_context, api_key)
        except Exception as exc:
            LOGGER.warning("Gemini follow-up call failed: %s", exc)

    # Deterministic fallback — keyword-based template answers
    return _deterministic_followup(question.strip(), analysis_result)


def _deterministic_followup(question: str, result: "AnalysisResult") -> str:
    """Template-based follow-up answers for common question types."""
    q = question.lower()
    pred = result.prediction
    structured = result.structured_explanation

    if any(kw in q for kw in ("mean", "class", "predicted", "what is", "what does")):
        return (
            f"The predicted class '{pred.predicted_class}' indicates that the model's "
            f"spectral pattern-matching found the sample most similar to turmeric samples "
            f"adulterated with {pred.predicted_class} wheat flour (w/w) in the training dataset. "
            f"This is a discrete classification from 7 trained levels (0%, 1%, 2%, 3%, 5%, 7%, 9%) "
            f"and not a continuous measurement."
        )

    if any(kw in q for kw in ("regression", "estimate", "differ", "percentage", "percent")):
        if pred.predicted_percentage is not None:
            return (
                f"The regression estimate ({pred.predicted_percentage:g}%) and the classifier "
                f"prediction ({pred.predicted_class}) use the same spectral features but "
                f"different mathematical approaches. The Logistic Regression assigns a discrete "
                f"class, while the Random Forest Regressor estimates a continuous value. Small "
                f"differences between them are expected and indicate the boundary between classes."
            )
        return (
            "A regression estimate was not available for this analysis. "
            "The classifier assigned a discrete class from the seven trained adulteration levels."
        )

    if any(kw in q for kw in ("reliable", "accurate", "trust", "confidence", "certain")):
        unc = structured.get("confidence_and_uncertainty", "")
        return (
            f"The model achieved 100% Macro F1 in 5-fold cross-validation on the research "
            f"dataset under controlled conditions. However, this does not guarantee real-world "
            f"accuracy on new instruments, sample batches, or preparation methods. "
            f"The model does not supply calibrated probabilities. "
            f"{'Key uncertainty: ' + result.uncertainty_warnings[0] if result.uncertainty_warnings else 'No specific uncertainty flags were raised for this sample.'}"
        )

    if any(kw in q for kw in ("laboratory", "lab", "confirm", "verify", "test")):
        steps = structured.get("recommended_next_steps", [])
        if steps:
            return "Recommended verification steps: " + " | ".join(steps[:3])
        return (
            "Submit the physical sample to an accredited food testing laboratory "
            "for validated wet chemistry analysis (e.g., microscopy, HPLC, or DNA-based methods)."
        )

    if any(kw in q for kw in ("limit", "weakness", "problem", "drawback", "cannot")):
        lims = structured.get("limitations", [])
        if lims:
            return "Key limitations: " + " • ".join(lims[:3])
        return (
            "Key limitations include: (1) trained on 350 controlled-environment samples, "
            "(2) wheat flour only as adulterant, (3) no feature-level explainability, "
            "(4) discrete class labels only (0–9%)."
        )

    if any(kw in q for kw in ("ftir", "infrared", "spectrum", "spectral", "wavenumber")):
        return (
            "ATR-FTIR (Attenuated Total Reflectance Fourier-Transform Infrared) spectroscopy "
            "measures how a sample absorbs infrared light at each wavenumber (cm⁻¹). "
            "Each chemical compound absorbs at characteristic wavenumbers, creating a unique "
            "'spectral fingerprint'. The model uses PCA-compressed versions of these "
            "fingerprints (2,522 wavenumbers → 13 components) to classify adulteration levels."
        )

    # Generic fallback
    return (
        f"Based on this analysis: the model predicted {pred.predicted_class} "
        f"adulteration for sample '{result.sample_id}'. "
        f"The analysis was performed using ATR-FTIR spectroscopy with PCA feature compression. "
        f"For more specific questions, please consult the detailed explanation sections above "
        f"or submit the sample to an accredited laboratory."
    )
