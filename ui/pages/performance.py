"""Model evaluation and performance metrics page for FoodSure AI — Bilingual."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backend.service import get_model_performance_artifacts
from ui.components import page_header
from ui.i18n import get_current_language


def render_performance_page() -> None:
    is_hi = get_current_language() == "hi"

    eyebrow = "वैज्ञानिक मूल्यांकन" if is_hi else "SCIENTIFIC EVALUATION"
    title = "प्रायोगिक मॉडल प्रदर्शन" if is_hi else "Empirical Model Performance"
    desc = (
        "नोटबुक 9 प्रयोगों में मूल्यांकित सभी 21 माध्यम और एल्गोरिदम कॉन्फ़िगरेशन के पारदर्शी मूल्यांकन परिणाम।"
        if is_hi
        else "Transparent evaluation results across all 21 modality and algorithm configurations evaluated in Notebook 9 experiments."
    )

    page_header(eyebrow, title, desc)

    artifacts = get_model_performance_artifacts()

    notice_title = "मूल्यांकन संदर्भ एवं अखंडता सूचना:" if is_hi else "Evaluation Context & Integrity Notice:"
    notice_body = (
        "सभी मेट्रिक्स 280-नमूना प्रशिक्षण विभाजन पर 5-फोल्ड क्रॉस-वैलिडेशन और निश्चित 70-नमूना होल्डआउट पर मूल्यांकन को दर्शाते हैं। "
        "चूंकि इस 70-नमूने के होल्डआउट का पहले के खोजपूर्ण नोटबुक (04-06) में भी परीक्षण किया गया था, इसलिए इसे अछूते बाहरी परीक्षण समूह के बजाय ऐतिहासिक रूप से पुन: उपयोग किए गए बेंचमार्क के रूप में रिपोर्ट किया गया है।"
        if is_hi
        else "All metrics reflect five-fold cross-validation on the 280-sample training partition and evaluation on the fixed 70-sample holdout. Because this 70-sample holdout was also inspected in earlier exploratory notebooks (Notebooks 04–06), it is reported as a historically reused benchmark rather than an untouched external test cohort."
    )

    st.markdown(
        f"""
        <div style="background: var(--turmeric-50); border: 1px solid var(--turmeric-100); border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; font-size: 0.92rem; color: #684805;">
            <strong>⚠️ {notice_title}</strong> {notice_body}
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_labels = (
        ["5-फोल्ड क्रॉस-वैलिडेशन (280)", "निश्चित होल्डआउट मूल्यांकन (70)", "मात्रात्मक रिग्रेशन मॉडल", "कन्फ्यूजन मैट्रिक्स"]
        if is_hi
        else ["5-Fold Cross-Validation (280)", "Fixed Holdout Evaluation (70)", "Continuous Regression Quantification", "Confusion Matrix"]
    )

    tab_cv, tab_holdout, tab_reg, tab_cm = st.tabs(tab_labels)

    with tab_cv:
        st.subheader("21 कॉन्फ़िगरेशन में माध्यम तुलना" if is_hi else "Modality Comparison Across 21 Configurations")
        st.caption("280 प्रशिक्षण नमूनों पर 5-फोल्ड स्तरीकृत क्रॉस-वैलिडेशन। औसत ± मानक विचलन।" if is_hi else "Stratified 5-fold cross-validation over the 280 training samples. Mean ± Fold Standard Deviation.")

        cv_df = artifacts["cv_results"]
        if cv_df is not None:
            display_cols = [c for c in ["Modalities", "Model", "Accuracy Mean", "Accuracy Std", "Macro F1 Mean", "Macro F1 Std"] if c in cv_df.columns]
            st.dataframe(
                cv_df[display_cols].round(4),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(f"#### {'मैक्रो F1 स्कोर तुलना' if is_hi else 'Macro F1 Score Comparison'}")
            chart_df = cv_df.copy()
            chart_df["Config"] = chart_df["Modalities"] + " (" + chart_df["Model"] + ")"
            chart_data = chart_df.set_index("Config")[["Macro F1 Mean"]].sort_values("Macro F1 Mean", ascending=True)
            st.bar_chart(chart_data)
        else:
            st.info("CV results table not found at results/notebook_09/fusion_cv_results.csv")

    with tab_holdout:
        st.subheader("70-नमूना होल्डआउट परिणाम" if is_hi else "Fixed 70-Sample Holdout Results")
        st.caption("निश्चित 70-नमूना परीक्षण सेट (प्रति मिलावट स्तर 10 नमूने) पर मूल्यांकन।" if is_hi else "Evaluation on the fixed 70-sample test set (10 samples per adulteration level).")

        holdout_df = artifacts["holdout_results"]
        if holdout_df is not None:
            st.dataframe(holdout_df.round(4), use_container_width=True, hide_index=True)
            st.markdown(
                """
                **Parsimony Decision:** In 5-fold cross-validation, FTIR alone achieved 1.0000 Macro F1, matching the performance of the full 3-modality fusion. 
                Following standard Occam's razor criteria (favoring simpler models when performance is tied), the deployable inference model was finalized with FTIR-only Logistic Regression.
                """
            )
        else:
            st.info("Holdout results table not found.")

    with tab_reg:
        st.subheader("मिलावट प्रतिशत रिग्रेशन मॉडल" if is_hi else "Adulteration Percentage Regression Models")
        st.caption("FTIR और Color + FTIR माध्यमों पर निरंतर मात्रात्मक मूल्यांकन।" if is_hi else "Continuous quantification evaluated on FTIR and Color + FTIR configurations.")

        reg_df = artifacts["regression_results"]
        if reg_df is not None:
            st.dataframe(reg_df.round(4), use_container_width=True, hide_index=True)
            st.markdown(
                """
                - **Random Forest Regressor on FTIR:** Achieved mean CV MAE of **0.0314%** adulterant w/w.
                - **Regression Units:** Expressed in absolute percentage points (w/w wheat flour in turmeric powder).
                - **Separate Estimator:** Regression is performed by an independent Random Forest Regressor, distinct from the discrete Logistic Regression classifier.
                """
            )
        else:
            st.info("Regression results table not found.")

    with tab_cm:
        st.subheader("कन्फ्यूजन मैट्रिक्स" if is_hi else "Confusion Matrix")
        st.caption("सभी सात मिलावट स्तरों (0%, 1%, 2%, 3%, 5%, 7%, 9%) पर सामान्यीकृत वर्ग भविष्यवाणियां।" if is_hi else "Normalized class predictions across all seven adulteration concentrations (0%, 1%, 2%, 3%, 5%, 7%, 9%).")

        cm_path = artifacts["confusion_matrix_path"]
        if cm_path:
            st.image(cm_path, caption="Saved Confusion Matrix from Notebook 9", use_container_width=True)
        else:
            st.info("Confusion matrix image not found.")
