"""How It Works educational walkthrough for FoodSure AI — Bilingual."""

from __future__ import annotations

import streamlit as st
from ui.components import page_header
from ui.i18n import get_current_language


def render_how_it_works_page() -> None:
    is_hi = get_current_language() == "hi"

    eyebrow = "कार्यप्रणाली एवं पाइपलाइन" if is_hi else "METHODOLOGY & PIPELINE"
    title = "फूडश्योर एआई कैसे काम करता है" if is_hi else "How FoodSure AI Works"
    desc = (
        "मशीन लर्निंग और स्पेक्ट्रोस्कोपिक विश्लेषण वर्कफ़्लो का एक पारदर्शी, चरण-दर-चरण विवरण।"
        if is_hi
        else "A transparent, step-by-step breakdown of the machine learning and spectroscopic analysis workflow."
    )

    page_header(eyebrow, title, desc)

    if is_hi:
        steps = [
            (
                "01",
                "स्पेक्ट्रल अधिग्रहण (ATR-FTIR)",
                "एटीआर-एफटीआईआर (ATR-FTIR) स्पेक्ट्रोस्कोपी 4000 cm⁻¹ से 650 cm⁻¹ वेवनंबर पर 2,522 अवशोषण तीव्रताएं कैप्चर करती है। यह गेहूं का आटा मिलाने से बदले हुए जैविक बंधों (C-H, O-H, C=O) के कंपनों का सटीक फिंगरप्रिंट रिकॉर्ड करती है।",
            ),
            (
                "02",
                "फ़ीचर प्रीप्रोसेसिंग और स्केलिंग",
                "कच्ची स्पेक्ट्रल तीव्रताओं को केवल 280 प्रशिक्षण नमूनों पर फ़िट किए गए StandardScaler का उपयोग करके सामान्यीकृत किया जाता है। इससे डेटा लीकेज रुकता है और स्पेक्ट्रल रेंज में विचरण संरेखित होता है।",
            ),
            (
                "03",
                "प्रिंसिपल कंपोनेंट एनालिसिस (PCA)",
                "निकटवर्ती वेवनंबरों में अत्यधिक आयाम और सह-संबंध को नियंत्रित करने के लिए, PCA 2,522 फीचर्स को 13 प्रमुख घटकों में संपीड़ित करता है, जिससे 90.04% स्पेक्ट्रल विचरण सुरक्षित रहता है।",
            ),
            (
                "04",
                "दोहरी-स्तरीय मशीन लर्निंग अनुमान",
                "13 पीसीए घटक दो स्वतंत्र मॉडल द्वारा मूल्यांकित किए जाते हैं: एक लॉजिस्टिक रिग्रेशन क्लासिफायर जो 7 श्रेणियों में से एक आवंटित करता है, और एक रैंडम फ़ॉरेस्ट रिग्रेसर जो निरंतर प्रतिशत मात्रा का अनुमान लगाता है।",
            ),
            (
                "05",
                "जेमिनी एआई वैज्ञानिक व्याख्या",
                "पूर्वानुमान आउटपुट और सत्यापित साक्ष्य को गूगल जेमिनी एआई (gemini-3.5-flash-lite) को प्रेषित किया जाता है। जेमिनी परिणाम की व्याख्या करता है, अनिश्चितता सीमाएं जांचता है और प्रयोगशाला सत्यापन कदम सुझाता है।",
            ),
            (
                "06",
                "स्वतंत्र प्रयोगशाला सत्यापन",
                "चूंकि फूडश्योर एआई एक शोध प्रोटोटाइप है, इसलिए नियामक या खाद्य सुरक्षा निर्णयों के लिए मान्यता प्राप्त प्रयोगशाला परीक्षण अनिवार्य है।",
            ),
        ]
    else:
        steps = [
            (
                "01",
                "Spectral Acquisition (ATR-FTIR)",
                "Attenuated Total Reflectance Fourier-Transform Infrared (ATR-FTIR) spectroscopy captures 2,522 absorbance intensities across wavenumbers 4000 cm⁻¹ to 650 cm⁻¹. This captures vibrational fingerprints of organic bonds (C-H, O-H, C=O, C-O-C) altered by the introduction of wheat flour.",
            ),
            (
                "02",
                "Feature Preprocessing & Scaling",
                "Raw spectral intensities are normalized using a StandardScaler fitted strictly on the 280 training samples. This prevents data leakage and aligns feature variances across the full spectral range.",
            ),
            (
                "03",
                "Principal Component Analysis (PCA)",
                "To mitigate the curse of dimensionality and collinearity among adjacent wavenumbers, PCA reduces the 2,522 features to 13 principal components, preserving 90.04% of cumulative spectral variance.",
            ),
            (
                "04",
                "Dual-Stage Machine Learning Inference",
                "The 13 PCA components are evaluated by two independent models: a Logistic Regression classifier that assigns the sample to one of seven discrete adulteration bins (0%, 1%, 2%, 3%, 5%, 7%, 9%), and a Random Forest regressor that estimates the continuous adulteration percentage.",
            ),
            (
                "05",
                "Gemini AI Scientific Interpretation",
                "The prediction outputs and verified metadata evidence are packaged into a structured contract and passed to Google Gemini AI (gemini-3.5-flash-lite). Gemini explains the result, identifies caveats, checks confidence boundaries, and formats laboratory verification guidelines.",
            ),
            (
                "06",
                "Independent Laboratory Verification",
                "Because FoodSure AI is an AI-assisted research prototype trained under controlled laboratory conditions, all consequential food-safety findings must be verified using accredited wet chemistry or standard AOAC methods.",
            ),
        ]

    for num, title_s, desc_s in steps:
        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom: 1rem; border-left: 4px solid var(--turmeric-500);">
                <div style="display: flex; align-items: baseline; gap: 0.8rem; margin-bottom: 0.4rem;">
                    <span style="font-size: 1.1rem; font-weight: 800; color: var(--turmeric-600);">{num}</span>
                    <h3 style="margin: 0; font-size: 1.2rem; color: var(--forest-900);">{title_s}</h3>
                </div>
                <p style="margin: 0; font-size: 0.95rem; color: var(--ink-700); line-height: 1.6;">{desc_s}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
