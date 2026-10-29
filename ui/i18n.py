"""Bilingual Internationalization (i18n) Engine for FoodSure AI.

Supports English (en) and Hindi (hi) across all pages, navigation, headings,
metrics, buttons, alerts, notifications, and settings.
"""

from __future__ import annotations

import streamlit as st
from typing import Any

# ---------------------------------------------------------------------------
# Central Translation Dictionary
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Application Brand & Sidebar ───────────────────────────────────────
    "app_title": {
        "en": "FoodSure AI | Turmeric Adulteration Platform",
        "hi": "फूडश्योर एआई | हल्दी मिलावट जांच प्लेटफॉर्म",
    },
    "brand_subtitle": {
        "en": "Turmeric Adulteration Platform",
        "hi": "हल्दी मिलावट जांच प्लेटफॉर्म",
    },
    "active_researcher": {
        "en": "ACTIVE RESEARCHER",
        "hi": "सक्रिय शोधकर्ता",
    },
    "system_status": {
        "en": "SYSTEM STATUS",
        "hi": "सिस्टम स्थिति",
    },
    "status_model": {
        "en": "Model: FTIR (v1.0)",
        "hi": "मॉडल: एफटीआईआर (v1.0)",
    },
    "status_ai": {
        "en": "AI Analyst: Gemini 3.5",
        "hi": "एआई विश्लेषक: जेमिनी 3.5",
    },
    "status_dataset": {
        "en": "Dataset: 350 Samples",
        "hi": "डेटासेट: 350 नमूने",
    },
    "sign_out": {
        "en": "Sign Out",
        "hi": "साइन आउट",
    },

    # ── Navigation Items ──────────────────────────────────────────────────
    "nav_dashboard": {
        "en": "Dashboard",
        "hi": "डैशबोर्ड",
    },
    "nav_analyze": {
        "en": "Analyze Sample",
        "hi": "नमूने का विश्लेषण",
    },
    "nav_history": {
        "en": "Analysis History",
        "hi": "विश्लेषण इतिहास",
    },
    "nav_analytics": {
        "en": "Analytics & Insights",
        "hi": "एनालिटिक्स और इनसाइट्स",
    },
    "nav_performance": {
        "en": "Model Performance",
        "hi": "मॉडल प्रदर्शन",
    },
    "nav_dataset": {
        "en": "Dataset Explorer",
        "hi": "डेटासेट एक्सप्लोरर",
    },
    "nav_notifications": {
        "en": "Notifications",
        "hi": "सूचनाएँ",
    },
    "nav_how_it_works": {
        "en": "How It Works",
        "hi": "यह कैसे काम करता है",
    },
    "nav_settings": {
        "en": "Settings",
        "hi": "सेटिंग्स",
    },
    "nav_about": {
        "en": "About",
        "hi": "परिचय",
    },

    # ── Top Navbar ────────────────────────────────────────────────────────
    "search_placeholder": {
        "en": "Quick Jump to Sample ID (e.g. T3S15)...",
        "hi": "त्वरित नमूना खोज (जैसे T3S15)...",
    },
    "search_button": {
        "en": "Search",
        "hi": "खोजें",
    },
    "sample_not_found": {
        "en": "Sample ID '{sample_id}' not found in the dataset.",
        "hi": "नमूना आईडी '{sample_id}' डेटासेट में नहीं मिला।",
    },
    "sample_found": {
        "en": "Sample '{sample_id}' loaded. Opening Analysis Workspace...",
        "hi": "नमूना '{sample_id}' लोड हो गया। विश्लेषण कक्ष खोला जा रहा है...",
    },
    "unread_notifications": {
        "en": "{count} unread notifications",
        "hi": "{count} अपठित सूचनाएँ",
    },
    "no_unread": {
        "en": "No unread notifications",
        "hi": "कोई नई सूचना नहीं",
    },

    # ── Dashboard Page ────────────────────────────────────────────────────
    "dash_eyebrow": {
        "en": "INTELLIGENCE FOR SAFER FOOD INSIGHTS",
        "hi": "सुरक्षित खाद्य अनुसंधान के लिए कृत्रिम बुद्धिमत्ता",
    },
    "dash_welcome": {
        "en": "Welcome, {name} 👋",
        "hi": "स्वागत है, {name} 👋",
    },
    "dash_hero_desc": {
        "en": "FoodSure AI provides machine learning detection and continuous quantification of turmeric adulteration using ATR-FTIR spectroscopy and multimodal feature evaluation.",
        "hi": "फूडश्योर एआई एटीआर-एफटीआईआर स्पेक्ट्रोस्कोपी और मल्टीमॉडल फीचर मूल्यांकन का उपयोग करके हल्दी मिलावट की पहचान और निरंतर मात्रात्मक विश्लेषण प्रदान करता है।",
    },
    "btn_analyze_now": {
        "en": "🔬 Analyze New Sample",
        "hi": "🔬 नया नमूना जांचें",
    },
    "btn_view_analytics": {
        "en": "📊 View Analytics",
        "hi": "📊 एनालिटिक्स देखें",
    },
    "btn_model_perf": {
        "en": "📈 Model Performance",
        "hi": "📈 मॉडल प्रदर्शन",
    },
    "btn_explore_dataset": {
        "en": "📚 Dataset Explorer",
        "hi": "📚 डेटासेट देखें",
    },

    # KPI Labels
    "kpi_my_analyses": {
        "en": "My Analyses",
        "hi": "मेरे कुल विश्लेषण",
    },
    "kpi_my_analyses_help": {
        "en": "Total sample screening runs performed by your account",
        "hi": "आपके खाते द्वारा की गई कुल नमूनों की जांच",
    },
    "kpi_today_analyses": {
        "en": "Analyses Today",
        "hi": "आज के विश्लेषण",
    },
    "kpi_today_help": {
        "en": "Analyses conducted during today's session",
        "hi": "आज के सत्र में की गई कुल जांचें",
    },
    "kpi_pure_rate": {
        "en": "Pure Turmeric Identified",
        "hi": "शुद्ध हल्दी के नमूने",
    },
    "kpi_pure_rate_help": {
        "en": "Samples classified as 0% unadulterated",
        "hi": "0% शुद्ध पाए गए नमूनों की संख्या",
    },
    "kpi_adulterated_count": {
        "en": "Adulterated Samples",
        "hi": "मिलावटी नमूने",
    },
    "kpi_adulterated_help": {
        "en": "Samples with detected wheat flour adulteration (1%–9%)",
        "hi": "गेहूं के आटे की मिलावट (1%–9%) वाले नमूने",
    },
    "kpi_dataset_benchmark": {
        "en": "Benchmark Dataset",
        "hi": "मानक डेटासेट",
    },
    "kpi_dataset_sub": {
        "en": "350 Samples • 7 Classes",
        "hi": "350 नमूने • 7 श्रेणियां",
    },
    "kpi_model_accuracy": {
        "en": "FTIR CV Accuracy",
        "hi": "एफटीआईआर सीवी सटीकता",
    },
    "kpi_model_sub": {
        "en": "100% Macro F1 (5-Fold CV)",
        "hi": "100% मैक्रो F1 (5-फोल्ड सीवी)",
    },

    # Section Headers
    "section_analytics_overview": {
        "en": "Analytics Overview",
        "hi": "एनालिटिक्स अवलोकन",
    },
    "section_daily_insights": {
        "en": "Daily Scientific Insights",
        "hi": "दैनिक वैज्ञानिक इनसाइट्स",
    },
    "section_recent_activity": {
        "en": "Recent Activity",
        "hi": "हाल की गतिविधियां",
    },
    "section_modalities": {
        "en": "Modality Capabilities & Deployment Status",
        "hi": "माध्यम क्षमताएं और डिप्लॉयमेंट स्थिति",
    },

    # Charts
    "chart_activity_title": {
        "en": "Daily Screening Activity (User History)",
        "hi": "दैनिक जांच गतिविधि (उपयोगकर्ता इतिहास)",
    },
    "chart_activity_caption": {
        "en": "Trend of analyses run in your account over recent days.",
        "hi": "हाल के दिनों में आपके खाते द्वारा किए गए परीक्षणों का रुझान।",
    },
    "chart_class_dist_title": {
        "en": "Predicted Adulteration Distribution",
        "hi": "अनुमानित मिलावट स्तरों का वितरण",
    },
    "chart_class_dist_caption": {
        "en": "Breakdown of predicted adulteration classes from your saved tests.",
        "hi": "आपके सहेजे गए परीक्षणों से प्राप्त मिलावट श्रेणियों का विवरण।",
    },
    "chart_dataset_title": {
        "en": "Research Dataset Partition (350 Samples)",
        "hi": "अनुसंधान डेटासेट विभाजन (350 नमूने)",
    },
    "chart_dataset_caption": {
        "en": "Mendeley benchmark samples across 7 wheat-flour adulteration tiers (50 samples per tier).",
        "hi": "7 मिलावट स्तरों पर 350 मेंडेली मानक नमूने (प्रत्येक श्रेणी में 50 नमूने)।",
    },
    "chart_empty_history": {
        "en": "No analysis records yet. Complete your first test in 'Analyze Sample' to visualize trends.",
        "hi": "अभी तक कोई विश्लेषण रिकॉर्ड नहीं है। रुझान देखने के लिए 'नमूने का विश्लेषण' में पहला परीक्षण करें।",
    },

    # ── Analytics Page ────────────────────────────────────────────────────
    "analytics_header_title": "ADVANCED ANALYTICS",
    "analytics_title": {
        "en": "Analytics & Scientific Insights",
        "hi": "एनालिटिक्स एवं वैज्ञानिक इनसाइट्स",
    },
    "analytics_desc": {
        "en": "Comprehensive visual breakdown of user analysis records, model predictions, and research dataset benchmarks.",
        "hi": "उपयोगकर्ता विश्लेषण रिकॉर्ड, मॉडल भविष्यवाणियों और अनुसंधान डेटासेट का व्यापक दृश्य विश्लेषण।",
    },
    "filter_date_range": {
        "en": "Date Range Filter",
        "hi": "तारीख सीमा फ़िल्टर",
    },
    "filter_all_time": {
        "en": "All Time",
        "hi": "पूरा समय",
    },
    "filter_last_7": {
        "en": "Last 7 Days",
        "hi": "पिछले 7 दिन",
    },
    "filter_last_30": {
        "en": "Last 30 Days",
        "hi": "पिछले 30 दिन",
    },
    "filter_status": {
        "en": "Filter by Result Status",
        "hi": "स्थिति के अनुसार फ़िल्टर",
    },
    "filter_all": {
        "en": "All Results",
        "hi": "सभी परिणाम",
    },
    "filter_pure_only": {
        "en": "Pure Only (0%)",
        "hi": "केवल शुद्ध (0%)",
    },
    "filter_adulterated_only": {
        "en": "Adulterated Only (1%–9%)",
        "hi": "केवल मिलावटी (1%–9%)",
    },
    "export_analytics_csv": {
        "en": "📥 Export Filtered Data to CSV",
        "hi": "📥 फ़िल्टर किया गया डेटा CSV में डाउनलोड करें",
    },

    # ── Notification Center ───────────────────────────────────────────────
    "notif_header_title": "NOTIFICATION CENTER",
    "notif_title": {
        "en": "System Alerts & Activity Notifications",
        "hi": "सिस्टम अलर्ट और गतिविधि सूचनाएँ",
    },
    "notif_desc": {
        "en": "Stay informed about analysis completions, system events, report readiness, and scientific insights.",
        "hi": "विश्लेषण समापन, सिस्टम इवेंट्स, रिपोर्ट की तैयारी और वैज्ञानिक जानकारियों से अवगत रहें।",
    },
    "tab_all_notifications": {
        "en": "All Notifications",
        "hi": "सभी सूचनाएँ",
    },
    "tab_unread_only": {
        "en": "Unread ({count})",
        "hi": "अपठित ({count})",
    },
    "btn_mark_all_read": {
        "en": "✓ Mark All as Read",
        "hi": "✓ सभी को पढ़ा हुआ चिह्नित करें",
    },
    "btn_clear_all_notif": {
        "en": "🗑️ Clear All Notifications",
        "hi": "🗑️ सभी सूचनाएँ हटाएं",
    },
    "no_notifications": {
        "en": "No notifications to display. Activity events will appear here automatically.",
        "hi": "दिखाने के लिए कोई सूचना नहीं है। गतिविधि की जानकारी यहाँ स्वचालित रूप से दिखाई देगी।",
    },
    "btn_mark_read": {
        "en": "Mark Read",
        "hi": "पढ़ा हुआ चिह्नित करें",
    },

    # ── Settings Page ─────────────────────────────────────────────────────
    "settings_header_title": "PREFERENCES & CONFIGURATION",
    "settings_title": {
        "en": "User Settings & Preferences",
        "hi": "उपयोगकर्ता सेटिंग्स और प्राथमिकताएं",
    },
    "settings_desc": {
        "en": "Customize your interface language, default explanation depth, notifications, and account settings.",
        "hi": "अपनी भाषा, डिफ़ॉल्ट विश्लेषण गहराई, सूचनाओं और खाता प्राथमिकताओं को अनुकूलित करें।",
    },
    "section_appearance": {
        "en": "Language & Localization",
        "hi": "भाषा और स्थानीयकरण",
    },
    "pref_ui_language": {
        "en": "Interface Language",
        "hi": "इंटरफ़ेस की भाषा",
    },
    "pref_explanation_lang": {
        "en": "Preferred AI Explanation Language",
        "hi": "पसंदीदा एआई स्पष्टीकरण भाषा",
    },
    "section_analysis_pref": {
        "en": "Analysis Preferences",
        "hi": "विश्लेषण प्राथमिकताएं",
    },
    "pref_default_depth": {
        "en": "Default AI Explanation Depth",
        "hi": "डिफ़ॉल्ट एआई स्पष्टीकरण की गहराई",
    },
    "depth_quick": {
        "en": "Quick Summary (2-3 sentences per section)",
        "hi": "त्वरित सारांश (प्रत्येक भाग में 2-3 वाक्य)",
    },
    "depth_detailed": {
        "en": "Detailed Explanation (Thorough scientific nuance — Recommended)",
        "hi": "विस्तृत स्पष्टीकरण (वैज्ञानिक सूक्ष्मता — अनुशंसित)",
    },
    "depth_technical": {
        "en": "Technical Analysis (Full PCA stats, wavenumbers & numerical metrics)",
        "hi": "तकनीकी विश्लेषण (पूर्ण पीसीए आंकड़े, वेवनंबर और सांख्यिकी)",
    },
    "section_notif_pref": {
        "en": "In-App Notification Preferences",
        "hi": "इन-ऐप सूचना प्राथमिकताएं",
    },
    "pref_notify_analysis": {
        "en": "Notify on completed sample screening",
        "hi": "नमूना जांच पूरी होने पर सूचना दें",
    },
    "pref_notify_insights": {
        "en": "Notify on new daily scientific insights",
        "hi": "दैनिक वैज्ञानिक इनसाइट्स पर सूचना दें",
    },
    "section_account_info": {
        "en": "Account Information",
        "hi": "खाता जानकारी",
    },
    "account_email": {
        "en": "Email Address",
        "hi": "ईमेल पता",
    },
    "account_name": {
        "en": "Researcher Name",
        "hi": "शोधकर्ता का नाम",
    },
    "account_role": {
        "en": "Access Role",
        "hi": "भूमिका",
    },
    "btn_save_settings": {
        "en": "💾 Save Settings & Preferences",
        "hi": "💾 सेटिंग्स और प्राथमिकताएं सहेजें",
    },
    "settings_saved": {
        "en": "✓ Settings saved successfully!",
        "hi": "✓ सेटिंग्स सफलतापूर्वक सहेजी गईं!",
    },

    # ── Analysis Workspace ────────────────────────────────────────────────
    "analyze_header_title": "ANALYSIS WORKSPACE",
    "analyze_title": {
        "en": "Turmeric Adulteration Screening",
        "hi": "हल्दी मिलावट जांच एवं प्रमाणीकरण",
    },
    "analyze_desc": {
        "en": "Upload an ATR-FTIR spectrum CSV or benchmark against existing physical samples from the research dataset.",
        "hi": "एटीआर-एफटीआईआर स्पेक्ट्रम सीएसवी अपलोड करें या शोध डेटासेट के नमूनों के साथ तुलनात्मक जांच करें।",
    },
    "step_1": {"en": "Input Data", "hi": "डेटा चुनें"},
    "step_2": {"en": "Validate", "hi": "जांचें"},
    "step_3": {"en": "Spectrum", "hi": "स्पेक्ट्रम"},
    "step_4": {"en": "Predict", "hi": "पूर्वानुमान"},
    "step_5": {"en": "AI Explain", "hi": "एआई व्याख्या"},
    "input_source_dataset": {
        "en": "Choose from 350 Research Dataset Samples",
        "hi": "350 शोध डेटासेट नमूनों में से चुनें",
    },
    "input_source_upload": {
        "en": "Upload Custom FTIR Spectrum CSV",
        "hi": "कस्टम एफटीआईआर स्पेक्ट्रम सीएसवी अपलोड करें",
    },
    "btn_run_analysis": {
        "en": "🚀 Run Adulteration Analysis",
        "hi": "🚀 मिलावट विश्लेषण शुरू करें",
    },
    "btn_new_analysis": {
        "en": "🔄 Start New Analysis",
        "hi": "🔄 नया विश्लेषण शुरू करें",
    },
    "btn_download_md": {
        "en": "📥 Download Markdown Report",
        "hi": "📥 मार्कडाउन रिपोर्ट डाउनलोड करें",
    },
    "btn_download_json": {
        "en": "📄 Download JSON Data",
        "hi": "📄 जेसन डेटा डाउनलोड करें",
    },
    "ground_truth_label": {
        "en": "Dataset Ground Truth",
        "hi": "डेटासेट वास्तविक सत्य (Ground Truth)",
    },
    "wheat_flour_suffix": {
        "en": "% Wheat Flour",
        "hi": "% गेहूं का आटा",
    },
    "pure_turmeric_status": {
        "en": "PURE TURMERIC",
        "hi": "शुद्ध हल्दी",
    },
    "adulterated_status": {
        "en": "ADULTERATED",
        "hi": "मिलावटी",
    },
    "predicted_class_eyebrow": {
        "en": "PREDICTED ADULTERATION CLASS",
        "hi": "अनुमानित मिलावट श्रेणी",
    },
    "metric_classifier": {
        "en": "Classifier Class",
        "hi": "वर्गीकरण परिणाम",
    },
    "metric_regression": {
        "en": "Regression Estimate",
        "hi": "मात्रात्मक अनुमान (रिग्रेशन)",
    },
    "metric_mode": {
        "en": "AI Analyst Mode",
        "hi": "एआई विश्लेषक मोड",
    },
    "ask_followup_title": {
        "en": "💬 Ask a Follow-Up Question",
        "hi": "💬 विश्लेषण से संबंधित प्रश्न पूछें",
    },
    "ask_followup_btn": {
        "en": "Ask →",
        "hi": "पूछें →",
    },
    "clear_followup_btn": {
        "en": "🗑️ Clear Follow-up Questions",
        "hi": "🗑️ प्रश्न इतिहास साफ करें",
    },

    # ── Common / General ──────────────────────────────────────────────────
    "loading": {
        "en": "Processing...",
        "hi": "प्रक्रिया जारी है...",
    },
    "success": {
        "en": "Success",
        "hi": "सफल",
    },
    "error": {
        "en": "Error",
        "hi": "त्रुटि",
    },
    "warning": {
        "en": "Warning",
        "hi": "चेतावनी",
    },
    "info": {
        "en": "Information",
        "hi": "सूचना",
    },
    "disclaimer_text": {
        "en": "FoodSure AI is a research prototype. Results do not substitute accredited laboratory testing.",
        "hi": "फूडश्योर एआई एक शोध प्रोटोटाइप है। परिणाम मान्यता प्राप्त प्रयोगशाला परीक्षण का विकल्प नहीं हैं।",
    },
}


# ---------------------------------------------------------------------------
# State Management & Translation Helper
# ---------------------------------------------------------------------------

_BARE_MODE_LANG = "en"


def get_current_language() -> str:
    """Return the active language code ('en' or 'hi') from session state or bare-mode fallback."""
    global _BARE_MODE_LANG
    try:
        lang = st.session_state.get("ui_language", _BARE_MODE_LANG)
        return lang if lang in ("en", "hi") else "en"
    except Exception:
        return _BARE_MODE_LANG


def set_current_language(lang: str) -> None:
    """Set the active language in session state and update user preference if available."""
    global _BARE_MODE_LANG
    if lang in ("en", "hi"):
        _BARE_MODE_LANG = lang
        try:
            st.session_state["ui_language"] = lang
        except Exception:
            pass


def t(key: str, default: str | None = None, **kwargs: Any) -> str:
    """Translate a key into the active language with optional kwargs interpolation.

    Parameters
    ----------
    key:
        Translation dictionary key.
    default:
        Fallback text if key is missing.
    kwargs:
        Template variables to format into the translated string.
    """
    lang = get_current_language()
    entry = TRANSLATIONS.get(key)
    if entry and isinstance(entry, dict):
        text = entry.get(lang) or entry.get("en") or default or key
    elif isinstance(entry, str):
        text = entry
    else:
        text = default or key

    if kwargs and isinstance(text, str):
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
