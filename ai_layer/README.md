# FoodSure AI backend

FoodSure AI is a research prototype for classification and regression experiments on controlled turmeric samples adulterated with wheat flour. It combines color measurements, ATR-FTIR spectra, and precomputed image embeddings. It is not a laboratory test, regulatory certification, or validated real-world product.

The project source is the Mendeley dataset [10.17632/cb5kbt7bgv.1](https://data.mendeley.com/datasets/cb5kbt7bgv/1). The Phase 5 ML evaluation and scientific audit is in [../results/phase_05_evaluation_report.md](../results/phase_05_evaluation_report.md).

## Requirements and setup

- Python **3.13** is the validated runtime (the baseline environment used Python 3.13.7).
- Install repository dependencies from the repository root. PowerShell commands:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, invoke the venv interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s ai_layer\tests -v
```

The checked-in `requirements.txt` includes NumPy, pandas, scikit-learn, joblib, and the notebook/data-analysis packages. The optional AI-provider integration imports the OpenAI Python package lazily; it is not a required dependency and is not listed in `requirements.txt`. Install it only if opting into that provider:

```powershell
python -m pip install openai
$env:OPENAI_API_KEY = "<your key in your local environment>"
$env:FOODSURE_LLM_MODEL = "gpt-4.1-mini"
```

Do not put API keys in source files, notebooks, or committed configuration. With no provider key, `use_llm=True` uses the deterministic fallback. Provider-generated narrative is excluded from final pipeline reports because its claims are not independently substantiated.
The Phase 6 verification exercised the no-key fallback only; a live provider request was not run (the OpenAI package and API key were unavailable in that environment).

## Required model artifacts

The saved model artifact is required at this repository-relative location:

- `models/foodsure_multimodal_v1.joblib`

The matching metadata sidecar is shipped at `models/foodsure_multimodal_v1_metadata.json`. It provides the saved feature order and class list and is checked against the serialized estimators when present; without it, metadata-based pipeline context and those cross-checks are unavailable. Keep the model and sidecar together for normal use. The bundle is version `foodsure-ml-v1`, selected classifier Logistic Regression, selected regression estimator Random Forest Regressor, and uses FTIR only. Do not retrain or overwrite the bundle as part of backend integration.

## Test suite and software smoke demonstration

From the repository root:

```powershell
python -m unittest discover -s ai_layer\tests -v
python examples\backend_smoke_demo.py
```

The smoke demo uses a synthetic all-zero FTIR row with the saved metadata's 2,522 ordered FTIR feature names. It exercises the real saved predictor and integrated AI pipeline, checks repeatability, report/disclaimer and uncertainty preservation, invalid-dimension rejection, and the provider-unavailable deterministic fallback. This artificial vector is **not a measured spectrum, scientific sample, accuracy test, or performance result**. The demo prints JSON to standard output; it does not change model artifacts or source data.

The available demo runs without access to the original raw CSVs. To run inference on a real spectrum, use a single-row feature DataFrame with the exact feature names and order in the metadata, populated with the original unscaled FTIR values. That requires the corresponding raw spectrum or a compatible acquisition workflow; do not use generated embeddings or transformed/scaled notebook intermediates in place of the original input features.

## Public inference and pipeline interface

There is **no HTTP server or API endpoint** in this repository. The public Python entry point for a future service is:

```python
from ai_layer.pipeline import run_pipeline

result = run_pipeline(
    {"ftir_features": one_row_ftir_dataframe},
    use_llm=False,
)
```

Exact signature:

```text
run_pipeline(
    request: Mapping[str, Any],
    *,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    use_llm: bool = False,
    detector_result: Mapping[str, Any] | None = None,
    calibration_info: Mapping[str, Any] | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]
```

`request` accepts one or more non-null keys from `color_features`, `ftir_features`, and `image_features`. For the current model, FTIR is required. Feature inputs are one sample each:

| Input | Expected width | Requirements |
|---|---:|---|
| `ftir_features` | 2,522 | Required by the current model. Finite numeric, original unscaled features, in the exact `feature_order["FTIR"]` order in the metadata. A one-row DataFrame is checked by column name and order; positional arrays cannot prove feature order. |
| `color_features` | 46 | Optional at the interface but not used by the current FTIR-only artifact. If supplied, it is validated as a feature input. |
| `image_features` | 1,280 | Optional at the interface but not used by the current FTIR-only artifact. If supplied, it must be a precomputed EfficientNet-B0 embedding, not a raw image. |

The saved scaler and PCA are applied by the predictor. Do not pre-scale or PCA-transform inputs. For a table containing extra columns such as `Sample_ID` and `Target`, select only the saved feature columns before calling inference.

### Returned structures

`result` contains:

- `prediction`: the real predictor dictionary (`predicted_class`, `predicted_percentage`, `modality_configuration`, `model_version`, `probabilities`, and explanatory notes).
- `explanation`: deterministic analysis used by the final report.
- `evidence`: model/version, modalities, prediction mapping, metadata evidence, limitations, and uncertainty flags.
- `uncertainty_warnings` and `uncertainty`: warnings/assessment including confidence, calibration, OOD, and external-validation status where known.
- `model_version`, `modalities_used`, and `model_metadata`.
- `report`: JSON-serializable report with model result, analysis, uncertainty, limitations, verification recommendation, and research-prototype disclaimer.

The classifier returns a discrete class string such as `"7%"`; it is a predicted class label, not a measured adulteration percentage. `predicted_percentage` is the separate continuous regression estimate on the dataset's numeric percentage-level target scale. It is unconstrained and is not a laboratory measurement. Probabilities are `None`: calibration has not been established.

`detector_result`, `calibration_info`, and `evidence_items` are optional. Do not supply invented detector or calibration results. Evidence supplied by a caller is marked unverified. Without a supplied detector, OOD status remains unknown. Inference/input failures raise errors and do not return a report based on an earlier prediction.

### Error handling and troubleshooting

- Missing model/metadata files: restore the matching saved files at the locations above; do not substitute a different bundle or sidecar.
- Wrong feature count, nonnumeric/nonfinite values, missing required FTIR, or reordered named columns: check the saved feature order and provide one unscaled sample row.
- `ModuleNotFoundError` for project dependencies: activate the project venv and install `requirements.txt`.
- Provider unavailable, malformed response, or provider error: the analyst uses deterministic fallback. The pipeline's final report still uses deterministic analysis; LLM narrative is excluded.
- Smoke demo reports a synthetic prediction: expected for its artificial all-zero input; do not interpret it as evidence about turmeric or model accuracy.

## Scientific and validation limits

- The Phase 5 report found perfect FTIR classification in the recorded five-fold CV and fixed-split results, but it does not establish generalization. The same 70-sample holdout was repeatedly examined in earlier notebooks, so it is not a fresh independent test.
- Saved label CSVs are not positionally aligned with the shuffled split-ID files. Training/evaluation must join labels to features by sample ID; do not pair those arrays to the shuffled IDs by position.
- Dataset documentation identifies `Sxx` as a sample number/index but does not establish whether indexed records are independent prepared specimens, repeated measurements, or batch-related. Group leakage cannot be ruled out from the available protocol/metadata.
- The data are controlled wheat-flour adulteration experiments. Independent external validation, probability calibration, and applicability to other adulterants, products, instruments, or laboratories have not been established.
- No sample-specific feature attributions are generated. Predictions are screening research outputs, not laboratory confirmation, FSSAI approval, or certification.

Before consequential use, obtain specimen/batch provenance, perform group-aware evaluation if required by that provenance, and validate on independently collected samples with an appropriate laboratory reference.
