"""Premium scientific visual styling for FoodSure AI."""

from __future__ import annotations

import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --forest-950: #07150e;
            --forest-900: #0e2318;
            --forest-800: #143525;
            --forest-700: #1c4933;
            --forest-600: #266044;
            --forest-50: #f1f6f3;
            
            --cream-bg: #f8f7f2;
            --surface: #ffffff;
            --surface-muted: #f4f3ec;
            
            --turmeric-500: #d49726;
            --turmeric-600: #b87f18;
            --turmeric-700: #96640c;
            --turmeric-100: #fdf3df;
            --turmeric-50: #fff9ed;
            
            --ink-900: #18201a;
            --ink-800: #25332a;
            --ink-700: #334036;
            --ink-500: #5d6f62;
            --ink-400: #7b8d80;
            --ink-300: #93a497;
            
            --border-light: #e2e6dc;
            --border-subtle: #eeefe8;
            
            --danger-600: #c53030;
            --danger-100: #fed7d7;
            --success-600: #276749;
            --success-100: #c6f6d5;
            
            --shadow-sm: 0 1px 3px 0 rgba(14, 35, 24, 0.05);
            --shadow-md: 0 4px 14px -2px rgba(14, 35, 24, 0.07), 0 2px 6px -1px rgba(14, 35, 24, 0.04);
            --shadow-lg: 0 12px 28px -4px rgba(14, 35, 24, 0.10), 0 4px 10px -2px rgba(14, 35, 24, 0.05);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 22px;
        }

        /* ── Base App & Typography ────────────────────────────────────────── */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: var(--cream-bg) !important;
            color: var(--ink-900) !important;
        }

        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* ── Remove Default Streamlit White Taskbar / Header ──────────────── */
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            display: none !important;
            height: 0px !important;
            min-height: 0px !important;
            visibility: hidden !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stDecoration"] {
            display: none !important;
            height: 0px !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Maintain sidebar toggle visibility if collapsed */
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            top: 0.75rem !important;
            left: 0.75rem !important;
            background: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: var(--shadow-sm) !important;
            z-index: 99999 !important;
        }

        /* ── Container Layout ─────────────────────────────────────────────── */
        .block-container {
            max-width: 1240px !important;
            padding-top: 1.2rem !important;
            padding-bottom: 4rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* ── Absolute Readability Override for All Headings ────────────────── */
        /* Guarantees NO invisible white text on cream backgrounds in any OS mode */
        h1, h2, h3, h4, h5, h6,
        .page-title,
        [data-testid="stHeadingWithActionElements"] h1,
        [data-testid="stHeadingWithActionElements"] h2,
        [data-testid="stHeadingWithActionElements"] h3,
        .stHeadingContainer h1,
        .stHeadingContainer h2,
        .stHeadingContainer h3,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4 {
            color: var(--forest-900) !important;
            font-weight: 800 !important;
            letter-spacing: -0.025em !important;
        }

        h1, .page-title {
            font-size: clamp(1.9rem, 3.2vw, 2.6rem) !important;
            line-height: 1.15 !important;
            margin-top: 0.1rem !important;
            margin-bottom: 0.4rem !important;
        }

        h2 {
            font-size: 1.45rem !important;
            margin-top: 1.4rem !important;
            margin-bottom: 0.6rem !important;
        }

        h3 {
            font-size: 1.2rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }

        h4 {
            font-size: 1.05rem !important;
            margin-top: 0.8rem !important;
        }

        p, li, span, div {
            color: var(--ink-800);
            line-height: 1.62;
        }

        .page-desc {
            color: var(--ink-500) !important;
            font-size: 1.02rem !important;
            line-height: 1.55 !important;
            margin-top: -0.1rem !important;
            margin-bottom: 1.4rem !important;
        }

        .eyebrow {
            color: var(--turmeric-600) !important;
            font-size: 0.76rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
            margin-bottom: 0.35rem !important;
            display: inline-block !important;
        }

        /* ── Sidebar Styling ──────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--forest-950) 0%, var(--forest-900) 60%, var(--forest-800) 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        [data-testid="stSidebar"] * {
            color: #f3f7f4 !important;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            padding: 0.52rem 0.8rem !important;
            border-radius: var(--radius-md) !important;
            transition: all 0.15s ease-in-out !important;
            margin-bottom: 0.12rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background-color: rgba(255, 255, 255, 0.08) !important;
        }

        /* ── Input Controls & Selectboxes (High Contrast & No Black Boxes) ── */
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            background-color: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input {
            color: var(--ink-900) !important;
            font-size: 0.92rem !important;
            background-color: transparent !important;
        }

        div[data-baseweb="input"] input::placeholder {
            color: var(--ink-400) !important;
        }

        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            color: var(--ink-900) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        div[data-baseweb="select"] * {
            color: var(--ink-900) !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {
            background-color: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: var(--shadow-lg) !important;
        }

        li[role="option"] {
            color: var(--ink-900) !important;
            background-color: #ffffff !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background-color: var(--forest-50) !important;
            color: var(--forest-900) !important;
        }

        /* ── Buttons ──────────────────────────────────────────────────────── */
        div.stButton > button {
            background-color: #ffffff !important;
            color: var(--forest-800) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            padding: 0.52rem 1.1rem !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.16s ease-in-out !important;
        }

        div.stButton > button:hover {
            background-color: var(--forest-50) !important;
            border-color: var(--forest-700) !important;
            color: var(--forest-900) !important;
            transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"] {
            background-color: var(--forest-800) !important;
            color: #ffffff !important;
            border: 1px solid var(--forest-800) !important;
            box-shadow: 0 2px 6px rgba(20, 53, 37, 0.25) !important;
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: var(--forest-700) !important;
            border-color: var(--forest-700) !important;
            box-shadow: 0 4px 12px rgba(20, 53, 37, 0.35) !important;
        }

        div.stDownloadButton > button {
            background-color: #ffffff !important;
            color: var(--forest-800) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            font-weight: 700 !important;
            box-shadow: var(--shadow-sm) !important;
        }

        div.stDownloadButton > button:hover {
            background-color: var(--forest-50) !important;
            border-color: var(--forest-700) !important;
        }

        /* ── Metric Cards ─────────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: var(--surface) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.15rem 1.25rem !important;
            box-shadow: var(--shadow-sm) !important;
        }

        [data-testid="stMetricLabel"] p {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            color: var(--ink-500) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--forest-900) !important;
            font-weight: 800 !important;
            font-size: 1.75rem !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }

        /* ── Custom Cards & Badges ────────────────────────────────────────── */
        .glass-card {
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 1.35rem;
            box-shadow: var(--shadow-sm);
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }

        .glass-card:hover {
            box-shadow: var(--shadow-md);
            border-color: #d1d7ca;
        }

        .top-navbar-card {
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 0.55rem 1rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 1.4rem;
        }

        .metric-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.65rem;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }

        .pill-pure {
            background-color: var(--success-100);
            color: var(--success-600);
            border: 1px solid rgba(39, 103, 73, 0.2);
        }

        .pill-adulterated {
            background-color: var(--danger-100);
            color: var(--danger-600);
            border: 1px solid rgba(197, 48, 48, 0.2);
        }

        .pill-gold {
            background-color: var(--turmeric-100);
            color: var(--turmeric-600);
            border: 1px solid rgba(184, 127, 24, 0.25);
        }

        /* ── Hero Banner ──────────────────────────────────────────────────── */
        .hero-banner {
            background: linear-gradient(135deg, #ffffff 0%, #f6f7f2 100%);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-xl);
            padding: clamp(1.8rem, 3.5vw, 2.8rem);
            box-shadow: var(--shadow-sm);
            margin-bottom: 1.8rem;
            position: relative;
            overflow: hidden;
        }

        .hero-banner::after {
            content: '';
            position: absolute;
            top: -60px;
            right: -60px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(212, 151, 38, 0.12) 0%, rgba(212, 151, 38, 0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        /* ── Result Callout ───────────────────────────────────────────────── */
        .result-panel {
            background: linear-gradient(135deg, var(--forest-950) 0%, var(--forest-900) 50%, var(--forest-800) 100%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: var(--radius-xl);
            padding: 2.2rem;
            color: #ffffff;
            box-shadow: var(--shadow-lg);
            margin-bottom: 1.5rem;
        }

        .result-panel * {
            color: #ffffff !important;
        }

        .result-giant {
            font-size: clamp(2.8rem, 6vw, 4.2rem);
            font-weight: 800;
            line-height: 1.0;
            color: #ffffff;
            letter-spacing: -0.04em;
            margin: 0.6rem 0;
        }

        /* ── Split-screen Login Container ─────────────────────────────────── */
        .auth-container {
            display: grid;
            grid-template-columns: 1.15fr 1fr;
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            margin: 1.5rem auto;
            max-width: 980px;
            min-height: 560px;
        }

        .auth-left {
            background: linear-gradient(145deg, var(--forest-950) 0%, var(--forest-900) 50%, var(--forest-800) 100%);
            padding: 3rem;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }

        .auth-left::after {
            content: '';
            position: absolute;
            bottom: -50px;
            left: -50px;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(212, 151, 38, 0.22) 0%, transparent 70%);
            border-radius: 50%;
        }

        .auth-left h2 {
            color: #ffffff !important;
            font-size: 2rem;
            margin-top: 0.5rem;
        }

        .auth-left p {
            color: #d1ded5 !important;
            font-size: 1.02rem;
            line-height: 1.6;
        }

        .auth-right {
            padding: 2.8rem;
            background: var(--surface);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        @media (max-width: 820px) {
            .auth-container {
                grid-template-columns: 1fr;
            }
            .auth-left {
                padding: 2rem;
            }
            .auth-right {
                padding: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
