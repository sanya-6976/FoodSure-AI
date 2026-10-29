"""About and scientific limitations page for FoodSure AI — Bilingual."""

from __future__ import annotations

import streamlit as st
from ui.components import page_header
from ui.i18n import get_current_language


def render_about_page() -> None:
    is_hi = get_current_language() == "hi"

    eyebrow = "परियोजना की जानकारी" if is_hi else "PROJECT INFORMATION"
    title = "फूडश्योर एआई के बारे में" if is_hi else "About FoodSure AI"
    desc = (
        "एआई-सहायता प्राप्त हल्दी मिलावट जांच और बहुमाध्यम फीचर मूल्यांकन की जांच करने वाला एक वैज्ञानिक प्रोटोटाइप।"
        if is_hi
        else "A scientific prototype investigating AI-assisted turmeric adulteration screening and multimodal feature evaluation."
    )

    page_header(eyebrow, title, desc)

    if is_hi:
        st.markdown(
            """
            ### 🌾 मिशन एवं वैज्ञानिक कार्यक्षेत्र
            खाद्य मिलावट वैश्विक स्तर पर एक महत्वपूर्ण आर्थिक और स्वास्थ्य चिंता का विषय है। 
            पारंपरिक निरीक्षण के तरीके अक्सर विनाशकारी, धीमे या त्वरित परीक्षण के लिए दुर्गम होते हैं।
            
            **फूडश्योर एआई** यह जांच करता है कि क्या बहुमाध्यम मशीन-लर्निंग आर्किटेक्चर (इन्फ्रारेड स्पेक्ट्रोस्कोपी, कैलोरीमेट्रिक इंडेक्स और कंप्यूटर-विज़न फीचर्स) 
            हल्दी में गेहूं के आटे की मिलावट की विश्वसनीय रूप से पहचान कर सकते हैं और मिलावट के स्तर को सटीक रूप से माप सकते हैं।
            """
        )

        st.markdown("---")
        st.markdown("### ⚠️ वैज्ञानिक अस्वीकरण एवं महत्वपूर्ण सीमाएं")

        st.warning(
            """
            **1. केवल अनुसंधान प्रोटोटाइप:** फूडश्योर एआई एक नियंत्रित बेंचमार्क डेटासेट पर विकसित एक प्रयोगात्मक शोध प्रणाली है। 
            इसे खाद्य सुरक्षा प्राधिकरणों (जैसे एफएसएसएआई, यूएस एफडीए, ईएफएसए) से विनियामक प्रमाणीकरण प्राप्त नहीं हुआ है।
            """
        )

        st.info(
            """
            **2. ऐतिहासिक होल्डआउट संदर्भ:** जबकि नोटबुक 9 में मॉडल चयन विशेष रूप से प्रशिक्षण विभाजन पर 5-फोल्ड क्रॉस-वैलिडेशन का उपयोग करता है, 
            70-नमूने के परीक्षण समूह की जांच पहले के खोजपूर्ण प्रयोगों में भी की गई थी।
            """
        )

        st.warning(
            """
            **3. नमूना समूहीकरण:** 350 नमूने `T{level}S{index}` नामकरण का पालन करते हैं। उपलब्ध डेटासेट दस्तावेज़ यह स्पष्ट नहीं करता 
            कि क्या ये स्वतंत्र हल्दी बैचों का प्रतिनिधित्व करते हैं या साझा मिश्रणों से बार-बार लिए गए स्कैन हैं।
            """
        )

        st.info(
            """
            **4. संभावना अंशांकन (Probability Calibration):** लॉजिस्टिक रिग्रेशन क्लासिफायर ऐसे निर्णय स्कोर आउटपुट करता है 
            जो वास्तविक दुनिया की शुद्धता की सत्य संभावनाओं के लिए कैलिब्रेटेड नहीं हैं।
            """
        )

        st.markdown("---")
        st.markdown("### 🛠️ आर्किटेक्चर और तकनीकी स्टैक")
        st.markdown(
            """
            - **मशीन लर्निंग एवं प्रीप्रोसेसिंग:** Scikit-Learn 1.9.1, PCA, Logistic Regression, Random Forest Regressor
            - **स्पेक्ट्रोस्कोपी पाइपलाइन:** NumPy 2.5, Pandas 3.0, Joblib 1.6
            - **जनरेटिव एआई विश्लेषक:** Google Gemini AI (`gemini-3.5-flash-lite`)
            - **सुरक्षा एवं क्रिप्टोग्राफी:** Argon2id (`argon2-cffi 25.1.0`), SQLite उपयोगकर्ता-स्तरीय डेटा अलगाव
            - **वेब एप्लिकेशन और यूआई/यूएक्स:** Streamlit 1.66.1, आधुनिक वैज्ञानिक सीएसएस
            """
        )
    else:
        st.markdown(
            """
            ### 🌾 Mission & Scientific Scope
            Food adulteration poses significant economic and health concerns globally. 
            Traditional inspection methods are often destructive, slow, or inaccessible for rapid screening.
            
            **FoodSure AI** investigates whether multimodal machine-learning architectures (incorporating infrared spectroscopy, 
            colorimetric indices, and computer-vision features) can reliably identify wheat-flour adulteration in turmeric 
            and accurately quantify adulteration levels.
            """
        )

        st.markdown("---")
        st.markdown("### ⚠️ Non-Negotiable Scientific Disclaimers & Limitations")

        st.warning(
            """
            **1. Research Prototype Only:** FoodSure AI is an experimental research system developed on a controlled benchmark dataset. 
            It has not received regulatory clearance, certification, or accreditation from food safety authorities (e.g. FSSAI, US FDA, EFSA).
            """
        )

        st.info(
            """
            **2. Reused Holdout Context:** While model selection in Notebook 9 utilized five-fold cross-validation exclusively on the training partition, 
            the 70-sample test cohort was previously examined in exploratory notebooks (Notebooks 04–06). It should not be considered an untouched external cohort.
            """
        )

        st.warning(
            """
            **3. Specimen Grouping:** The 350 samples follow the naming convention `T{level}S{index}`. Available dataset documentation 
            does not establish whether indexed specimens represent fully independent turmeric root batches or repeated instrumental scans from shared mixtures.
            """
        )

        st.info(
            """
            **4. Probability Calibration:** The saved Logistic Regression classifier outputs decision scores that are not calibrated to true 
            empirical posterior probabilities of real-world correctness.
            """
        )

        st.markdown("---")
        st.markdown("### 🛠️ Architecture & Technology Stack")
        st.markdown(
            """
            - **Machine Learning & Preprocessing:** Scikit-Learn 1.9.1, PCA, Logistic Regression, Random Forest Regressor
            - **Spectroscopy Pipeline:** NumPy 2.5, Pandas 3.0, Joblib 1.6
            - **Generative AI Analyst:** Google Gemini AI (`gemini-3.5-flash-lite`)
            - **Security & Cryptography:** Argon2id (`argon2-cffi 25.1.0`), SQLite with user-level data isolation
            - **Web Application & UI/UX:** Streamlit 1.66.1, Modern Scientific CSS
            """
        )
