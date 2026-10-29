"""FoodSure AI Explanation Engine.

Builds enriched evidence payloads and generates 8-section structured
explanations with configurable depth (quick / detailed / technical).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Spectrum statistics helpers
# ---------------------------------------------------------------------------

def _compute_spectrum_stats(features_df: pd.DataFrame) -> dict[str, Any]:
    """Compute summary statistics from raw FTIR features for the evidence payload."""
    try:
        row = features_df.iloc[0]
        wavenumbers: list[float] = []
        absorbances: list[float] = []

        for col, val in row.items():
            try:
                wn = float(col)
                ab = float(val)
                if math.isfinite(wn) and math.isfinite(ab):
                    wavenumbers.append(wn)
                    absorbances.append(ab)
            except (TypeError, ValueError):
                continue

        if not absorbances:
            return {}

        arr = np.array(absorbances, dtype=float)
        wn_arr = np.array(wavenumbers, dtype=float)

        peak_idx = int(np.argmax(arr))
        trough_idx = int(np.argmin(arr))

        # Key spectral regions for ATR-FTIR turmeric analysis
        region_stats: dict[str, Any] = {}
        regions = {
            "fingerprint_region": (600, 1800),
            "curcumin_region": (1580, 1640),
            "CH_stretch": (2800, 3000),
            "OH_stretch": (3200, 3600),
        }
        for region_name, (lo, hi) in regions.items():
            mask = (wn_arr >= lo) & (wn_arr <= hi)
            if mask.sum() > 0:
                region_abs = arr[mask]
                region_stats[region_name] = {
                    "wavenumber_range": f"{lo}–{hi} cm⁻¹",
                    "mean_absorbance": float(np.mean(region_abs)),
                    "max_absorbance": float(np.max(region_abs)),
                    "n_points": int(mask.sum()),
                }

        return {
            "n_features": len(absorbances),
            "wavenumber_range": f"{min(wavenumbers):.1f}–{max(wavenumbers):.1f} cm⁻¹",
            "mean_absorbance": float(np.mean(arr)),
            "std_absorbance": float(np.std(arr)),
            "peak_absorbance_wavenumber": float(wn_arr[peak_idx]),
            "peak_absorbance_value": float(arr[peak_idx]),
            "trough_absorbance_wavenumber": float(wn_arr[trough_idx]),
            "trough_absorbance_value": float(arr[trough_idx]),
            "spectral_regions": region_stats,
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Enriched evidence builder
# ---------------------------------------------------------------------------

def build_enriched_evidence(
    features_df: pd.DataFrame,
    pipeline_result: dict[str, Any],
    actual_level: float | None,
    sample_meta: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build an enriched evidence payload for the explanation engine.

    Adds spectrum statistics, PCA info, CV metrics, and sample partition
    information on top of the standard pipeline evidence.
    """
    prediction_raw = pipeline_result.get("prediction", {})
    predicted_class = prediction_raw.get("predicted_class", "Unknown")
    predicted_percentage = prediction_raw.get("predicted_percentage")
    model_version = pipeline_result.get(
        "model_version",
        metadata.get("model_version", "foodsure-v1"),
    )

    # Modalities actually used
    modalities_used = pipeline_result.get("modalities_used", ["ftir"])
    if isinstance(modalities_used, list):
        modalities_used = [str(m).lower() for m in modalities_used]
    else:
        modalities_used = ["ftir"]

    # Existing evidence + uncertainty from pipeline
    existing_evidence = pipeline_result.get("evidence", {})
    evidence_items_raw = existing_evidence.get("evidence", []) if isinstance(existing_evidence, dict) else []
    uncertainty_flags = pipeline_result.get("uncertainty_warnings", [])
    limitations_raw: list[str] = []

    # Spectrum statistics
    spectrum_stats = _compute_spectrum_stats(features_df)

    # PCA info from metadata
    pca_info: dict[str, Any] = {}
    pca_meta = metadata.get("pca", {})
    if pca_meta:
        pca_info = {
            "n_components": pca_meta.get("n_components", 13),
            "explained_variance_pct": round(
                pca_meta.get("explained_variance_ratio_sum", 0.9004) * 100, 2
            ),
        }
    else:
        pca_info = {"n_components": 13, "explained_variance_pct": 90.04}

    # CV metrics from metadata
    cv_metrics: dict[str, Any] = {}
    cv_raw = metadata.get("cv_results", {})
    if cv_raw:
        cv_metrics = {
            "macro_f1_mean": cv_raw.get("mean_macro_f1", cv_raw.get("macro_f1_mean", 1.0)),
            "folds": cv_raw.get("n_folds", 5),
        }

    # Sample partition
    sample_partition = "unknown"
    is_train: bool | None = None
    if sample_meta:
        is_train = sample_meta.get("is_train")
        if is_train is True:
            sample_partition = "training split (280 samples)"
        elif is_train is False:
            sample_partition = "holdout test split (70 samples)"

    # Build regression info
    reg_estimate: float | None = None
    if predicted_percentage is not None:
        try:
            reg_estimate = float(predicted_percentage)
        except (TypeError, ValueError):
            reg_estimate = None

    # Construct model_result dict for the analyst
    model_result = {
        "prediction": predicted_class,
        "regression_estimate": reg_estimate,
        "target_type": "classification",
        "model_version": model_version,
    }

    # Build standard evidence items list
    evidence_items: list[dict[str, Any]] = []
    for item in evidence_items_raw:
        if isinstance(item, dict):
            evidence_items.append({
                "description": item.get("description", str(item)),
                "source": item.get("source", "pipeline"),
            })
        else:
            evidence_items.append({
                "description": str(item),
                "source": "pipeline",
            })

    # Combine payload
    enriched: dict[str, Any] = {
        "model_version": model_version,
        "modalities_used": modalities_used,
        "model_result": model_result,
        "evidence": evidence_items,
        "uncertainty_flags": uncertainty_flags,
        "limitations": limitations_raw,
        # Enrichments
        "spectrum_stats": spectrum_stats,
        "pca_info": pca_info,
        "cv_metrics": cv_metrics,
        "sample_partition": sample_partition,
        "is_train_sample": is_train,
        "actual_level": actual_level,
    }

    # Remove None/non-JSON-safe values
    import json
    try:
        json.dumps(enriched, allow_nan=False)
    except (TypeError, ValueError):
        # Strip spectrum_stats if it contains invalid values
        enriched["spectrum_stats"] = {}

    return enriched


# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------

def generate_structured_explanation(
    enriched_evidence: dict[str, Any],
    depth: str = "detailed",
    use_gemini: bool = True,
    lang: str = "en",
) -> dict[str, Any]:
    """Generate an 8-section structured explanation.

    Parameters
    ----------
    enriched_evidence:
        Output of `build_enriched_evidence()`.
    depth:
        ``"quick"`` | ``"detailed"`` | ``"technical"``
    use_gemini:
        If True, attempt Gemini API call before falling back to deterministic.
    lang:
        ``"en"`` or ``"hi"``
    """
    from ai_layer.analyst import analyze

    enriched_evidence["language"] = lang
    return analyze(enriched_evidence, use_llm=use_gemini, depth=depth, lang=lang)


def generate_deterministic_explanation(
    enriched_evidence: dict[str, Any],
    depth: str = "detailed",
    lang: str = "en",
) -> dict[str, Any]:
    """Generate a deterministic 8-section explanation (no LLM call)."""
    from ai_layer.analyst import deterministic_analysis

    enriched_evidence["language"] = lang
    return deterministic_analysis(enriched_evidence, depth=depth, lang=lang)

    return deterministic_analysis(enriched_evidence, depth=depth)
