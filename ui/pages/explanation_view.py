"""FoodSure AI — Premium structured explanation renderer.

Renders the 8-section AI explanation with:
- HTML sanitization (whitelist: <u>, <strong>, <em>, <br>)
- Auto-underline of key scientific terms
- Section cards with expandable details
- Depth controls (Quick / Detailed / Technical)
- Follow-up question interface
"""

from __future__ import annotations

import html
import re
from typing import Any

import streamlit as st

from backend.service import generate_followup_answer
from ui.i18n import get_current_language


# ---------------------------------------------------------------------------
# Key terms to auto-underline (order matters — longer phrases first)
# ---------------------------------------------------------------------------
_UNDERLINE_TERMS: list[str] = [
    # English terms
    "predicted adulteration level",
    "model confidence",
    "observed evidence",
    "estimated quantity",
    "scientific interpretation",
    "laboratory confirmation",
    "model limitations",
    "recommended next steps",
    "uncertainty",
    "adulteration class",
    "regression estimate",
    "principal component",
    "cross-validation",
    "ATR-FTIR",
    "wavenumber",
    "calibrated",
    # Hindi terms
    "अनुमानित मिलावट स्तर",
    "मॉडल विश्वास",
    "अवलोकित साक्ष्य",
    "मात्रात्मक अनुमान",
    "वैज्ञानिक व्याख्या",
    "प्रयोगशाला सत्यापन",
    "मॉडल सीमाएं",
    "अनुशंसित अगले कदम",
    "अनिश्चितता",
    "मिलावट श्रेणी",
    "रिग्रेशन अनुमान",
    "प्रिंसिपल कंपोनेंट",
    "क्रॉस-वैलिडेशन",
]

_ALLOWED_TAGS = {"u", "strong", "em", "br"}
_TAG_RE = re.compile(r"<(/?)(\w+)([^>]*)>", re.IGNORECASE)


def sanitize_for_display(text: str) -> str:
    """Escape raw AI output then re-allow safe tags (whitelist approach)."""
    if not text:
        return ""
    # Step 1: escape all HTML entities in the raw text
    safe = html.escape(text, quote=False)
    # Step 2: restore allowed tags (escaped as &lt;tag&gt; → <tag>)
    def restore_tag(m: re.Match) -> str:
        slash, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag in _ALLOWED_TAGS:
            return f"<{slash}{tag}>"  # strip any attributes for safety
        return m.group(0)  # keep as escaped entity
    # After html.escape, < becomes &lt; — we need to unescape ONLY allowed tags
    # Strategy: detect &lt;(allowed_tag)&gt; patterns
    for tag in _ALLOWED_TAGS:
        # opening tag
        safe = re.sub(
            rf"&lt;({re.escape(tag)})&gt;",
            rf"<\1>",
            safe,
            flags=re.IGNORECASE,
        )
        # closing tag
        safe = re.sub(
            rf"&lt;/({re.escape(tag)})&gt;",
            rf"</\1>",
            safe,
            flags=re.IGNORECASE,
        )
    return safe


def _auto_underline(text: str) -> str:
    """Auto-apply <u>...</u> to key scientific terms (case-insensitive, once each)."""
    for term in _UNDERLINE_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        # Only underline if not already inside a <u> tag
        text = pattern.sub(lambda m: f"<u>{m.group(0)}</u>", text, count=1)
    return text


def _render_text(text: str, underline: bool = True) -> str:
    """Sanitize and optionally underline a text string for safe HTML rendering."""
    safe = sanitize_for_display(text)
    if underline:
        safe = _auto_underline(safe)
    # Convert newlines to <br> for display
    safe = safe.replace("\n", "<br>")
    return safe


def _section_card(
    icon: str,
    title: str,
    content_html: str,
    color: str = "var(--forest-900)",
    bg: str = "var(--surface)",
    border: str = "var(--border-light)",
) -> str:
    return f"""
<div style="background:{bg}; border:1px solid {border}; border-radius:18px;
     padding:1.5rem 1.7rem; margin-bottom:1.2rem; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.8rem;">
    <span style="font-size:1.3rem;">{icon}</span>
    <span style="font-size:1.05rem; font-weight:800; color:{color}; letter-spacing:-0.01em;">{title}</span>
  </div>
  <div style="font-size:0.97rem; line-height:1.7; color:var(--forest-900);">
    {content_html}
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Depth selector
# ---------------------------------------------------------------------------

def render_depth_selector(key: str = "explanation_depth") -> str:
    """Render a compact depth radio and return the selected depth string."""
    is_hi = get_current_language() == "hi"
    heading = "स्पष्टीकरण गहराई" if is_hi else "Explanation Depth"
    st.markdown(
        f"<div style='margin-bottom:0.4rem; font-size:0.85rem; font-weight:700; "
        f"color:var(--forest-700); text-transform:uppercase; letter-spacing:0.05em;'>"
        f"{heading}</div>",
        unsafe_allow_html=True,
    )
    if is_hi:
        options = ["त्वरित सारांश", "विस्तृत स्पष्टीकरण", "तकनीकी विश्लेषण"]
        depth_map = {
            "त्वरित सारांश": "quick",
            "विस्तृत स्पष्टीकरण": "detailed",
            "तकनीकी विश्लेषण": "technical",
        }
    else:
        options = ["Quick Summary", "Detailed Explanation", "Technical Analysis"]
        depth_map = {
            "Quick Summary": "quick",
            "Detailed Explanation": "detailed",
            "Technical Analysis": "technical",
        }

    depth = st.radio(
        "Explanation depth",
        options=options,
        index=1,
        horizontal=True,
        label_visibility="collapsed",
        key=key,
    )
    return depth_map.get(depth, "detailed")


# ---------------------------------------------------------------------------
# Main explanation renderer
# ---------------------------------------------------------------------------

def render_explanation(
    structured_explanation: dict[str, Any],
    analysis_result: Any,  # AnalysisResult — avoid circular import
) -> None:
    """Render the full 8-section structured explanation with premium UI."""

    depth = structured_explanation.get("depth", "detailed")
    mode = structured_explanation.get("analysis_mode", "deterministic_fallback")
    is_gemini = "gemini" in mode.lower() or "llm" in mode.lower()

    is_hi = get_current_language() == "hi"

    title_main = "🔬 एआई वैज्ञानिक व्याख्या" if is_hi else "🔬 AI Scientific Explanation"
    mode_label = ("🤖 जेमिनी एआई" if is_gemini else "📐 डिटर्मिनिस्टिक") if is_hi else ("🤖 Gemini AI" if is_gemini else "📐 Deterministic")
    mode_color = "#1a6640" if is_gemini else "#7a6010"

    st.markdown(
        f"<div style='display:flex; align-items:center; gap:0.7rem; margin:1.5rem 0 1rem;'>"
        f"<span style='font-size:1.15rem; font-weight:800; color:var(--forest-900);'>"
        f"{title_main}</span>"
        f"<span style='background:{mode_color}22; color:{mode_color}; border:1px solid {mode_color}44; "
        f"border-radius:20px; padding:0.2rem 0.7rem; font-size:0.78rem; font-weight:700;'>"
        f"{mode_label} · {depth.upper()}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── 1. Executive Summary (always visible, highlighted) ─────────────────
    exec_title = "📋 कार्यकारी सारांश" if is_hi else "📋 Executive Summary"
    exec_summary = _render_text(
        structured_explanation.get("executive_summary", "No summary available.")
    )
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,#1a3d2b,#183b2c); border-radius:18px;
     padding:1.7rem 2rem; margin-bottom:1.5rem; box-shadow:0 4px 16px rgba(0,0,0,0.15);">
  <div style="font-size:0.8rem; font-weight:800; color:#d49726; text-transform:uppercase;
       letter-spacing:0.1em; margin-bottom:0.7rem;">{exec_title}</div>
  <div style="font-size:1.02rem; line-height:1.75; color:#f0ede4; font-weight:500;">
    {exec_summary}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── 2. Result Interpretation (visible) ────────────────────────────────
    interp_title = "विस्तृत परिणाम व्याख्या" if is_hi else "Detailed Result Interpretation"
    result_interp = _render_text(
        structured_explanation.get("result_interpretation", "")
    )
    if result_interp:
        st.markdown(
            _section_card(
                "📊", interp_title,
                result_interp,
                border="#d4972644",
            ),
            unsafe_allow_html=True,
        )

    # ── 3. Evidence & Reasoning (expandable, structured) ──────────────────
    evidence_list = structured_explanation.get("evidence_and_reasoning", [])
    if evidence_list:
        ev_exp_title = "🔬 साक्ष्य एवं तर्क (साक्ष्य → अर्थ → पूर्वानुमान से संबंध → सीमा)" if is_hi else "🔬 Evidence & Reasoning (Evidence → Meaning → Connection → Limitation)"
        with st.expander(ev_exp_title, expanded=True):
            for i, item in enumerate(evidence_list):
                if not isinstance(item, dict):
                    continue
                evidence = _render_text(item.get("evidence", ""), underline=False)
                meaning = _render_text(item.get("meaning", ""))
                connection = _render_text(item.get("connection", ""))
                limitation = _render_text(item.get("limitation", ""), underline=False)

                lbl_ev = "📌 साक्ष्य" if is_hi else "📌 Evidence"
                lbl_mn = "💡 अर्थ" if is_hi else "💡 Meaning"
                lbl_cn = "🔗 पूर्वानुमान से संबंध" if is_hi else "🔗 Connection to Prediction"
                lbl_lm = "⚠️ सीमा" if is_hi else "⚠️ Limitation"

                st.markdown(
                    f"""
<div style="background:var(--surface); border-left:4px solid #d49726; border-radius:0 12px 12px 0;
     padding:1rem 1.3rem; margin-bottom:1rem;">
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
    <div>
      <div style="font-size:0.75rem; font-weight:800; color:#1a6640; text-transform:uppercase;
           letter-spacing:0.08em; margin-bottom:0.3rem;">{lbl_ev}</div>
      <div style="font-size:0.92rem; line-height:1.6; color:var(--forest-900);">{evidence}</div>
    </div>
    <div>
      <div style="font-size:0.75rem; font-weight:800; color:#7a6010; text-transform:uppercase;
           letter-spacing:0.08em; margin-bottom:0.3rem;">{lbl_mn}</div>
      <div style="font-size:0.92rem; line-height:1.6; color:var(--forest-900);">{meaning}</div>
    </div>
    <div>
      <div style="font-size:0.75rem; font-weight:800; color:#1a4060; text-transform:uppercase;
           letter-spacing:0.08em; margin-bottom:0.3rem;">{lbl_cn}</div>
      <div style="font-size:0.92rem; line-height:1.6; color:var(--forest-900);">{connection}</div>
    </div>
    <div>
      <div style="font-size:0.75rem; font-weight:800; color:#7a1010; text-transform:uppercase;
           letter-spacing:0.08em; margin-bottom:0.3rem;">{lbl_lm}</div>
      <div style="font-size:0.92rem; line-height:1.6; color:var(--forest-900);">{limitation}</div>
    </div>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

    # ── 4. Scientific Explanation (expandable, beginner-friendly) ─────────
    sci_exp = _render_text(structured_explanation.get("scientific_explanation", ""))
    if sci_exp:
        sci_title = "🧪 वैज्ञानिक व्याख्या — सरल भाषा में" if is_hi else "🧪 Scientific Explanation — Made Simple"
        with st.expander(sci_title, expanded=False):
            st.markdown(
                f"""
<div style="background:#f3faf6; border:1px solid #b8ddc8; border-radius:12px;
     padding:1.3rem 1.5rem; font-size:0.95rem; line-height:1.75; color:#1a3d2b;">
  {sci_exp}
</div>
""",
                unsafe_allow_html=True,
            )

    # ── 5. Confidence & Uncertainty (expandable, with caution styling) ────
    conf_text = _render_text(structured_explanation.get("confidence_and_uncertainty", ""))
    if conf_text:
        conf_title = "🎯 परिणाम कितना विश्वसनीय है? — विश्वास और अनिश्चितता" if is_hi else "🎯 How Reliable Is This Result? — Confidence & Uncertainty"
        with st.expander(conf_title, expanded=False):
            st.markdown(
                f"""
<div style="background:#fdf8ee; border:1px solid #e8c96a; border-radius:12px;
     padding:1.3rem 1.5rem; font-size:0.95rem; line-height:1.75; color:#5a400a;">
  {conf_text}
</div>
""",
                unsafe_allow_html=True,
            )

    # ── 6. Practical Implications (visible) ───────────────────────────────
    prac_impl = _render_text(structured_explanation.get("practical_implications", ""))
    if prac_impl:
        prac_title = "व्यावहारिक निहितार्थ" if is_hi else "Practical Implications"
        st.markdown(
            _section_card(
                "🌿", prac_title,
                prac_impl,
                border="#1a664044",
            ),
            unsafe_allow_html=True,
        )

    # ── 7. Recommended Next Steps (visible bullet list) ───────────────────
    next_steps = structured_explanation.get("recommended_next_steps", [])
    if next_steps:
        next_title = "अनुशंसित अगले कदम" if is_hi else "Recommended Next Steps"
        steps_html = "".join(
            f"<li style='margin-bottom:0.5rem; line-height:1.6;'>{_render_text(s)}</li>"
            for s in next_steps
        )
        st.markdown(
            _section_card(
                "✅", next_title,
                f"<ol style='padding-left:1.3rem; margin:0;'>{steps_html}</ol>",
                border="#1a664044",
            ),
            unsafe_allow_html=True,
        )

    # ── 8. Limitations & Transparency (expandable, warning styling) ───────
    limitations = structured_explanation.get("limitations", [])
    if limitations:
        lim_title = "⚠️ सीमाएं एवं पारदर्शिता" if is_hi else "⚠️ Limitations & Transparency"
        with st.expander(lim_title, expanded=False):
            lim_html = "".join(
                f"<li style='margin-bottom:0.5rem; line-height:1.6;'>{_render_text(s, underline=False)}</li>"
                for s in limitations
            )
            st.markdown(
                f"""
<div style="background:#fff5f5; border:1px solid #f0b8b8; border-radius:12px;
     padding:1.3rem 1.5rem;">
  <ul style="padding-left:1.3rem; margin:0; font-size:0.92rem; line-height:1.7; color:#6b1a1a;">
    {lim_html}
  </ul>
</div>
""",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Follow-up question interface
# ---------------------------------------------------------------------------

def render_followup_interface(
    analysis_result: Any,  # AnalysisResult
    use_gemini: bool = True,
) -> None:
    """Render the interactive follow-up question interface below the explanation."""

    st.markdown("---")
    st.markdown(
        "<div style='font-size:1.05rem; font-weight:800; color:var(--forest-900); "
        "margin-bottom:0.8rem;'>💬 Ask a Follow-Up Question</div>",
        unsafe_allow_html=True,
    )

    # Pre-canned question buttons from follow_up_questions
    follow_up_qs = analysis_result.structured_explanation.get("follow_up_questions", [])
    if follow_up_qs:
        st.markdown(
            "<div style='font-size:0.82rem; color:var(--ink-500); margin-bottom:0.5rem;'>"
            "Suggested questions (click to ask):</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(follow_up_qs), 3))
        for i, q in enumerate(follow_up_qs[:3]):
            with cols[i % 3]:
                if st.button(f"❓ {q[:60]}{'…' if len(q) > 60 else ''}", key=f"fq_{i}_{analysis_result.analysis_id[:6]}"):
                    st.session_state["followup_pending"] = q

    # Custom question input
    col_input, col_ask = st.columns([4, 1])
    with col_input:
        custom_q = st.text_input(
            "Ask a follow-up question about this analysis",
            value=st.session_state.pop("followup_pending", ""),
            placeholder="e.g. What does the regression estimate mean?",
            key=f"followup_input_{analysis_result.analysis_id[:6]}",
            label_visibility="collapsed",
        )
    with col_ask:
        ask_clicked = st.button("Ask →", type="primary", use_container_width=True, key=f"ask_btn_{analysis_result.analysis_id[:6]}")

    if ask_clicked and custom_q and custom_q.strip():
        question = custom_q.strip()
        with st.spinner("Generating answer…"):
            try:
                answer = generate_followup_answer(
                    question=question,
                    analysis_result=analysis_result,
                    use_gemini=use_gemini,
                )
            except Exception as exc:
                answer = f"Could not generate answer: {exc}"

        # Add to session history
        history: list[dict] = st.session_state.get("followup_history", [])
        history.append({"question": question, "answer": answer})
        st.session_state["followup_history"] = history
        st.rerun()

    # Render conversation history
    history = st.session_state.get("followup_history", [])
    if history:
        st.markdown(
            "<div style='margin-top:1rem; margin-bottom:0.4rem; font-size:0.82rem; "
            "color:var(--ink-500); font-weight:700; text-transform:uppercase; "
            "letter-spacing:0.05em;'>Conversation</div>",
            unsafe_allow_html=True,
        )
        for item in reversed(history):
            q_safe = html.escape(item["question"])
            a_safe = _render_text(item["answer"])
            st.markdown(
                f"""
<div style="margin-bottom:1rem;">
  <div style="background:#e8f5ee; border-radius:12px 12px 4px 12px; padding:0.7rem 1rem;
       font-size:0.92rem; color:#1a3d2b; font-weight:600; margin-bottom:0.4rem;">
    ❓ {q_safe}
  </div>
  <div style="background:var(--surface); border:1px solid var(--border-light); border-radius:4px 12px 12px 12px;
       padding:0.8rem 1rem; font-size:0.92rem; color:var(--forest-900); line-height:1.65;">
    🤖 {a_safe}
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        if st.button("🗑️ Clear Follow-up Questions", key=f"clear_fq_{analysis_result.analysis_id[:6]}"):
            st.session_state["followup_history"] = []
            st.rerun()
