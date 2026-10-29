"""Settings and Preferences view for FoodSure AI."""

from __future__ import annotations

import streamlit as st
from typing import Any

from backend.settings import get_user_settings, save_user_settings
from ui.components import page_header
from ui.i18n import get_current_language, set_current_language, t


def render_settings_page(user: dict[str, Any]) -> None:
    user_id = user["user_id"]

    page_header(
        t("settings_header_title"),
        t("settings_title"),
        t("settings_desc"),
    )

    settings = get_user_settings(user_id)

    with st.form("user_settings_form"):
        # 1. Language & Localization
        st.markdown(f"### 🌐 {t('section_appearance')}")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            curr_ui = settings.get("language", get_current_language())
            ui_idx = 0 if curr_ui == "en" else 1
            selected_ui_lang = st.selectbox(
                t("pref_ui_language"),
                options=["English", "हिन्दी"],
                index=ui_idx,
                help="Sets the language for buttons, navigation, charts, and interface text.",
            )
        with col_l2:
            curr_exp = settings.get("explanation_lang", "en")
            exp_idx = 0 if curr_exp == "en" else 1
            selected_exp_lang = st.selectbox(
                t("pref_explanation_lang"),
                options=["English", "हिन्दी"],
                index=exp_idx,
                help="Sets the default language used when generating AI scientific explanations.",
            )

        st.markdown("---")

        # 2. Analysis Preferences
        st.markdown(f"### 🔬 {t('section_analysis_pref')}")
        curr_depth = settings.get("explanation_depth", "detailed")
        depth_options = ["quick", "detailed", "technical"]
        depth_labels = [
            t("depth_quick"),
            t("depth_detailed"),
            t("depth_technical"),
        ]
        depth_idx = depth_options.index(curr_depth) if curr_depth in depth_options else 1
        selected_depth_label = st.radio(
            t("pref_default_depth"),
            options=depth_labels,
            index=depth_idx,
        )
        selected_depth = depth_options[depth_labels.index(selected_depth_label)]

        st.markdown("---")

        # 3. Notification Preferences
        st.markdown(f"### 🔔 {t('section_notif_pref')}")
        notify_analysis = st.checkbox(
            t("pref_notify_analysis"),
            value=bool(settings.get("notify_analysis", 1)),
        )
        notify_insights = st.checkbox(
            t("pref_notify_insights"),
            value=bool(settings.get("notify_insights", 1)),
        )

        st.markdown("---")

        # 4. Account Profile (Read-Only overview)
        st.markdown(f"### 👤 {t('section_account_info')}")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            st.text_input(t("account_name"), value=user.get("full_name", "Researcher"), disabled=True)
        with col_a2:
            st.text_input(t("account_email"), value=user.get("email", ""), disabled=True)
        with col_a3:
            st.text_input(t("account_role"), value=user.get("role", "researcher").title(), disabled=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button(t("btn_save_settings"), type="primary", use_container_width=True)

        if submitted:
            new_lang_code = "en" if selected_ui_lang == "English" else "hi"
            new_exp_code = "en" if selected_exp_lang == "English" else "hi"

            updated_data = {
                "language": new_lang_code,
                "explanation_lang": new_exp_code,
                "explanation_depth": selected_depth,
                "notify_analysis": 1 if notify_analysis else 0,
                "notify_insights": 1 if notify_insights else 0,
                "theme": settings.get("theme", "light"),
            }
            save_user_settings(user_id, updated_data)
            set_current_language(new_lang_code)
            st.success(t("settings_saved"))
            st.rerun()
