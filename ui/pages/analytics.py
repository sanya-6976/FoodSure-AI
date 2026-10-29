"""Dedicated Analytics & Visual Insights page for FoodSure AI."""

from __future__ import annotations

import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Any
import pandas as pd

from backend.analytics_service import (
    get_activity_timeline,
    get_dataset_class_distribution,
    get_prediction_distribution,
)
from backend.history import get_user_history
from backend.service import get_model_performance_artifacts
from ui.components import (
    page_header,
    render_activity_chart,
    render_dataset_benchmark_chart,
    render_distribution_chart,
)
from ui.i18n import t


def render_analytics_page(user: dict[str, Any]) -> None:
    user_id = user["user_id"]

    page_header(
        t("analytics_header_title"),
        t("analytics_title"),
        t("analytics_desc"),
    )

    history = get_user_history(user_id, limit=2000)

    # ── Filter Bar ────────────────────────────────────────────────────────
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.2])
    with f_col1:
        date_filter = st.selectbox(
            t("filter_date_range"),
            [t("filter_all_time"), t("filter_last_7"), t("filter_last_30")],
            index=0,
        )
    with f_col2:
        status_filter = st.selectbox(
            t("filter_status"),
            [t("filter_all"), t("filter_pure_only"), t("filter_adulterated_only")],
            index=0,
        )

    # Apply Filters
    filtered_history = list(history)
    now_utc = datetime.now(timezone.utc)

    if date_filter == t("filter_last_7"):
        cutoff = (now_utc - timedelta(days=7)).isoformat()
        filtered_history = [h for h in filtered_history if str(h.get("timestamp", "")) >= cutoff]
    elif date_filter == t("filter_last_30"):
        cutoff = (now_utc - timedelta(days=30)).isoformat()
        filtered_history = [h for h in filtered_history if str(h.get("timestamp", "")) >= cutoff]

    if status_filter == t("filter_pure_only"):
        filtered_history = [h for h in filtered_history if "PURE" in str(h.get("status", "")).upper()]
    elif status_filter == t("filter_adulterated_only"):
        filtered_history = [h for h in filtered_history if "ADULTERATED" in str(h.get("status", "")).upper()]

    with f_col3:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if filtered_history:
            df_export = pd.DataFrame(filtered_history)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                t("export_analytics_csv"),
                data=csv_bytes,
                file_name=f"FoodSure_Analytics_{user_id[:6]}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")

    # ── Filtered Summary Metrics ──────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(t("kpi_my_analyses"), len(filtered_history))
    with m2:
        pures = sum(1 for h in filtered_history if "PURE" in str(h.get("status", "")).upper())
        st.metric(t("kpi_pure_rate"), pures)
    with m3:
        adultered = len(filtered_history) - pures
        st.metric(t("kpi_adulterated_count"), adultered)
    with m4:
        st.metric(t("kpi_dataset_benchmark"), "350 Samples", t("kpi_dataset_sub"))

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ── Charts Grid ───────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(f"### 📈 {t('chart_activity_title')}")
        st.caption(t("chart_activity_caption"))
        timeline_df = get_activity_timeline(user_id, days=14)
        render_activity_chart(timeline_df, height=270)

    with chart_col2:
        st.markdown(f"### 📊 {t('chart_class_dist_title')}")
        st.caption(t("chart_class_dist_caption"))
        dist_df = get_prediction_distribution(user_id)
        render_distribution_chart(dist_df, height=270)

    st.markdown("---")

    # ── Research Dataset Benchmark Distribution ───────────────────────────
    st.markdown(f"### 📚 {t('chart_dataset_title')}")
    st.caption(t("chart_dataset_caption"))

    ds_df = get_dataset_class_distribution()
    render_dataset_benchmark_chart(ds_df, height=270)

    # ── Verified Model Performance Overview ───────────────────────────────
    st.markdown(f"### 🔬 {t('nav_performance')} Overview")
    st.caption("Empirical 5-fold cross-validation performance across modalities from Notebook 9.")

    artifacts = get_model_performance_artifacts()
    cv_df = artifacts.get("cv_results")
    if cv_df is not None:
        display_cols = [c for c in ["Modalities", "Model", "Accuracy Mean", "Macro F1 Mean"] if c in cv_df.columns]
        st.dataframe(cv_df[display_cols].round(4), use_container_width=True, hide_index=True)
    else:
        st.info("Performance artifacts available in Model Performance page.")
