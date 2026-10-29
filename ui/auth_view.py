"""Split-screen Authentication View for FoodSure AI."""

from __future__ import annotations

import streamlit as st
from backend.auth import authenticate_user, register_user
from ui.i18n import get_current_language, set_current_language, t


def render_auth_view() -> None:
    curr_lang = get_current_language()

    # Top right language switcher on login page
    top_c1, top_c2 = st.columns([5, 1])
    with top_c2:
        lang_choice = st.selectbox(
            "Language",
            ["English", "हिन्दी"],
            index=0 if curr_lang == "en" else 1,
            label_visibility="collapsed",
            key="auth_lang_select",
        )
        new_code = "en" if lang_choice == "English" else "hi"
        if new_code != curr_lang:
            set_current_language(new_code)
            st.rerun()

    is_hi = curr_lang == "hi"

    eyebrow = "खाद्य सुरक्षा अनुसंधान प्लेटफॉर्म" if is_hi else "FOOD SAFETY RESEARCH PLATFORM"
    headline = "सुरक्षित खाद्य अनुसंधान के लिए कृत्रिम बुद्धिमत्ता • बहुमाध्यम हल्दी मिलावट जांच" if is_hi else "Intelligence for Safer Food Insights • Multimodal Turmeric Adulteration Analysis"

    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 0.5rem; margin-bottom: 2rem;">
            <div class="eyebrow">{eyebrow}</div>
            <h1 style="margin: 0; font-size: 2.5rem;">FoodSure AI</h1>
            <p style="color: var(--ink-500); font-size: 1.1rem; margin-top: 0.3rem;">
                {headline}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        left_badge = "अनुसंधान प्रोटोटाइप" if is_hi else "RESEARCH PROTOTYPE"
        left_h2 = "वैज्ञानिक हल्दी मिलावट जांच" if is_hi else "Scientific Turmeric Adulteration Screening"
        left_desc = (
            "हल्दी में गेहूं के आटे की मिलावट की पहचान और सटीक प्रतिशत मात्रा निर्धारण के लिए एटीआर-एफटीआईआर स्पेक्ट्रोस्कोपी, कैलोरीमेट्री और कंप्यूटर-विज़न फीचर्स का संयोजन।"
            if is_hi
            else "Combines ATR-FTIR spectroscopy, colorimetry, and computer-vision features to detect wheat-flour adulteration and quantify adulterant percentage with high precision."
        )
        card1_t = "संरक्षित शोध बेंचमार्क" if is_hi else "Preserved Research Benchmark"
        card1_d = (
            "7 गेहूं-आटा मिलावट स्तरों (0%, 1%, 2%, 3%, 5%, 7%, और 9%) पर 350 नियंत्रित भौतिक नमूने (50 प्रति श्रेणी)।"
            if is_hi
            else "350 controlled physical samples (50 per class) across 7 wheat-flour adulteration levels: 0%, 1%, 2%, 3%, 5%, 7%, and 9%."
        )
        card2_t = "गूगल जेमिनी एआई द्वारा संचालित" if is_hi else "Powered by Google Gemini AI"
        card2_d = (
            "स्वचालित सरल-भाषा वैज्ञानिक व्याख्याएं, साक्ष्य सारांश और प्रयोगशाला सत्यापन मार्गदर्शन।"
            if is_hi
            else "Automated plain-language interpretations, evidence summaries, and laboratory verification guidelines."
        )

        st.markdown(
            f"""
            <div class="auth-left" style="border-radius: var(--radius-xl); height: 100%; min-height: 540px; box-shadow: var(--shadow-md);">
                <div>
                    <span style="font-size: 2.2rem;">🌾🧪</span>
                    <div class="eyebrow" style="color: var(--turmeric-500); margin-top: 1rem;">{left_badge}</div>
                    <h2 style="color: #ffffff; margin-top: 0.3rem; font-size: 1.85rem; line-height: 1.2;">
                        {left_h2}
                    </h2>
                    <p style="color: #e2e8e4; font-size: 1rem; line-height: 1.6; margin-top: 1rem;">
                        {left_desc}
                    </p>
                </div>
                <div style="margin-top: 2rem;">
                    <div style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 14px; padding: 1.1rem; margin-bottom: 1rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #fdf3df; margin-bottom: 0.3rem;">🔬 {card1_t}</div>
                        <div style="font-size: 0.82rem; color: #d0ded4; line-height: 1.5;">
                            {card1_d}
                        </div>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 14px; padding: 1.1rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #fdf3df; margin-bottom: 0.3rem;">🤖 {card2_t}</div>
                        <div style="font-size: 0.82rem; color: #d0ded4; line-height: 1.5;">
                            {card2_d}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <div style="background: var(--surface); border: 1px solid var(--border-light); border-radius: var(--radius-xl); padding: 2.2rem; box-shadow: var(--shadow-md);">
            """,
            unsafe_allow_html=True,
        )

        tab_title_1 = "साइन इन" if is_hi else "Sign In"
        tab_title_2 = "खाता बनाएं" if is_hi else "Create Account"
        tab_login, tab_signup = st.tabs([tab_title_1, tab_title_2])

        with tab_login:
            st.markdown(f"### {'वापसी पर स्वागत है' if is_hi else 'Welcome Back'}")
            st.caption("अपने फूडश्योर एआई शोध कक्ष में साइन इन करें" if is_hi else "Sign in to your FoodSure AI research workspace")

            login_email = st.text_input("ईमेल पता" if is_hi else "Email Address", key="login_email", placeholder="researcher@foodsure.ai")
            login_password = st.text_input("पासवर्ड" if is_hi else "Password", type="password", key="login_password", placeholder="••••••••")

            col_sub, col_demo = st.columns([1, 1])
            with col_sub:
                btn_signin_label = "साइन इन करें" if is_hi else "Sign In"
                if st.button(btn_signin_label, type="primary", use_container_width=True, key="btn_signin"):
                    if not login_email or not login_password:
                        st.error("कृपया ईमेल और पासवर्ड दोनों प्रदान करें।" if is_hi else "Please provide both email and password.")
                    else:
                        ok, msg, user = authenticate_user(login_email, login_password)
                        if ok and user:
                            st.session_state["authenticated_user"] = user
                            st.session_state["navigation"] = "Dashboard"
                            st.success(f"{'स्वागत है' if is_hi else 'Welcome back'}, {user['full_name']}!")
                            st.rerun()
                        else:
                            st.error(msg)

            with col_demo:
                btn_demo_label = "डेमो खाता उपयोग करें" if is_hi else "Use Demo Account"
                if st.button(btn_demo_label, use_container_width=True, key="btn_demo_fill"):
                    ok, msg, user = authenticate_user("researcher@foodsure.ai", "FoodSure2026!")
                    if ok and user:
                        st.session_state["authenticated_user"] = user
                        st.session_state["navigation"] = "Dashboard"
                        st.rerun()

            st.markdown(
                f"""
                <div style="margin-top: 1.5rem; padding: 0.85rem; background: var(--surface-muted); border-radius: 10px; font-size: 0.8rem; color: var(--ink-500);">
                    <strong>{'मूल्यांकनकर्ता त्वरित पहुँच:' if is_hi else 'Evaluator Quick Access:'}</strong><br>
                    Email: <code>researcher@foodsure.ai</code><br>
                    Password: <code>FoodSure2026!</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_signup:
            st.markdown(f"### {'नया शोध खाता बनाएं' if is_hi else 'Create Research Account'}")
            st.caption("नमूना विश्लेषण चलाने और ट्रैक करने के लिए जुड़ें" if is_hi else "Join FoodSure AI to run and track multimodal sample analyses")

            reg_name = st.text_input("पूरा नाम" if is_hi else "Full Name", key="reg_name", placeholder="Dr. Jane Doe")
            reg_email = st.text_input("ईमेल पता" if is_hi else "Email Address", key="reg_email", placeholder="jane@institute.org")
            reg_password = st.text_input("पासवर्ड (कम से कम 8 अक्षर)" if is_hi else "Password (min 8 chars with uppercase, lowercase, digit)", type="password", key="reg_password", placeholder="••••••••")
            reg_confirm = st.text_input("पासवर्ड की पुष्टि करें" if is_hi else "Confirm Password", type="password", key="reg_confirm", placeholder="••••••••")

            btn_create_label = "खाता बनाएं" if is_hi else "Create Account"
            if st.button(btn_create_label, type="primary", use_container_width=True, key="btn_signup"):
                if not reg_name or not reg_email or not reg_password:
                    st.error("सभी फ़ील्ड आवश्यक हैं।" if is_hi else "All fields are required.")
                elif reg_password != reg_confirm:
                    st.error("पासवर्ड मेल नहीं खाते।" if is_hi else "Passwords do not match.")
                else:
                    ok, msg, user = register_user(reg_email, reg_password, reg_name)
                    if ok and user:
                        st.session_state["authenticated_user"] = user
                        st.session_state["navigation"] = "Dashboard"
                        st.success("खाता सफलतापूर्वक बनाया गया!" if is_hi else "Account created successfully! Redirecting...")
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)
