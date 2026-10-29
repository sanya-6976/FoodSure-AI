"""Reusable UI components and Navigation Bar for FoodSure AI."""

from __future__ import annotations

from typing import Any
import altair as alt
import pandas as pd
import streamlit as st

from backend.notifications import get_unread_count
from backend.service import get_dataset_sample_ids
from backend.settings import get_user_settings, save_user_settings
from ui.i18n import get_current_language, set_current_language, t


def page_header(eyebrow: str, title: str, description: str | None = None) -> None:
    """Render a unified page header with guaranteed high contrast and rich brand typography."""
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="page-title" style="color: #0e2318 !important; font-size: 2.3rem; font-weight: 800; margin-top: 0; margin-bottom: 0.35rem; letter-spacing: -0.025em;">{title}</h1>',
        unsafe_allow_html=True,
    )
    if description:
        st.markdown(
            f'<p class="page-desc" style="color: #455749 !important; font-size: 1.05rem; margin-top: -0.1rem; margin-bottom: 1.4rem; line-height: 1.55;">{description}</p>',
            unsafe_allow_html=True,
        )


def status_badge(status_text: str, is_pure: bool | None = None) -> str:
    """Render an accessible, color-coded status badge."""
    if is_pure is True or "PURE" in status_text.upper():
        cls = "pill-pure"
        icon = "✓ "
    elif is_pure is False or "ADULTERATED" in status_text.upper():
        cls = "pill-adulterated"
        icon = "⚠ "
    else:
        cls = "pill-gold"
        icon = "• "
    return f'<span class="metric-pill {cls}">{icon}{status_text}</span>'


def render_spectrum_chart(
    wavenumbers: list[float],
    absorbance: list[float],
    title: str = "ATR-FTIR Spectrum",
) -> None:
    """Render an ATR-FTIR absorbance spectrum with scientific theme and inverted wavenumber axis."""
    if not wavenumbers or not absorbance or len(wavenumbers) != len(absorbance):
        st.info("Spectral waveform points not available for this sample.")
        return

    df = pd.DataFrame({"Wavenumber": wavenumbers, "Absorbance": absorbance})

    st.markdown(f"#### 🔬 {title}")
    st.caption("Spectral absorbance across infrared range (4000 cm⁻¹ – 650 cm⁻¹)")

    # Standard FTIR convention: wavenumbers decrease from left to right (4000 -> 650)
    chart = (
        alt.Chart(df)
        .mark_line(color="#1c4933", strokeWidth=2)
        .encode(
            x=alt.X(
                "Wavenumber:Q",
                scale=alt.Scale(reverse=True),
                axis=alt.Axis(
                    title="Wavenumber (cm⁻¹)",
                    titleColor="#18201a",
                    labelColor="#334036",
                    gridColor="#e8ebe2",
                    labelFont="Plus Jakarta Sans",
                    titleFont="Plus Jakarta Sans",
                ),
            ),
            y=alt.Y(
                "Absorbance:Q",
                axis=alt.Axis(
                    title="Absorbance (AU)",
                    titleColor="#18201a",
                    labelColor="#334036",
                    gridColor="#e8ebe2",
                    labelFont="Plus Jakarta Sans",
                    titleFont="Plus Jakarta Sans",
                ),
            ),
            tooltip=[
                alt.Tooltip("Wavenumber:Q", format=".1f", title="Wavenumber (cm⁻¹)"),
                alt.Tooltip("Absorbance:Q", format=".4f", title="Absorbance"),
            ],
        )
        .properties(height=280)
        .configure_view(stroke=None, fill="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_activity_chart(timeline_df: pd.DataFrame, height: int = 250) -> None:
    """Render an activity timeline chart using light SaaS styling with soft area fill."""
    if timeline_df.empty or "Date" not in timeline_df.columns:
        st.info(t("chart_empty_history"))
        return

    # Base line
    line = (
        alt.Chart(timeline_df)
        .mark_line(color="#1c4933", strokeWidth=2.5, point=True)
        .encode(
            x=alt.X(
                "Date:N",
                axis=alt.Axis(
                    title=None,
                    labelColor="#334036",
                    labelAngle=-30 if len(timeline_df) > 8 else 0,
                    labelFont="Plus Jakarta Sans",
                    grid=False,
                ),
            ),
            y=alt.Y(
                "Analyses:Q",
                axis=alt.Axis(
                    title=t("nav_analyze"),
                    titleColor="#18201a",
                    labelColor="#334036",
                    labelFont="Plus Jakarta Sans",
                    gridColor="#eef1e9",
                    tickMinStep=1,
                ),
            ),
            tooltip=[
                alt.Tooltip("Date:N", title=t("filter_date_range")),
                alt.Tooltip("Analyses:Q", title=t("nav_analyze")),
            ],
        )
    )

    # Soft area fill underneath
    area = (
        alt.Chart(timeline_df)
        .mark_area(opacity=0.15, color="#1c4933")
        .encode(
            x="Date:N",
            y="Analyses:Q",
        )
    )

    chart = (
        (area + line)
        .properties(height=height)
        .configure_view(stroke=None, fill="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_distribution_chart(dist_df: pd.DataFrame, height: int = 250) -> None:
    """Render prediction distribution with emerald pure bars and turmeric gold adulterated bars."""
    if dist_df.empty or dist_df["Count"].sum() == 0:
        st.info(t("chart_empty_history"))
        return

    # Distinctive color condition: Pure (0%) is emerald, Adulterated (1%-9%) is turmeric gold
    bars = (
        alt.Chart(dist_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(
                "Adulteration Class:N",
                axis=alt.Axis(
                    title=None,
                    labelColor="#334036",
                    labelAngle=0,
                    labelFont="Plus Jakarta Sans",
                    grid=False,
                ),
            ),
            y=alt.Y(
                "Count:Q",
                axis=alt.Axis(
                    title="Sample Count",
                    titleColor="#18201a",
                    labelColor="#334036",
                    labelFont="Plus Jakarta Sans",
                    gridColor="#eef1e9",
                    tickMinStep=1,
                ),
            ),
            color=alt.condition(
                alt.datum["Adulteration Class"] == "0%",
                alt.value("#1c4933"),  # Scientific emerald for Pure
                alt.value("#d49726"),  # Turmeric gold for Adulterated
            ),
            tooltip=[
                alt.Tooltip("Adulteration Class:N", title="Class"),
                alt.Tooltip("Count:Q", title="Analyses"),
            ],
        )
    )

    # Data value labels on top of bars
    text = bars.mark_text(
        align="center",
        baseline="bottom",
        dy=-4,
        color="#18201a",
        font="Plus Jakarta Sans",
        fontWeight="bold",
        fontSize=12,
    ).encode(
        text="Count:Q"
    )

    chart = (
        (bars + text)
        .properties(height=height)
        .configure_view(stroke=None, fill="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_dataset_benchmark_chart(ds_df: pd.DataFrame, height: int = 260) -> None:
    """Render 350-sample research benchmark class distribution with training vs holdout splits."""
    if ds_df.empty:
        st.info("Dataset statistics not available.")
        return

    # Reshape for Altair grouped/stacked visualization
    id_vars = ["Adulteration Level"]
    value_vars = [c for c in ["Training Split (280)", "Holdout Split (70)"] if c in ds_df.columns]
    melted = pd.melt(
        ds_df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="Split",
        value_name="Samples",
    )

    chart = (
        alt.Chart(melted)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Adulteration Level:N",
                axis=alt.Axis(
                    title="Concentration Level",
                    labelColor="#334036",
                    labelAngle=0,
                    labelFont="Plus Jakarta Sans",
                    grid=False,
                ),
            ),
            y=alt.Y(
                "Samples:Q",
                axis=alt.Axis(
                    title="Samples Count",
                    labelColor="#334036",
                    labelFont="Plus Jakarta Sans",
                    gridColor="#eef1e9",
                ),
            ),
            color=alt.Color(
                "Split:N",
                scale=alt.Scale(
                    domain=["Training Split (280)", "Holdout Split (70)"],
                    range=["#1c4933", "#d49726"],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="top-right",
                    labelColor="#334036",
                    labelFont="Plus Jakarta Sans",
                ),
            ),
            tooltip=["Adulteration Level:N", "Split:N", "Samples:Q"],
        )
        .properties(height=height)
        .configure_view(stroke=None, fill="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_top_navbar(current_page: str, user: dict[str, Any]) -> None:
    """Render the premium top navigation bar with search, language, notifications, and settings."""
    user_id = user.get("user_id", "")
    unread = get_unread_count(user_id) if user_id else 0
    current_lang = get_current_language()

    # Navbar container with dedicated SaaS styling
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(
        [2.3, 2.1, 1.1, 0.75, 0.55],
        gap="small",
    )

    with nav_col1:
        # Breadcrumbs
        translated_page = t(
            f"nav_{current_page.lower().replace(' ', '_').replace('&', '').replace('__', '_')}",
            current_page,
        )
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.45rem; padding-top:0.35rem;">
                <span style="color:#1c4933; font-weight:800; font-size:0.9rem; letter-spacing:0.02em;">FoodSure AI</span>
                <span style="color:#93a497; font-weight:600;">/</span>
                <span style="color:#0e2318; font-weight:800; font-size:1.08rem; letter-spacing:-0.01em;">{translated_page}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_col2:
        # Global Sample Search input
        search_query = st.text_input(
            "Global Search",
            placeholder=t("search_placeholder"),
            label_visibility="collapsed",
            key="navbar_global_search",
        )
        if search_query and search_query.strip():
            clean_q = search_query.strip().upper()
            valid_ids = get_dataset_sample_ids()
            if clean_q in valid_ids:
                st.session_state["preselected_sample_id"] = clean_q
                st.session_state["navigation"] = "Analyze Sample"
                st.toast(t("sample_found", sample_id=clean_q), icon="🔬")
                st.rerun()
            else:
                st.warning(t("sample_not_found", sample_id=clean_q))

    with nav_col3:
        # Language Selector
        lang_idx = 0 if current_lang == "en" else 1
        new_lang_choice = st.selectbox(
            "Language",
            options=["English", "हिन्दी"],
            index=lang_idx,
            label_visibility="collapsed",
            key="navbar_lang_selector",
        )
        selected_code = "en" if new_lang_choice == "English" else "hi"
        if selected_code != current_lang:
            set_current_language(selected_code)
            if user_id:
                try:
                    settings = get_user_settings(user_id)
                    settings["language"] = selected_code
                    save_user_settings(user_id, settings)
                except Exception:
                    pass
            st.rerun()

    with nav_col4:
        # Notification Bell with unread badge
        bell_label = f"🔔 {unread}" if unread > 0 else "🔔"
        bell_help = t("unread_notifications", count=unread) if unread > 0 else t("no_unread")
        if st.button(bell_label, help=bell_help, use_container_width=True, key="navbar_bell_btn"):
            st.session_state["navigation"] = "Notifications"
            st.rerun()

    with nav_col5:
        # Settings shortcut
        if st.button("⚙️", help=t("nav_settings"), use_container_width=True, key="navbar_settings_btn"):
            st.session_state["navigation"] = "Settings"
            st.rerun()

    st.markdown(
        "<div style='border-bottom: 1px solid #e2e6dc; margin-top:0.4rem; margin-bottom:1.5rem;'></div>",
        unsafe_allow_html=True,
    )
