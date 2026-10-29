"""Dashboard page for FoodSure AI — Premium SaaS Scientific Experience."""

from __future__ import annotations

import streamlit as st
from typing import Any

from backend.analytics_service import (
    get_activity_timeline,
    get_daily_insights,
    get_dashboard_kpis,
    get_dataset_class_distribution,
    get_prediction_distribution,
)
from backend.history import get_user_history
from ui.components import (
    render_activity_chart,
    render_distribution_chart,
    status_badge,
)
from ui.i18n import get_current_language, t


def render_dashboard(user: dict[str, Any]) -> None:
    user_id = user["user_id"]
    first_name = user.get("full_name", "Researcher").split()[0]
    lang = get_current_language()

    # ── Welcome Hero Banner ────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="eyebrow">{t('dash_eyebrow')}</div>
            <h1 style="color: #0e2318 !important; font-weight: 800; margin-top: 0.15rem; margin-bottom: 0.5rem;">{t('dash_welcome', name=first_name)}</h1>
            <p style="color: #334036 !important; font-size: 1.05rem; line-height: 1.6; max-width: 680px;">
                {t('dash_hero_desc')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Quick Action Shortcuts ─────────────────────────────────────────────
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button(t("btn_analyze_now"), type="primary", use_container_width=True, key="dash_btn_analyze"):
            st.session_state["navigation"] = "Analyze Sample"
            st.rerun()
    with qa2:
        if st.button(t("btn_view_analytics"), use_container_width=True, key="dash_btn_analytics"):
            st.session_state["navigation"] = "Analytics & Insights"
            st.rerun()
    with qa3:
        if st.button(t("btn_model_perf"), use_container_width=True, key="dash_btn_perf"):
            st.session_state["navigation"] = "Model Performance"
            st.rerun()
    with qa4:
        if st.button(t("btn_explore_dataset"), use_container_width=True, key="dash_btn_ds"):
            st.session_state["navigation"] = "Dataset Explorer"
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ── Real Backend KPI Cards ─────────────────────────────────────────────
    kpis = get_dashboard_kpis(user_id)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            t("kpi_my_analyses"),
            str(kpis["total_analyses"]),
            t("kpi_today_analyses") + f": {kpis['analyses_today']}",
            help=t("kpi_my_analyses_help"),
        )
    with c2:
        st.metric(
            t("kpi_pure_rate"),
            str(kpis["pure_count"]),
            f"Adulterated: {kpis['adulterated_count']}",
            help=t("kpi_pure_rate_help"),
        )
    with c3:
        st.metric(
            t("kpi_model_accuracy"),
            "100% F1",
            "5-Fold CV (FTIR)",
            help=t("kpi_model_sub"),
        )
    with c4:
        st.metric(
            t("kpi_dataset_benchmark"),
            f"{kpis['dataset_sample_count']} Samples",
            "7 Classes (0%–9%)",
            help=t("kpi_dataset_sub"),
        )

    st.markdown("---")

    # ── Daily Scientific Insights ──────────────────────────────────────────
    st.markdown(f"### 💡 {t('section_daily_insights')}")
    insights = get_daily_insights(user_id, lang=lang)

    ins_cols = st.columns(len(insights))
    badge_colors = {
        "activity": ("#eef4fb", "#1a4d7a"),
        "benchmark": ("#fdf8ee", "#7a6010"),
        "model": ("#e8f5ee", "#1a6640"),
        "disclaimer": ("#fff5f5", "#7a1a1a"),
    }

    for idx, ins in enumerate(insights):
        bg, fg = badge_colors.get(ins.get("category", "activity"), ("#f5f5f5", "#555"))
        with ins_cols[idx]:
            st.markdown(
                f"""
                <div class="glass-card" style="height: 100%; min-height: 165px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <span style="font-size:0.75rem; font-weight:800; background:{bg}; color:{fg}; padding:0.15rem 0.55rem; border-radius:10px;">
                                {ins.get('badge', 'Insight')}
                            </span>
                        </div>
                        <h4 style="margin:0 0 0.4rem 0; font-size:1.02rem; color:var(--forest-900);">{ins['title']}</h4>
                        <p style="margin:0; font-size:0.87rem; line-height:1.55; color:var(--ink-700);">{ins['body']}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ── Analytics & Visual Charts ──────────────────────────────────────────
    st.markdown(f"### 📊 {t('section_analytics_overview')}")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown(f"#### 📈 {t('chart_activity_title')}")
        st.caption(t("chart_activity_caption"))
        timeline_df = get_activity_timeline(user_id, days=14)
        render_activity_chart(timeline_df, height=260)

    with col_chart2:
        st.markdown(f"#### 📊 {t('chart_class_dist_title')}")
        st.caption(t("chart_class_dist_caption"))
        dist_df = get_prediction_distribution(user_id)
        render_distribution_chart(dist_df, height=260)

    st.markdown("---")

    # ── Recent Analysis Activity ───────────────────────────────────────────
    st.markdown(f"### 🕒 {t('section_recent_activity')}")
    recent_history = get_user_history(user_id, limit=4)

    if not recent_history:
        st.info(t("chart_empty_history"))
    else:
        for item in recent_history:
            is_pure = "PURE" in item.get("status", "").upper()
            badge = status_badge(item.get("status", "Analyzed"), is_pure)
            est_text = f"{item['predicted_percentage']:g}%" if item.get("predicted_percentage") is not None else "N/A"
            actual_text = f" (Ground Truth: {item['actual_level']:g}%)" if item.get("actual_level") is not None else ""
            date_time = str(item.get("timestamp", ""))[:16].replace("T", " ")

            st.markdown(
                f"""
                <div style="background: var(--surface); border: 1px solid var(--border-light); border-radius: 12px; padding: 0.9rem 1.3rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Sample {item['sample_id']}</strong> • <span style="color: var(--ink-500); font-size: 0.85rem;">{date_time}</span><br>
                        <span style="font-size: 0.9rem;">Prediction: <strong>{item['predicted_class']}</strong> | Estimated: <strong>{est_text}</strong>{actual_text}</span>
                    </div>
                    <div>
                        {badge}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
