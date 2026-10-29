"""Notification Center view for FoodSure AI."""

from __future__ import annotations

import streamlit as st
from typing import Any

from backend.notifications import (
    clear_user_notifications,
    delete_notification,
    get_unread_count,
    get_user_notifications,
    mark_all_as_read,
    mark_as_read,
)
from ui.components import page_header
from ui.i18n import t


def render_notifications_page(user: dict[str, Any]) -> None:
    user_id = user["user_id"]

    page_header(
        t("notif_header_title"),
        t("notif_title"),
        t("notif_desc"),
    )

    unread_count = get_unread_count(user_id)
    all_notifs = get_user_notifications(user_id, limit=100)
    unread_notifs = [n for n in all_notifs if not n["is_read"]]

    # Header actions
    act_col1, act_col2, act_col3 = st.columns([1.5, 1, 1])
    with act_col2:
        if st.button(t("btn_mark_all_read"), use_container_width=True, key="btn_mark_all"):
            mark_all_as_read(user_id)
            st.rerun()
    with act_col3:
        if st.button(t("btn_clear_all_notif"), use_container_width=True, key="btn_clear_all"):
            clear_user_notifications(user_id)
            st.rerun()

    tab_all, tab_unread = st.tabs([
        t("tab_all_notifications"),
        t("tab_unread_only", count=unread_count),
    ])

    def render_items(items: list[dict[str, Any]], tab_name: str) -> None:
        if not items:
            st.info(t("no_notifications"))
            return

        for item in items:
            notif_id = item["id"]
            is_read = bool(item["is_read"])
            category = item.get("category", "info").lower()
            created_at = str(item.get("created_at", ""))[:16].replace("T", " ")

            badge_style = {
                "success": "background:#e8f5ee; color:#1a6640; border:1px solid #b8ddc8;",
                "warning": "background:#fdf8ee; color:#7a6010; border:1px solid #e8c96a;",
                "info": "background:#eef4fb; color:#1a4d7a; border:1px solid #b8d4f0;",
            }.get(category, "background:#f5f5f5; color:#555;")

            card_border = "border:1px solid var(--border-light);" if is_read else "border:2px solid #d49726; background:#fffdfa;"

            st.markdown(
                f"""
                <div style="border-radius:14px; padding:1.1rem 1.4rem; margin-bottom:0.75rem; {card_border}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span style="border-radius:12px; padding:0.15rem 0.55rem; font-size:0.72rem; font-weight:800; text-transform:uppercase; {badge_style}">
                                {category}
                            </span>
                            <span style="font-size:0.8rem; color:var(--ink-500); margin-left:0.6rem;">{created_at} UTC</span>
                            <div style="font-size:1.05rem; font-weight:700; color:var(--forest-900); margin-top:0.4rem;">
                                {item['title']}
                            </div>
                            <div style="font-size:0.92rem; color:var(--forest-800); line-height:1.6; margin-top:0.25rem;">
                                {item['message']}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn1, col_btn2 = st.columns([1, 5])
            with col_btn1:
                if not is_read:
                    if st.button(t("btn_mark_read"), key=f"read_{tab_name}_{notif_id}"):
                        mark_as_read(notif_id, user_id)
                        st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{tab_name}_{notif_id}", help="Delete notification"):
                        delete_notification(notif_id, user_id)
                        st.rerun()

    with tab_all:
        render_items(all_notifs, "all")

    with tab_unread:
        render_items(unread_notifs, "unread")
