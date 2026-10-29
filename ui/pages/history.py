"""Analysis history page for FoodSure AI — Bilingual & Account Isolated."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backend.history import clear_user_history, delete_analysis, get_user_history
from ui.components import page_header, status_badge
from ui.i18n import get_current_language, t


def render_history_page(user: dict) -> None:
    is_hi = get_current_language() == "hi"

    eyebrow = "सुरक्षित रिकॉर्ड्स" if is_hi else "PERSISTENT RECORDS"
    title = "विश्लेषण इतिहास" if is_hi else "Analysis History"
    desc = (
        "अपने ऐतिहासिक नमूना जांच परीक्षणों को ब्राउज़, निरीक्षण और निर्यात करें। रिकॉर्ड आपके खाते में सुरक्षित रूप से पृथक हैं।"
        if is_hi
        else "Browse, inspect, and export your historical sample screening runs. Records are securely isolated to your account."
    )

    page_header(eyebrow, title, desc)

    history = get_user_history(user["user_id"], limit=150)

    if not history:
        st.info("आपने अभी तक कोई विश्लेषण नहीं चलाया है। परीक्षण शुरू करने के लिए 'नमूने का विश्लेषण' पर जाएं।" if is_hi else "You haven't run any analyses yet. Visit the 'Analyze Sample' page to begin testing samples.")
        return

    # Top stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("kpi_my_analyses"), len(history))
    with c2:
        pure_count = sum(1 for h in history if "PURE" in h["status"].upper())
        st.metric(t("kpi_pure_rate"), pure_count)
    with c3:
        adulterated_count = len(history) - pure_count
        st.metric(t("kpi_adulterated_count"), adulterated_count)
    with c4:
        gemini_count = sum(1 for h in history if "gemini" in h.get("analysis_mode", "").lower())
        st.metric("जेमिनी रिपोर्ट" if is_hi else "Gemini Reports", gemini_count)

    st.markdown("---")

    col_search, col_filter, col_action = st.columns([1.5, 1.2, 1])
    with col_search:
        search_term = st.text_input("🔍 नमूना आईडी द्वारा खोजें" if is_hi else "🔍 Search by Sample ID", placeholder="e.g. T3S12")
    with col_filter:
        status_opts = ["सभी स्थितियां", "शुद्ध हल्दी", "मिलावटी"] if is_hi else ["All Statuses", "Pure Turmeric", "Adulterated"]
        status_filter = st.selectbox("स्थिति अनुसार फ़िल्टर" if is_hi else "Filter by Status", status_opts)
    with col_action:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ इतिहास साफ करें" if is_hi else "🗑️ Clear My History", type="secondary", use_container_width=True):
            if clear_user_history(user["user_id"]):
                st.success("इतिहास साफ हो गया।" if is_hi else "Analysis history cleared.")
                st.rerun()

    # Filter records
    filtered = []
    for item in history:
        if search_term and search_term.lower() not in item["sample_id"].lower():
            continue
        if status_filter in ("Pure Turmeric", "शुद्ध हल्दी") and "PURE" not in item["status"].upper():
            continue
        if status_filter in ("Adulterated", "मिलावटी") and "ADULTERATED" not in item["status"].upper():
            continue
        filtered.append(item)

    st.caption(f"{len(filtered)} / {len(history)} रिकॉर्ड प्रदर्शित" if is_hi else f"Showing {len(filtered)} of {len(history)} records")

    for item in filtered:
        with st.container():
            is_pure = "PURE" in item["status"].upper()
            badge = status_badge(item["status"], is_pure)
            est_str = f"{item['predicted_percentage']:g}%" if item.get("predicted_percentage") is not None else "N/A"
            actual_str = f" | Truth: {item['actual_level']:g}%" if item.get("actual_level") is not None else ""

            with st.expander(f"Sample {item['sample_id']} • {item['predicted_class']} ({item['timestamp'][:16].replace('T', ' ')})", expanded=False):
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f"**Sample ID:** `{item['sample_id']}`")
                    st.markdown(f"**{'इनपुट स्रोत' if is_hi else 'Input Source'}:** {item['input_source']}")
                    st.markdown(f"**{'माध्यम' if is_hi else 'Modality'}:** {item['modality']}")
                    st.markdown(f"**{'अनुमानित श्रेणी' if is_hi else 'Predicted Class'}:** **{item['predicted_class']}**")
                    st.markdown(f"**{'मात्रात्मक अनुमान' if is_hi else 'Regression Estimate'}:** **{est_str}**{actual_str}")
                    st.markdown(f"**{'एआई सारांश' if is_hi else 'AI Analyst Summary'}:** {item.get('summary', 'N/A')}")

                with col_right:
                    st.markdown(f"**{'स्थिति' if is_hi else 'Status'}:** {badge}", unsafe_allow_html=True)
                    st.markdown(f"**{'एआई इंजन' if is_hi else 'AI Engine'}:** `{item.get('analysis_mode', 'N/A')}`")
                    st.markdown(f"**ID:** `{item['analysis_id'][:8]}...`")

                    if st.button("एंट्री हटाएं" if is_hi else "Delete Entry", key=f"del_{item['analysis_id']}", use_container_width=True):
                        delete_analysis(item["analysis_id"], user["user_id"])
                        st.success("हटा दिया गया।" if is_hi else "Deleted record.")
                        st.rerun()

    # Export all history to CSV
    st.markdown("---")
    df_export = pd.DataFrame(filtered)
    csv_bytes = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 इतिहास CSV में डाउनलोड करें" if is_hi else "📥 Export Analysis History to CSV",
        data=csv_bytes,
        file_name="FoodSure_Analysis_History.csv",
        mime="text/csv",
        use_container_width=False,
    )
