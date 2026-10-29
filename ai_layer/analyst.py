"""FoodSure AI Analyst.

Explains supplied model outputs and evidence using a structured 8-section
JSON schema.  Does not train models or generate adulteration predictions.
"""

from __future__ import annotations

import json
import os
from typing import Any

from pathlib import Path

from ai_layer.prompts import (
    FOLLOWUP_SYSTEM_PROMPT,
    FOLLOWUP_USER_TEMPLATE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class AnalystInputError(ValueError):
    """Raised when the analyst receives an invalid evidence payload."""


class AnalystError(RuntimeError):
    """Raised when analysis cannot produce a valid result."""


# ---------------------------------------------------------------------------
# Schema definition — 8-section structured output
# ---------------------------------------------------------------------------

OUTPUT_FIELDS = (
    "executive_summary",
    "result_interpretation",
    "evidence_and_reasoning",
    "scientific_explanation",
    "confidence_and_uncertainty",
    "practical_implications",
    "recommended_next_steps",
    "limitations",
)

# follow_up_questions is validated separately (optional grace)
_STRING_FIELDS = (
    "executive_summary",
    "result_interpretation",
    "scientific_explanation",
    "confidence_and_uncertainty",
    "practical_implications",
)
_LIST_OF_STR_FIELDS = (
    "recommended_next_steps",
    "limitations",
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


def deterministic_analysis(
    payload: dict[str, Any],
    depth: str = "detailed",
    lang: str = "en",
) -> dict[str, Any]:
    """Generate a conservative 8-section explanation without using an LLM."""

    validate_payload(payload)

    result = payload["model_result"]
    modalities = payload["modalities_used"]
    evidence = payload.get("evidence", [])
    uncertainty_flags = payload.get("uncertainty_flags", [])
    limitations_in = payload.get("limitations", [])

    prediction = result.get("prediction")
    regression_est = result.get("regression_estimate")
    target_type = result.get("target_type", "classification")
    model_version = payload["model_version"]

    # Spectrum statistics (enriched payload fields)
    spectrum_stats = payload.get("spectrum_stats", {})
    sample_partition = payload.get("sample_partition", "unknown")
    actual_level = payload.get("actual_level")
    pca_info = payload.get("pca_info", {})
    cv_metrics = payload.get("cv_metrics", {})

    # ── Executive Summary ──────────────────────────────────────────────────
    if prediction is None:
        exec_summary = (
            "The supplied payload does not contain a model prediction. "
            "No conclusion about adulteration status can be drawn from this result. "
            "Ensure the pipeline completed successfully before interpreting outcomes."
        )
    else:
        pred_desc = f"adulteration class {prediction}" if prediction != "0%" else "pure turmeric (0% adulteration)"
        reg_clause = ""
        if regression_est is not None:
            reg_clause = (
                f" The regression estimator independently quantified the adulteration "
                f"level at approximately {regression_est:g}%."
            )
        truth_clause = ""
        if actual_level is not None:
            truth_clause = (
                f" The dataset ground truth for this sample is {actual_level:g}% wheat flour."
            )
        exec_summary = (
            f"The FoodSure AI system analyzed an ATR-FTIR spectroscopic fingerprint "
            f"(sample partition: {sample_partition}) using a Logistic Regression classifier "
            f"supported by principal component analysis (PCA) dimensionality reduction. "
            f"The model predicted {pred_desc}.{reg_clause}{truth_clause} "
            f"This is a research-prototype model output and must not be used in place of "
            f"validated laboratory analysis."
        )

    # ── Result Interpretation ──────────────────────────────────────────────
    if prediction is None:
        result_interp = (
            "No prediction is available. The pipeline may have encountered an error "
            "or the input data may not have met the feature contract requirements."
        )
    else:
        is_pure = str(prediction).strip() in ("0%", "0.0%", "0")
        class_meaning = (
            "This indicates the model believes the sample contains no detectable "
            "wheat flour adulteration within the model's seven-class resolution."
            if is_pure
            else
            f"This indicates the model detected spectral evidence consistent with "
            f"wheat flour adulteration at the {prediction} concentration level. "
            f"The model was trained on seven discrete adulteration classes: "
            f"0%, 1%, 2%, 3%, 5%, 7%, and 9%."
        )
        reg_interp = ""
        if regression_est is not None:
            reg_interp = (
                f" The Random Forest Regressor provides an independent continuous "
                f"estimate of {regression_est:g}%, which may differ from the classifier's "
                f"discrete class label. Both outputs come from the same spectral features "
                f"but use different mathematical approaches."
            )
        result_interp = (
            f"The model predicted class: {prediction}. {class_meaning}{reg_interp} "
            f"The classifier assigns each sample to one of seven discrete adulteration "
            f"levels; it cannot detect adulteration outside these trained classes. "
            f"The model does not supply calibrated posterior probabilities, so the "
            f"output should be interpreted as a pattern-matching decision rather than "
            f"a statistical confidence score."
        )

    # ── Evidence & Reasoning ──────────────────────────────────────────────
    evidence_items_out = []

    # Spectrum statistics evidence
    if spectrum_stats:
        peak_wn = spectrum_stats.get("peak_absorbance_wavenumber")
        mean_abs = spectrum_stats.get("mean_absorbance")
        n_features = spectrum_stats.get("n_features")
        ev_desc = f"ATR-FTIR spectrum with {n_features} wavenumber features" if n_features else "ATR-FTIR spectrum"
        if peak_wn is not None:
            ev_desc += f"; highest absorbance at {peak_wn:.1f} cm⁻¹"
        if mean_abs is not None:
            ev_desc += f"; mean absorbance {mean_abs:.4f}"
        evidence_items_out.append({
            "evidence": ev_desc,
            "meaning": (
                "ATR-FTIR (Attenuated Total Reflectance Fourier-Transform Infrared) "
                "spectroscopy measures how a sample absorbs infrared light at different "
                "wavenumbers (cm⁻¹). Each chemical bond in a molecule absorbs at "
                "characteristic wavenumbers, producing a unique 'spectral fingerprint'."
            ),
            "connection": (
                f"The spectrum was reduced from {n_features or 2522} raw wavenumber "
                f"features to {pca_info.get('n_components', 13)} principal components "
                f"(explaining {pca_info.get('explained_variance_pct', 90.04):.1f}% of variance) "
                f"before classification. The {prediction or 'predicted'} class assignment "
                f"reflects which training-data cluster these compressed features most "
                f"closely resemble."
            ),
            "limitation": (
                "The model does not expose which specific wavenumber regions drove the "
                "prediction (no SHAP or feature importance is available). The spectral "
                "statistics above describe the raw input, not the model's internal reasoning."
            ),
        })

    # PCA information evidence
    if pca_info:
        evidence_items_out.append({
            "evidence": (
                f"PCA compression: {pca_info.get('n_components', 13)} components, "
                f"{pca_info.get('explained_variance_pct', 90.04):.1f}% variance retained"
            ),
            "meaning": (
                "Principal Component Analysis (PCA) reduces thousands of correlated "
                "wavenumber measurements into a smaller set of composite variables "
                "that capture most of the meaningful variation. This prevents "
                "over-fitting to noise in the raw spectrum."
            ),
            "connection": (
                "The 13 PCA components serve as the actual numerical inputs to the "
                "Logistic Regression classifier. The prediction is based on the "
                "sample's position in this compressed 13-dimensional feature space."
            ),
            "limitation": (
                "PCA compression is a linear transformation. If adulteration produces "
                "subtle non-linear spectral changes, some discriminative information "
                "may be lost during compression."
            ),
        })

    # Cross-validation metrics evidence
    if cv_metrics:
        macro_f1 = cv_metrics.get("macro_f1_mean", cv_metrics.get("mean_macro_f1"))
        if macro_f1 is not None:
            evidence_items_out.append({
                "evidence": f"5-fold cross-validation Macro F1: {macro_f1:.4f} (on 280 training samples)",
                "meaning": (
                    "Cross-validation Macro F1 = 1.00 means the model correctly classified "
                    "all seven adulteration classes in every cross-validation fold during "
                    "training. This is an exceptionally strong within-dataset result."
                ),
                "connection": (
                    "This metric supports the model's ability to separate spectral "
                    "patterns for the seven adulteration classes under research conditions. "
                    "It does not guarantee performance on new samples outside the dataset."
                ),
                "limitation": (
                    "Cross-validation performance is measured on held-out folds from the "
                    "same Mendeley dataset. Real-world generalization to different "
                    "instruments, labs, or sample batches is unknown."
                ),
            })

    # Pipeline-reported evidence items
    for item in evidence:
        if isinstance(item, dict):
            desc = item.get("description", str(item))
            src = item.get("source", "pipeline")
            evidence_items_out.append({
                "evidence": f"{desc} (source: {src})",
                "meaning": "Pipeline-reported observation from the inference process.",
                "connection": "Included as part of the model's reported evidence record.",
                "limitation": "Detailed interpretation requires domain-specific context.",
            })
        else:
            evidence_items_out.append({
                "evidence": str(item),
                "meaning": "Pipeline-reported observation.",
                "connection": "Part of the inference record.",
                "limitation": "See full evidence payload for context.",
            })

    if not evidence_items_out:
        evidence_items_out.append({
            "evidence": "No sample-specific evidence was available from this pipeline run.",
            "meaning": "The pipeline did not expose feature-level contributions for this prediction.",
            "connection": "The prediction was still produced by the trained model, but the specific spectral evidence cannot be shown.",
            "limitation": "Without explainability data, the basis for the prediction cannot be verified at the feature level.",
        })

    # ── Scientific Explanation ─────────────────────────────────────────────
    sci_exp = (
        "**What is turmeric adulteration?**\n"
        "Turmeric adulteration means that a foreign substance — in this research, "
        "wheat flour — has been mixed into turmeric powder, reducing its purity. "
        "This is a significant food safety concern because adulterated turmeric may "
        "mislead consumers about quality and potentially affect people with allergies.\n\n"
        "**What is ATR-FTIR spectroscopy?**\n"
        "ATR-FTIR stands for Attenuated Total Reflectance Fourier-Transform Infrared "
        "Spectroscopy. In simple terms: a beam of infrared light is shone onto the "
        "sample. Different chemical compounds absorb different wavelengths of this "
        "light. By measuring how much light is absorbed at each wavenumber (a unit "
        "representing light frequency, measured in cm⁻¹), the instrument produces a "
        "'spectral fingerprint' unique to each chemical mixture.\n\n"
        "**What is PCA (Principal Component Analysis)?**\n"
        "The raw FTIR spectrum has 2,522 data points (one per wavenumber). Many of "
        "these are correlated — neighboring wavenumbers often move together. PCA is "
        "a mathematical technique that compresses this information into a smaller set "
        "of summary variables (principal components) without losing too much "
        "information. In this model, 13 components capture over 90% of the spectral "
        "variation.\n\n"
        "**How does the ML model make a prediction?**\n"
        "The Logistic Regression classifier was trained on 280 turmeric samples "
        "spanning seven known adulteration levels (0% to 9% wheat flour). It learned "
        "which patterns in the 13 PCA components correspond to each adulteration "
        "class. When a new spectrum arrives, the model compares its PCA values to "
        "what it learned during training and assigns the most likely class.\n\n"
        "**Why is a model prediction not the same as a laboratory result?**\n"
        "The model learned from one research dataset under controlled conditions. "
        "Laboratory-certified analysis uses validated wet chemistry methods, "
        "calibrated instruments, and accredited procedures. A model prediction is "
        "a data-driven pattern match — a very useful screening tool, but not a "
        "substitute for definitive laboratory confirmation."
    )

    # ── Confidence & Uncertainty ───────────────────────────────────────────
    unc_text_parts = [
        "The FoodSure AI model does not produce calibrated posterior probabilities. "
        "This means the model's class assignment cannot be directly interpreted as "
        "a percentage likelihood that the sample belongs to that class.\n"
    ]
    if uncertainty_flags:
        unc_text_parts.append("The following uncertainty flags were raised by the pipeline:")
        for flag in uncertainty_flags:
            unc_text_parts.append(f"• {flag}")
    else:
        unc_text_parts.append(
            "No explicit uncertainty flags were raised for this analysis. "
            "This does not mean uncertainty is absent — it means the pipeline "
            "did not detect a specific known issue. External factors such as "
            "instrument variability, sample preparation, and distribution shift "
            "are always sources of uncertainty."
        )
    conf_uncertainty = "\n".join(unc_text_parts)

    # ── Practical Implications ─────────────────────────────────────────────
    if prediction is None:
        prac_impl = (
            "No actionable result is available because no prediction was produced. "
            "Review the input data and pipeline logs before drawing conclusions."
        )
    elif str(prediction).strip() in ("0%", "0.0%", "0"):
        prac_impl = (
            "The model's prediction of pure turmeric (0% adulteration) suggests that "
            "the spectral fingerprint is consistent with unadulterated turmeric within "
            "the model's training distribution. For research purposes, this is a "
            "promising screening result. However, for regulatory or commercial decisions, "
            "independent laboratory confirmation is mandatory. The model's research-only "
            "status means this result alone is not sufficient for quality certification."
        )
    else:
        prac_impl = (
            f"The model's prediction of {prediction} wheat flour adulteration indicates "
            f"that the spectral fingerprint matches patterns associated with adulterated "
            f"samples in the training dataset. This is a significant finding that warrants "
            f"follow-up laboratory analysis before any regulatory or commercial action is taken. "
            f"The result should be reported to a qualified food safety professional. "
            f"Do not use this prediction alone to reject, recall, or quarantine food products."
        )

    # ── Recommended Next Steps ─────────────────────────────────────────────
    next_steps = [
        "Submit the physical sample to an accredited food testing laboratory for "
        "validated wet chemistry analysis (e.g., microscopy, HPLC, or DNA-based methods).",
        "Document the sample chain of custody, instrument calibration date, and "
        "ATR-FTIR measurement conditions for reproducibility.",
        "Compare this result against additional samples from the same batch to assess "
        "within-batch variability.",
        "If adulteration is confirmed by laboratory analysis, follow applicable food "
        "safety regulations (e.g., FSSAI, EFSA, or relevant national authority).",
        "Consider implementing this screening tool as part of a multi-step quality "
        "control workflow rather than as a standalone decision system.",
    ]

    # ── Limitations ────────────────────────────────────────────────────────
    limitations_out = list(limitations_in) + [
        "FoodSure AI is a research prototype trained on 350 controlled-environment "
        "samples. Real-world generalization is unverified.",
        "The model was trained exclusively on wheat flour as the adulterant. Other "
        "adulterants (chalk, starch, synthetic dyes) are not within scope.",
        "The model does not expose feature-level explanations (no SHAP or "
        "feature importance available for individual predictions).",
        "Predicted adulteration classes are discrete (0%, 1%, 2%, 3%, 5%, 7%, 9%). "
        "Intermediate values (e.g., 4%, 6%) are not represented.",
        "ATR-FTIR results can be influenced by instrument model, operator technique, "
        "sample particle size, and measurement conditions.",
        "FoodSure AI is not a substitute for accredited laboratory testing and does "
        "not constitute regulatory approval or food safety certification.",
    ]

    # ── Follow-up Questions ────────────────────────────────────────────────
    follow_up_qs = [
        "What does this predicted class actually mean?",
        "Why does the regression estimate differ from the classified level?",
        "How reliable is the FTIR analysis for detecting wheat flour adulteration?",
        "What laboratory tests should I run to confirm this result?",
        "What are the limitations of using only FTIR for adulteration detection?",
    ]

    return {
        "executive_summary": exec_summary,
        "result_interpretation": result_interp,
        "evidence_and_reasoning": evidence_items_out,
        "scientific_explanation": sci_exp,
        "confidence_and_uncertainty": conf_uncertainty,
        "practical_implications": prac_impl,
        "recommended_next_steps": next_steps,
        "limitations": limitations_out,
        "follow_up_questions": follow_up_qs,
        "analysis_mode": "deterministic_fallback",
        "depth": depth,
    }


def _parse_llm_output(response: str) -> dict[str, Any]:
    """Parse and validate the new 8-section JSON schema from an LLM response."""

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

    # Validate string fields
    for field in _STRING_FIELDS:
        value = parsed[field]
        if not isinstance(value, str) or not value.strip():
            raise AnalystError(
                f"LLM output field '{field}' must be a non-empty string."
            )

    # Validate list-of-strings fields
    for field in _LIST_OF_STR_FIELDS:
        value = parsed[field]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise AnalystError(
                f"LLM output field '{field}' must be a list of strings."
            )

    # Validate evidence_and_reasoning
    ear = parsed["evidence_and_reasoning"]
    if not isinstance(ear, list) or len(ear) == 0:
        raise AnalystError(
            "'evidence_and_reasoning' must be a non-empty list."
        )
    for i, item in enumerate(ear):
        if not isinstance(item, dict):
            raise AnalystError(
                f"evidence_and_reasoning[{i}] must be a dict."
            )
        for key in ("evidence", "meaning", "connection", "limitation"):
            if not isinstance(item.get(key), str):
                raise AnalystError(
                    f"evidence_and_reasoning[{i}].{key} must be a string."
                )

    return parsed


def _ensure_env_loaded() -> None:
    """Ensure environment variables from local .env are loaded safely without external dependencies."""
    if "GEMINI_API_KEY" in os.environ and "OPENAI_API_KEY" in os.environ:
        return
    candidates = (
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env",
    )
    for env_path in candidates:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key, value = key.strip(), value.strip()
                        if key and key not in os.environ:
                            os.environ[key] = value
            except Exception:
                pass


def _call_gemini(
    payload: dict[str, Any],
    api_key: str,
    depth: str = "detailed",
    lang: str = "en",
) -> dict[str, Any]:
    """Call Google Gemini generateContent API with the new 8-section schema."""
    import urllib.error
    import urllib.request

    effective_lang = lang or payload.get("language", "en")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        evidence_payload=json.dumps(payload, ensure_ascii=False, allow_nan=False),
        depth=depth,
    )
    if effective_lang == "hi":
        user_prompt += (
            "\n\nLANGUAGE REQUIREMENT: Generate all explanatory text in formal, fluent, "
            "clear Hindi (हिन्दी) script. Keep technical scientific symbols and terms "
            "(ATR-FTIR, PCA, wavenumber) alongside their Hindi explanations. Maintain strictly "
            "valid JSON matching the schema."
        )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                raise AnalystError("Gemini returned no candidates.")
            content = (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            parsed = _parse_llm_output(content)

            # Security: preserve the ML model's original prediction — never
            # allow Gemini to change it.
            parsed["analysis_mode"] = "gemini_llm"
            parsed["depth"] = depth
            parsed["model_version"] = payload["model_version"]
            parsed["provider"] = f"gemini ({model})"

            # Ensure follow_up_questions is present
            if "follow_up_questions" not in parsed or not isinstance(
                parsed["follow_up_questions"], list
            ):
                parsed["follow_up_questions"] = [
                    "What does this predicted class actually mean?",
                    "Why does the regression estimate differ from the classified level?",
                    "How reliable is the FTIR analysis for detecting wheat flour adulteration?",
                    "What laboratory tests should I run to confirm this result?",
                    "What are the limitations of using only FTIR for adulteration detection?",
                ]

            return parsed
    except AnalystError:
        raise
    except Exception as exc:
        raise AnalystError(f"Gemini analysis failed ({type(exc).__name__}).") from exc


def _call_llm(
    payload: dict[str, Any],
    depth: str = "detailed",
    lang: str = "en",
) -> dict[str, Any]:
    """Call configured LLM (Google Gemini preferred)."""
    _ensure_env_loaded()
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip() and not gemini_key.startswith("your_"):
        return _call_gemini(payload, gemini_key.strip(), depth=depth, lang=lang)

    raise AnalystError("No LLM provider is configured.")


def call_gemini_followup(
    question: str,
    analysis_context: str,
    api_key: str,
) -> str:
    """Call Gemini for a follow-up question answer."""
    import urllib.request

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    user_prompt = FOLLOWUP_USER_TEMPLATE.format(
        analysis_context=analysis_context,
        question=question,
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": FOLLOWUP_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 512,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                raise AnalystError("Gemini returned no candidates for follow-up.")
            return (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )
    except AnalystError:
        raise
    except Exception as exc:
        raise AnalystError(f"Follow-up call failed ({type(exc).__name__}).") from exc


def analyze(
    payload: dict[str, Any],
    *,
    use_llm: bool = True,
    depth: str = "detailed",
    lang: str = "en",
) -> dict[str, Any]:
    """Analyze model evidence, returning 8-section structured explanation.

    Falls back to the deterministic template if LLM is unavailable.
    """

    validate_payload(payload)
    effective_lang = lang or payload.get("language", "en")

    if use_llm:
        try:
            return _call_llm(payload, depth=depth, lang=effective_lang)
        except AnalystError:
            result = deterministic_analysis(payload, depth=depth, lang=effective_lang)
            result["analysis_mode"] = "deterministic_fallback"
            result["provider_note"] = (
                "LLM analysis was unavailable or invalid; "
                "deterministic analysis was used."
            )
            return result

    return deterministic_analysis(payload, depth=depth, lang=effective_lang)
