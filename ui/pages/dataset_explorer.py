"""Dataset explorer page for FoodSure AI — Bilingual."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backend.service import load_raw_dataset
from ui.components import page_header
from ui.i18n import get_current_language


def render_dataset_explorer() -> None:
    is_hi = get_current_language() == "hi"

    eyebrow = "डेटासेट स्रोत" if is_hi else "DATASET PROVENANCE"
    title = "बहुमाध्यम शोध डेटासेट" if is_hi else "Multimodal Research Dataset"
    desc = (
        "मेंडेली डेटा (DOI: 10.17632/cb5kbt7bgv.1) पर प्रकाशित मानक अनुसंधान डेटासेट का अन्वेषण करें।"
        if is_hi
        else "Explore the benchmark research dataset published on Mendeley Data (DOI: 10.17632/cb5kbt7bgv.1)."
    )

    page_header(eyebrow, title, desc)

    try:
        data = load_raw_dataset()
    except Exception as exc:
        st.error(f"डेटासेट लोड नहीं हो सका: {exc}" if is_hi else f"Could not load raw dataset: {exc}")
        return

    # Dataset High-Level Overview
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("कुल नमूने" if is_hi else "Total Samples", "350", "50 per class")
    with c2:
        st.metric("प्रशिक्षण विभाजन" if is_hi else "Training Split", "280", "40 per class (80%)")
    with c3:
        st.metric("होल्डआउट विभाजन" if is_hi else "Holdout Split", "70", "10 per class (20%)")
    with c4:
        st.metric("श्रेणियां" if is_hi else "Classes", "7", "0%, 1%, 2%, 3%, 5%, 7%, 9%")

    st.markdown("---")

    tab_labels = (
        ["विभाजन विवरण", "नमूना निरीक्षण", "माध्यम फीचर आयाम"]
        if is_hi
        else ["Split Breakdown", "Sample Inspection", "Modality Feature Dimensions"]
    )
    tab_overview, tab_samples, tab_modalities = st.tabs(tab_labels)

    with tab_overview:
        st.subheader("संरक्षित विभाजन आवंटन" if is_hi else "Preserved Partition Allocation")

        train_y = data["y_train"].value_counts().sort_index()
        test_y = data["y_test"].value_counts().sort_index()

        breakdown_df = pd.DataFrame({
            "Adulteration Level": [f"{lvl:g}%" for lvl in train_y.index],
            "Training Samples": train_y.values,
            "Holdout Samples": test_y.values,
            "Total Samples": train_y.values + test_y.values,
        })
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        st.caption("सभी 350 नमूनों को सटीक स्तरीकरण के साथ 280 प्रशिक्षण नमूनों और 70 परीक्षण नमूनों में विभाजित किया गया है।" if is_hi else "All 350 samples are partitioned into 280 training samples and 70 test samples with exact stratification.")

    with tab_samples:
        st.subheader("श्रेणी अनुसार नमूने ब्राउज़ करें" if is_hi else "Browse Samples by Class")

        level_choice = st.selectbox("मिलावट स्तर चुनें" if is_hi else "Select Adulteration Level", ["0%", "1%", "2%", "3%", "5%", "7%", "9%"])
        level_numeric = float(level_choice.rstrip("%"))

        target_map = dict(zip(data["train_ids"], data["y_train"]))
        target_map.update(dict(zip(data["test_ids"], data["y_test"])))

        matching_ids = [sid for sid, tgt in target_map.items() if float(tgt) == level_numeric]

        st.write(f"श्रेणी **{level_choice}** के लिए **{len(matching_ids)}** नमूने मिले:" if is_hi else f"Found **{len(matching_ids)}** samples for class **{level_choice}**:")

        sample_rows = []
        for sid in matching_ids:
            is_tr = sid in set(data["train_ids"])
            sample_rows.append({
                "Sample ID": sid,
                "Adulteration Target": f"{level_numeric:g}%",
                "Partition": "Training (280)" if is_tr else "Holdout (70)",
                "Status": "Pure Turmeric" if level_numeric == 0.0 else "Adulterated",
            })

        st.dataframe(pd.DataFrame(sample_rows), use_container_width=True, hide_index=True)

    with tab_modalities:
        st.subheader("माध्यमों में फीचर रिक्त स्थान" if is_hi else "Feature Spaces Across Modalities")

        mod_info = [
            {
                "Modality": "ATR-FTIR Spectroscopy",
                "Feature Count": data["features"]["FTIR"].shape[1],
                "Representation": "Raw unscaled absorbance across wavenumbers 4000–650 cm⁻¹",
                "Integration Status": "Active Production Model (PCA 13 components)",
            },
            {
                "Modality": "Hunter Lab Colorimeter",
                "Feature Count": data["features"]["Color"].shape[1],
                "Representation": "L*, a*, b*, chroma, hue, and reflectance indices",
                "Integration Status": "Evaluated Baseline (PCA 3 components)",
            },
            {
                "Modality": "Image (EfficientNet-B0)",
                "Feature Count": data["features"]["Image"].shape[1],
                "Representation": "Deep convolutional feature embeddings pre-extracted from 4032x3024 RGB photos",
                "Integration Status": "Tabular Embeddings Benchmark",
            },
        ]
        st.dataframe(pd.DataFrame(mod_info), use_container_width=True, hide_index=True)
