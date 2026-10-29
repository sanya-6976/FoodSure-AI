# FoodSure AI 🧪🌾

## Multimodal AI for Turmeric Adulteration Detection & Quantification

**FoodSure AI** is an AI-assisted research and screening platform designed to detect and quantify wheat-flour adulteration in turmeric powder using multimodal machine learning, ATR-FTIR spectroscopy, and Google Gemini AI.

---

## 🎯 System Capabilities

- **🔬 ATR-FTIR Spectroscopic Analysis:** 2,522 infrared wavenumber features (4000–650 cm⁻¹) compressed via PCA (13 orthogonal components, 90.04% variance).
- **🎯 Dual-Stage Prediction:**
  - **Classification:** Discrete adulteration level identification (`0%`, `1%`, `2%`, `3%`, `5%`, `7%`, `9%`) via Multinomial Logistic Regression.
  - **Quantification:** Continuous percentage estimation (`% w/w`) via Random Forest Regressor (MAE: 0.031%).
- **🤖 Google Gemini AI Analyst:** Interprets spectral findings, generates plain-language scientific summaries, notes uncertainty boundaries, and outlines laboratory verification protocols.
- **🔐 Secure Authentication:** Argon2id password hashing, user registration, login, and user-isolated analysis history in SQLite.
- **📊 Research Dataset Explorer:** Interactive browser for the 350-sample benchmark dataset with ground-truth comparisons.
- **📈 Comprehensive Evaluation Dashboard:** Interactive 5-fold cross-validation metrics across all 21 model/modality configurations, confusion matrix, and holdout evaluation.

---

## 📊 Dataset Provenance

The system is evaluated on the publicly available benchmark:

**Multimodal Dataset for Turmeric Adulteration Detection Using Imaging, ATR-FTIR Spectroscopy, and Color Measurements**  
*Mendeley Data — DOI: `10.17632/cb5kbt7bgv.1`*

- **350 physical samples** across 7 adulteration levels (50 samples each).
- **Adulterant:** Wheat flour mixed w/w under controlled laboratory conditions.
- **Preserved Split:** 280 training samples (40/class) and 70 holdout samples (10/class).

---

## 🔬 Subsystem Audit & Empirical Realities

1. **CNN / Computer Vision:**
   - The repository contains 350 `.JPG` images (4032x3024 RGB) and 1,280 pre-extracted EfficientNet-B0 embedding features (`EfficientNetB0_Image_Features.csv`).
   - No custom deep learning CNN weights (`.pt`, `.pth`, `.h5`) exist in the checkout. Image modeling was evaluated as tabular classification on these 1,280 embeddings (reaching 95.36% SVM accuracy).
2. **FTIR Spectroscopy:**
   - In 5-fold cross-validation on the 280 training samples, FTIR-only Logistic Regression achieved 100% Macro F1, tying all 3-modality fusion configurations.
   - For parsimony, the production model artifact (`models/foodsure_multimodal_v1.joblib`) packages FTIR-only Logistic Regression and Random Forest Regressor.
3. **Evaluation Caveats:**
   - The 70-sample test cohort was previously examined in exploratory notebooks; it is reported as a historically reused benchmark rather than an untouched external test set.
   - The system is a research prototype; results do not replace accredited laboratory wet chemistry or certify food safety.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Virtual environment with dependencies

```powershell
# From the repository root:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and provide your Google Gemini API key:

```powershell
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
APP_ENV=development
```

### 3. Launch the Application

```powershell
cd FoodSure-AI
..\.venv\Scripts\streamlit.exe run app.py
```
*(Or from the workspace root: `.\.venv\Scripts\streamlit.exe run FoodSure-AI\app.py`)*

### 4. Evaluator Login Credentials
For immediate evaluator access:
- **Email:** `researcher@foodsure.ai`
- **Password:** `FoodSure2026!`
*(Or click "Create Account" on the login screen to register a new user profile.)*

---

## 🧪 Running the Test Suite

Run all unit and integration test suites:

```powershell
cd FoodSure-AI
..\.venv\Scripts\python.exe -m unittest tests/test_backend_full.py
..\.venv\Scripts\python.exe -m unittest ai_layer/tests/test_analyst.py
..\.venv\Scripts\python.exe -m unittest ai_layer/tests/test_pipeline.py
..\.venv\Scripts\python.exe -m unittest ai_layer/tests/test_predictor_validation.py
```
