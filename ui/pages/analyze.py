"""Guided sample analysis workspace for FoodSure AI."""

from __future__ import annotations

import json
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from backend.service import (
    export_report_markdown,
    get_dataset_sample_ids,
    get_metadata,
    get_spectrum_data,
    load_dataset_sample,
    run_sample_analysis,
    validate_uploaded_ftir_csv,
)
from ui.components import page_header, render_spectrum_chart, status_badge
from ui.i18n import get_current_language, t
from ui.pages.explanation_view import (
    render_depth_selector,
    render_explanation,
    render_followup_interface,
)


def render_analyze_page(user: dict) -> None:
    page_header(
        t("analyze_header_title"),
        t("analyze_title"),
        t("analyze_desc"),
    )

    # Workflow step indicator
    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.8rem; margin-bottom: 2rem;">
            <div class="step-item"><div class="step-circle">1</div><div style="font-size:0.85rem; font-weight:700;">{t('step_1')}</div></div>
            <div class="step-item"><div class="step-circle">2</div><div style="font-size:0.85rem; font-weight:700;">{t('step_2')}</div></div>
            <div class="step-item"><div class="step-circle">3</div><div style="font-size:0.85rem; font-weight:700;">{t('step_3')}</div></div>
            <div class="step-item"><div class="step-circle">4</div><div style="font-size:0.85rem; font-weight:700;">{t('step_4')}</div></div>
            <div class="step-item"><div class="step-circle">5</div><div style="font-size:0.85rem; font-weight:700;">{t('step_5')}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        metadata = get_metadata()
        feature_columns = metadata["feature_order"]["FTIR"]
    except Exception as exc:
        st.error(f"Could not load model configuration: {exc}")
        return

    # Modality Choice
    c_mod1, c_mod2 = st.columns([1.5, 1])
    with c_mod1:
        modality_choice = st.selectbox(
            "Measurement Modality",
            (
                "ATR-FTIR Spectroscopy (Active & Connected)",
                "Hunter Lab Colorimetry (Research Baseline)",
                "EfficientNet-B0 Computer Vision (Tabular Embeddings)",
                "Multimodal Concatenation Fusion (FTIR + Color + Image)",
            ),
            index=0,
        )

    if not modality_choice.startswith("ATR-FTIR"):
        st.warning(
            f"Note: '{modality_choice}' was evaluated in research notebooks (Notebooks 04–09). "
            "In accordance with Phase 2 audit findings, the production inference artifact is "
            "parsimoniously configured for FTIR only (which achieved 100% CV Macro F1, tying multimodal fusion). "
            "Please select ATR-FTIR Spectroscopy to run live sample inference."
        )
        return

    st.markdown("---")
    input_mode = st.radio(
        "Select Input Source",
        ("Choose from 350 Research Dataset Samples", "Upload Custom FTIR Spectrum CSV"),
        horizontal=True,
    )

    sample_id: str | None = None
    actual_level: float | None = None
    features: pd.DataFrame | None = None
    sample_meta: dict | None = None
    source_label = ""
    spectrum_data: dict[str, list[float]] = {"wavenumbers": [], "absorbance": []}

    if input_mode == "Choose from 350 Research Dataset Samples":
        sample_ids = get_dataset_sample_ids()
        if not sample_ids:
            st.error("Dataset files are not available at the expected path. Please upload a CSV instead.")
        else:
            col_sel1, col_sel2 = st.columns([1.2, 1])
            with col_sel1:
                pre = st.session_state.pop("preselected_sample_id", None)
                def_idx = sample_ids.index(pre) if pre in sample_ids else 0
                selected_id = st.selectbox(
                    "Sample Identifier",
                    sample_ids,
                    index=def_idx,
                    help="Dataset sample identifiers follow the convention T{level}S{index} (e.g. T0S01 = 0% Pure, T3S15 = 3% Adulterated).",
                )

            if selected_id:
                try:
                    features, actual_level, sample_meta = load_dataset_sample(selected_id)
                    sample_id = selected_id
                    source_label = f"Mendeley Dataset ({'Train Split (280)' if sample_meta['is_train'] else 'Holdout Split (70)'})"
                    spectrum_data = get_spectrum_data(features)

                    with col_sel2:
                        st.markdown(
                            f"""
                            <div style="background: var(--surface); border: 1px solid var(--border-light); border-radius: 12px; padding: 0.9rem 1.1rem; margin-top: 1.6rem;">
                                <div style="font-size: 0.8rem; color: var(--ink-500); text-transform: uppercase; font-weight: 700;">Dataset Ground Truth</div>
                                <div style="font-size: 1.25rem; font-weight: 800; color: var(--forest-900);">{actual_level:g}% Wheat Flour</div>
                                <div style="font-size: 0.8rem; color: var(--ink-500);">Partition: {source_label}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                except Exception as exc:
                    st.error(f"Error loading sample: {exc}")

    else:
        st.markdown(
            """
            <div style="background: var(--turmeric-50); border: 1px solid var(--turmeric-100); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; font-size: 0.9rem; color: #684805;">
                <strong>Upload Instructions:</strong> Provide a single-row CSV with exactly 2,522 numeric ATR-FTIR columns matching the wavenumber features from 4000 cm⁻¹ to 650 cm⁻¹. An optional <code>Sample_ID</code> column may be included.
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader("Upload FTIR CSV", type=["csv"], key="custom_ftir_upload")
        if uploaded is not None:
            try:
                sample_id, features = validate_uploaded_ftir_csv(uploaded.getvalue())
                source_label = f"Uploaded CSV ({uploaded.name})"
                spectrum_data = get_spectrum_data(features)
                st.success(f"✓ Validated CSV: Exactly {features.shape[1]} FTIR wavenumber features detected.")
            except Exception as exc:
                st.error(f"Validation Error: {exc}")

    # Display Spectrum Plot if features available
    if features is not None and spectrum_data["wavenumbers"]:
        # Reset stale results if the user switched to a different sample
        current_sample_key = f"{input_mode}_{sample_id}"
        if st.session_state.get("active_sample_key") != current_sample_key:
            st.session_state["active_sample_key"] = current_sample_key
            st.session_state["latest_analysis"] = None
            st.session_state["followup_history"] = []
            st.session_state["followup_pending"] = ""

        with st.expander("🔬 View Raw Spectral Fingerprint (ATR-FTIR)", expanded=True):
            render_spectrum_chart(
                spectrum_data["wavenumbers"],
                spectrum_data["absorbance"],
                title=f"Sample Spectrum ({sample_id or 'Uploaded Sample'})",
            )

    st.markdown("---")

    # ── Analysis Options ───────────────────────────────────────────────────
    col_opt1, col_opt2 = st.columns([1.5, 1])
    with col_opt1:
        use_gemini = st.toggle(
            "Enable Google Gemini AI Scientific Interpretation",
            value=True,
            help="Interprets spectral findings, structures evidence, notes confidence caveats, and suggests laboratory verification.",
        )

    # Depth selector
    depth = render_depth_selector(key="analysis_depth_selector")

    if features is not None:
        if st.button("🚀 Run Adulteration Analysis", type="primary", use_container_width=True):
            # Clear previous follow-up history when running a new analysis
            st.session_state["followup_history"] = []
            st.session_state["followup_pending"] = ""

            spinner_msg = (
                "Generating AI scientific interpretation via Gemini…"
                if use_gemini
                else "Analyzing spectral features through PCA and model estimators…"
            )
            with st.spinner(spinner_msg):
                try:
                    result = run_sample_analysis(
                        features=features,
                        sample_id=sample_id,
                        actual_level=actual_level,
                        source_label=source_label,
                        user_id=user["user_id"],
                        use_gemini=use_gemini,
                        depth=depth,
                        sample_meta=sample_meta,
                        explanation_lang=get_current_language(),
                    )
                    st.session_state["latest_analysis"] = result
                    st.session_state["latest_use_gemini"] = use_gemini
                    st.success("✓ Analysis completed successfully and saved to your history.")
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")

    # Render Latest Result if available
    latest: Any = st.session_state.get("latest_analysis")
    if latest:
        render_analysis_result(latest, use_gemini=st.session_state.get("latest_use_gemini", True))


def render_analysis_result(res: Any, use_gemini: bool = True) -> None:
    p = res.prediction
    safe_sample_id = escape(res.sample_id)
    badge = status_badge(p.status_label, p.is_pure)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Hero Result Box
    st.markdown(
        f"""
        <div class="result-panel">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="eyebrow" style="color: var(--turmeric-500) !important;">PREDICTED ADULTERATION CLASS</span>
                    <div class="result-giant">{escape(p.predicted_class)}</div>
                    <div style="font-size: 1.1rem; color: #e2e8e4;">Sample: <strong>{safe_sample_id}</strong> • Source: {escape(res.input_source)}</div>
                </div>
                <div style="text-align: right;">
                    {badge}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metrics grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Classifier Class", p.predicted_class, help="Discrete adulteration level identified by Logistic Regression")
    with m2:
        est_str = f"{p.predicted_percentage:g}%" if p.predicted_percentage is not None else "Not Available"
        st.metric("Regression Estimate", est_str, help="Continuous percentage quantified by Random Forest Regressor")
    with m3:
        actual_str = f"{res.actual_level:g}%" if res.actual_level is not None else "Unknown"
        st.metric("Dataset Ground Truth", actual_str, help="Controlled target concentration recorded in the research dataset")
    with m4:
        mode_label = "Gemini AI" if "gemini" in res.analysis_mode.lower() or "llm" in res.analysis_mode.lower() else "Deterministic"
        st.metric("AI Analyst Mode", mode_label, help="Engine used to generate scientific explanations and safety checks")

    st.caption("ℹ️ Classification predicts discrete adulteration categories (0%–9%); regression independently estimates continuous percentage. Confidence is not calibrated to true external probabilities.")

    # ── Render 8-section structured explanation ─────────────────────────
    if res.structured_explanation:
        render_explanation(res.structured_explanation, res)
    else:
        # Fallback if structured_explanation is missing (legacy result)
        st.markdown("### 🤖 Scientific AI Interpretation")
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-sm);">
                <p style="font-size: 1.05rem; line-height: 1.65; color: var(--forest-900); font-weight: 500;">
                    {escape(res.explanation_summary)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Follow-up question interface ─────────────────────────────────────
    render_followup_interface(res, use_gemini=use_gemini)

    st.markdown("---")

    # Download & Actions
    col_dl1, col_dl2, col_clear = st.columns([1, 1, 1])
    with col_dl1:
        md_text = export_report_markdown(res)
        st.download_button(
            "📥 Download Markdown Report",
            data=md_text,
            file_name=f"FoodSure_Report_{res.sample_id}_{res.analysis_id[:8]}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_dl2:
        json_text = json.dumps(res.to_dict(), indent=2, ensure_ascii=False)
        st.download_button(
            "📄 Download JSON Data",
            data=json_text,
            file_name=f"FoodSure_Data_{res.sample_id}_{res.analysis_id[:8]}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_clear:
        if st.button("🔄 Start New Analysis", use_container_width=True):
            st.session_state["latest_analysis"] = None
            st.session_state["followup_history"] = []
            st.session_state["followup_pending"] = ""
            st.rerun()
