"""FoodSure AI — Production Web Application.

Multimodal AI for Turmeric Adulteration Detection & Quantification.
"""

from __future__ import annotations

import streamlit as st

from backend.notifications import get_unread_count
from backend.settings import get_user_settings
from ui.auth_view import render_auth_view
from ui.components import render_top_navbar
from ui.i18n import get_current_language, set_current_language, t
from ui.pages.about import render_about_page
from ui.pages.analytics import render_analytics_page
from ui.pages.analyze import render_analyze_page
from ui.pages.dashboard import render_dashboard
from ui.pages.dataset_explorer import render_dataset_explorer
from ui.pages.history import render_history_page
from ui.pages.how_it_works import render_how_it_works_page
from ui.pages.notifications import render_notifications_page
from ui.pages.performance import render_performance_page
from ui.pages.settings import render_settings_page
from ui.styles import apply_styles

NAV_CANONICAL = (
    "Dashboard",
    "Analyze Sample",
    "Analysis History",
    "Analytics & Insights",
    "Model Performance",
    "Dataset Explorer",
    "Notifications",
    "How It Works",
    "Settings",
    "About",
)

st.set_page_config(
    page_title="FoodSure AI | Turmeric Adulteration Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply scientific typography, cards, and theme
apply_styles()

# Initialize session state keys
if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None
if "navigation" not in st.session_state:
    st.session_state["navigation"] = "Dashboard"
if "latest_analysis" not in st.session_state:
    st.session_state["latest_analysis"] = None
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = "en"

# Authentication Gatekeeper
user = st.session_state.get("authenticated_user")
if not user:
    render_auth_view()
    st.stop()

# Synchronize user language from stored user settings if present
user_id = user.get("user_id", "")
if "user_settings_synced" not in st.session_state and user_id:
    try:
        user_cfg = get_user_settings(user_id)
        if user_cfg.get("language") in ("en", "hi"):
            st.session_state["ui_language"] = user_cfg["language"]
        st.session_state["user_settings_synced"] = True
    except Exception:
        pass

unread_count = get_unread_count(user_id) if user_id else 0

# Authenticated Sidebar
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0.2rem 1.2rem 0.2rem; border-bottom: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 1.2rem;">
            <div style="font-size: 1.8rem; display: flex; align-items: center; gap: 0.5rem;">
                <span>🔬</span> <strong style="color: #ffffff; font-size: 1.45rem;">FoodSure AI</strong>
            </div>
            <div style="font-size: 0.75rem; color: #a4c2b0; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-top: 0.3rem;">
                Turmeric Adulteration Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # User Profile Pill
    full_name = user.get("full_name", "Researcher")
    email = user.get("email", "")
    st.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 0.75rem 0.9rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.75rem; color: #d49726; font-weight: 800; text-transform: uppercase;">{t('active_researcher')}</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{full_name}</div>
            <div style="font-size: 0.75rem; color: #b7cebf; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{email}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_nav = st.session_state.get("navigation", "Dashboard")
    if current_nav not in NAV_CANONICAL:
        current_nav = "Dashboard"

    # Bilingual labels for sidebar
    def get_sidebar_label(nav_key: str) -> str:
        key_map = {
            "Dashboard": "nav_dashboard",
            "Analyze Sample": "nav_analyze",
            "Analysis History": "nav_history",
            "Analytics & Insights": "nav_analytics",
            "Model Performance": "nav_performance",
            "Dataset Explorer": "nav_dataset",
            "Notifications": "nav_notifications",
            "How It Works": "nav_how_it_works",
            "Settings": "nav_settings",
            "About": "nav_about",
        }
        base_label = t(key_map.get(nav_key, "nav_dashboard"), nav_key)
        if nav_key == "Notifications" and unread_count > 0:
            return f"🔔 {base_label} ({unread_count})"
        return base_label

    sidebar_options = list(NAV_CANONICAL)
    sidebar_display_labels = [get_sidebar_label(k) for k in sidebar_options]
    active_idx = sidebar_options.index(current_nav)

    selected_display = st.radio(
        "Navigation Menu",
        options=sidebar_display_labels,
        index=active_idx,
        label_visibility="collapsed",
    )
    # Map back to canonical key
    st.session_state["navigation"] = sidebar_options[sidebar_display_labels.index(selected_display)]

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # System Status Badges
    st.markdown(
        f"""
        <div style="font-size: 0.72rem; color: #a4c2b0; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; margin-bottom: 0.6rem;">
            {t('system_status')}
        </div>
        <div style="font-size: 0.8rem; line-height: 1.7; color: #e2ede5;">
            <div>✓ {t('status_model')}</div>
            <div>✓ {t('status_ai')}</div>
            <div>✓ {t('status_dataset')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    if st.button(f"🚪 {t('sign_out')}", use_container_width=True, type="secondary"):
        st.session_state["authenticated_user"] = None
        st.session_state["latest_analysis"] = None
        st.session_state["navigation"] = "Dashboard"
        st.rerun()

# ── Render Premium Top Navbar ──────────────────────────────────────────────
page = st.session_state.get("navigation", "Dashboard")
render_top_navbar(page, user)

# ── Page Routing ───────────────────────────────────────────────────────────
if page == "Dashboard":
    render_dashboard(user)
elif page == "Analyze Sample":
    render_analyze_page(user)
elif page == "Analysis History":
    render_history_page(user)
elif page == "Analytics & Insights":
    render_analytics_page(user)
elif page == "Model Performance":
    render_performance_page()
elif page == "Dataset Explorer":
    render_dataset_explorer()
elif page == "Notifications":
    render_notifications_page(user)
elif page == "How It Works":
    render_how_it_works_page()
elif page == "Settings":
    render_settings_page(user)
elif page == "About":
    render_about_page()
else:
    render_dashboard(user)
