# FoodSure AI — Phase 5 ML Evaluation and Scientific Audit

**Audit date:** 2026-10-15  
**Scope:** Read-only evaluation of the existing Notebook 9 experiment, saved predictions/results, model metadata and relevant earlier notebooks. No models were retrained; Notebook 9, model artifacts, raw data, split files, and historical result files were not modified. The only deliverable created for this phase is this report.

## Executive assessment

The saved Notebook 9 results are reproducible from their fold and prediction CSVs. Its FTIR-only Logistic Regression classification achieved 1.0000 on every reported five-fold training-CV metric and on the 70-row fixed test split. I found no explicit target column in model features, no exact FTIR duplicate spectra, no cross-split exact feature-vector duplicates, and no fold-preprocessing leakage in the Notebook 9 workflow. Those checks do **not** explain why FTIR is perfectly separable, establish independence of specimens, or demonstrate performance beyond the controlled dataset.

The final Notebook 9 code selects using training CV and evaluates the held-out IDs after selection. However, the same 70 IDs were already repeatedly evaluated for model/modality comparisons in Notebooks 4–6. The final test score is therefore reproducible but **not an untouched, independent confirmation**. Dataset documentation defines IDs as `T{level}S{sample number}` and says the `Sxx` part is a sample index. 39 of the 50 suffix values occur in both split partitions, but shared index numbers across concentration classes do not establish that records are related replicates or batches. The available documentation still does not establish whether each indexed sample is an independent experimental unit.

**Conclusion:** evidence supports FTIR as a compact, strong classifier on this controlled fixed split. Fusion ties rather than improves its CV results. The evidence is insufficient for generalization, certification, or real-world screening claims. A group-aware, independently collected evaluation is needed before those claims.

## 1. Experimental setup and provenance

| Item | Verified setup |
|---|---|
| Raw data | 350 records in each modality: sibling workspace `Multimodal Dataset for Turmeric Adulteration Detec/Color Measurement/Hunter_Lab_colorimeter.csv`, `.../FTIR Spectroscopy/FTIR_Data.csv`, and `.../Image/EfficientNetB0_Image_Features/EfficientNetB0_Image_Features.csv`. Notebook 9 reports those same resolved paths. The repository README and the dataset README identify the Mendeley Data set, DOI [`10.17632/cb5kbt7bgv.1`](https://data.mendeley.com/datasets/cb5kbt7bgv/1). The dataset README describes 350 samples with 50 per class. The publisher's description says samples were prepared under controlled laboratory conditions by mixing pure turmeric powder and wheat flour at predefined w/w levels. |
| Target | Raw `Target`, parsed numerically after removing `%`; seven controlled wheat-flour adulteration levels: 0, 1, 2, 3, 5, 7, and 9. Classification predicts one of these discrete levels; regression estimates the numeric target separately. |
| Features | Color: 46; FTIR: 2,522; Image: 1,280 precomputed EfficientNet-B0 embedding values. `Sample_ID` is the index/join key and `Target` is dropped from the feature frame; neither is passed as a feature. |
| Split | Existing stratified 280/70 split, random state 42. Each training class has 40 samples; each test class has 10. IDs are unique and have no train/test overlap. Ordered ID hashes match the values saved in the model metadata. |
| CV | `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` over training IDs only. Each validation fold has 56 samples (8/class); fold fit sets have 224. |
| Classification | Logistic Regression, RBF SVM, Random Forest across Color, FTIR, Image, all three pairwise combinations, and the three-modality combination: 21 model/configuration comparisons. |
| Regression | Ridge Regression and Random Forest Regressor on FTIR and Color + FTIR. These are the best individual and best fusion configurations selected from the classification comparison, not an exhaustive regression search over all modalities. |
| Preprocessing | Notebook 9 fits a separate `StandardScaler` inside each training fold; FTIR and Image also fit fold-local `PCA(n_components=0.90)`. Validation rows are only transformed. Final preprocessing is refit on the 280 training rows and applied to the test rows. No target inverse-transform is required: targets remain in the raw numeric level scale. |
| Selection | CV results select the classifier/configuration; held-out performance does not enter that selection. Ties are resolved by stable sorting favoring fewer modalities and then Logistic Regression. Regression selection is restricted to the selected classifier configuration. |

Primary provenance:

- Methods and executed cells: [notebook/09_final.ipynb](../notebook/09_final.ipynb)
- Data loading, fold evaluation, selection, and model writing: [ml_service/experiments.py](../ml_service/experiments.py)
- Saved CV means/stds: [results/notebook_09/fusion_cv_results.csv](notebook_09/fusion_cv_results.csv)
- Fold-level classification metrics: [results/notebook_09/fusion_cv_fold_results.csv](notebook_09/fusion_cv_fold_results.csv)
- ID-tagged CV out-of-fold predictions: [results/notebook_09/fusion_oof_predictions.csv](notebook_09/fusion_oof_predictions.csv)
- Fold preprocessing fit-row evidence: [results/notebook_09/fusion_fold_preprocessing.csv](notebook_09/fusion_fold_preprocessing.csv)
- Regression means/stds and folds: [results/notebook_09/regression_results.csv](notebook_09/regression_results.csv), [results/notebook_09/regression_fold_results.csv](notebook_09/regression_fold_results.csv)
- ID-tagged regression OOF predictions: [results/notebook_09/regression_oof_predictions.csv](notebook_09/regression_oof_predictions.csv)
- Fixed-split test metrics and predictions: [results/notebook_09/fusion_holdout_results.csv](notebook_09/fusion_holdout_results.csv), [results/notebook_09/fusion_holdout_predictions.csv](notebook_09/fusion_holdout_predictions.csv)
- Saved model selection and split/preprocessing metadata: [models/foodsure_multimodal_v1_metadata.json](../models/foodsure_multimodal_v1_metadata.json)

## 2. Classification results — existing Notebook 9 CV results

Each cell is the **mean ± population standard deviation across five fold-level scores**. These are not confidence intervals and are not the pooled OOF metric. The reported metrics were independently reconciled against the five rows per configuration in `fusion_cv_fold_results.csv`; no discrepancies were found.

| Modalities | Model | Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---|---:|---:|---:|---:|
| Color | Logistic Regression | 0.9714 ± 0.0214 | 0.9754 ± 0.0186 | 0.9714 ± 0.0214 | 0.9710 ± 0.0219 |
| Color | SVM (RBF) | 0.9393 ± 0.0368 | 0.9469 ± 0.0318 | 0.9393 ± 0.0368 | 0.9376 ± 0.0391 |
| Color | Random Forest | 0.9429 ± 0.0364 | 0.9500 ± 0.0374 | 0.9429 ± 0.0364 | 0.9421 ± 0.0365 |
| FTIR | Logistic Regression | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| FTIR | SVM (RBF) | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| FTIR | Random Forest | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Image | Logistic Regression | 0.9464 ± 0.0357 | 0.9506 ± 0.0331 | 0.9464 ± 0.0357 | 0.9456 ± 0.0366 |
| Image | SVM (RBF) | 0.9536 ± 0.0290 | 0.9581 ± 0.0272 | 0.9536 ± 0.0290 | 0.9533 ± 0.0291 |
| Image | Random Forest | 0.9000 ± 0.0460 | 0.9141 ± 0.0378 | 0.9000 ± 0.0460 | 0.8968 ± 0.0479 |
| Color + FTIR | Logistic Regression | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + FTIR | SVM (RBF) | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + FTIR | Random Forest | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + Image | Logistic Regression | 0.9714 ± 0.0143 | 0.9752 ± 0.0124 | 0.9714 ± 0.0143 | 0.9712 ± 0.0144 |
| Color + Image | SVM (RBF) | 0.9714 ± 0.0182 | 0.9748 ± 0.0155 | 0.9714 ± 0.0182 | 0.9712 ± 0.0184 |
| Color + Image | Random Forest | 0.9536 ± 0.0416 | 0.9562 ± 0.0412 | 0.9536 ± 0.0416 | 0.9534 ± 0.0418 |
| FTIR + Image | Logistic Regression | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| FTIR + Image | SVM (RBF) | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| FTIR + Image | Random Forest | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + FTIR + Image | Logistic Regression | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + FTIR + Image | SVM (RBF) | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Color + FTIR + Image | Random Forest | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |

The best individual configuration and best fusion both score 1.0000 CV Macro F1. Fusion therefore **ties; it does not improve** the strongest single modality. FTIR + Logistic Regression is a reasonable parsimonious selection among the tied results, not evidence that fusion adds value.

### Existing fixed-split test result

Notebook 9's saved 70 prediction rows contain 70 unique test IDs and have zero actual-target mismatches against targets rejoined from raw CSVs by ID. Recalculated metrics from those saved predictions exactly match `fusion_holdout_results.csv`:

| Selected model/configuration | Accuracy | Macro precision | Macro recall | Macro F1 | Samples |
|---|---:|---:|---:|---:|---:|
| FTIR + Logistic Regression | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 70 |

This is a single fixed-split score, not CV stability. Its independence is compromised by prior repeated use of this test split in earlier notebook experiments (see Section 5).

## 3. Regression results — separate estimation task

Notebook 9 reports fold-level metrics summarized as five-fold **mean ± population standard deviation**. MAE/RMSE use the target's percentage-level numeric scale (percentage points); R² is dimensionless. These estimates are not classification accuracy or laboratory measurements.

| Modalities | Model | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| FTIR | Ridge Regression | 0.2484 ± 0.0261 | 0.3310 ± 0.0447 | 0.9880 ± 0.0031 |
| FTIR | Random Forest Regressor | 0.0314 ± 0.0451 | 0.1832 ± 0.3246 | 0.9850 ± 0.0299 |
| Color + FTIR | Ridge Regression | 0.1921 ± 0.0197 | 0.2575 ± 0.0351 | 0.9927 ± 0.0019 |
| Color + FTIR | Random Forest Regressor | 0.0421 ± 0.0198 | 0.1301 ± 0.1004 | 0.9971 ± 0.0042 |

The saved Notebook 9 holdout predictions contain regression estimates only for selected FTIR + Random Forest Regressor: **MAE 0.0118, RMSE 0.0302, R² 0.9999** on 70 samples. No Notebook 9 held-out regression predictions are provided for Color + FTIR, so no final-split comparison of that regressor is reported.

Regression interpretation needs care. FTIR Random Forest has lower mean CV MAE than Color + FTIR Random Forest, while the latter has lower mean CV RMSE and higher mean CV R². FTIR Random Forest is also unstable across folds: fold 2 has MAE 0.1217 and RMSE 0.8324, whereas the other fold RMSEs are near 0.02. The reported mean-fold RMSE is 0.1832; pooling all 280 OOF residuals and taking one square root gives RMSE 0.3727. These are different aggregation definitions, not a discrepancy in the saved fold summary.

Notebook 9 evaluates regression only for FTIR and Color + FTIR, configurations chosen from the classification comparison. It does not establish the best regression modality/configuration overall. Older Notebook 5/6 tables did repeatedly compare regressors on the same fixed test set; for example, Notebook 5 reports FTIR Random Forest MAE 0.0112, RMSE 0.0289, R² 0.9999, and Notebook 6 reports Color + FTIR Random Forest MAE 0.013524, RMSE 0.031259, R² 0.999895. These are **historical reused-holdout results**, not independent validation, and should not be pooled with Notebook 9's CV results.

Regression predictions are unconstrained. The saved FTIR Ridge OOF predictions include negative values and values below zero-target range; no clipping or inverse target transform is applied. The model API describes its regression output as an unconstrained research estimate.

## 4. Investigation of perfect FTIR classification scores

### Confirmed safe for the inspected Notebook 9 path

- All three raw modality files have 350 unique IDs. Each raw table has the same row ordering across modalities in the present data.
- Notebook 9 uses the `Target` only as y and removes it from X; `Sample_ID` is used for ID joins and not included as a feature. No feature name suggests an ID, target, class, or adulteration label.
- Notebook 9 uses the preserved train/test IDs, verifies target agreement between modalities after joining by ID, and validates saved target exports without aligning them positionally to shuffled IDs.
- The 280 training IDs and 70 test IDs are unique, disjoint, and have per-class counts of 40 and 10. Their ordered SHA-256 values match the metadata associated with the fitted artifact.
- The saved OOF predictions include every training ID exactly once per model/configuration (280 each); all `Actual` labels match raw targets by ID. The classification CV table reconciles exactly to its five fold rows.
- Scaling and PCA are fitted on each fold's 224 training rows only. The saved fold-preprocessing CSV records 224 fit rows and 56 validation rows for each fold/modality. The final model's preprocessing is fit on the 280 training rows; test rows are transformed, not used to fit.
- No exact duplicate Color or FTIR feature rows were found. One identical pair of Image embedding vectors was found (`T0S09`, `T0S10`); both belong to class 0 and the training partition. No identical feature-vector group spans train and test in any modality.

### Confirmed issues and unresolved causes

- **Confirmed historical holdout reuse:** Notebooks 4–6 repeatedly report model/modality comparisons on the same 70 test samples. Notebook 9's own selection uses CV only, but its fixed test set was already exposed in earlier experiments; it is not a fresh blind test.
- **Unresolved specimen independence / group dependence:** The dataset README.docx and Mendeley dataset description define the ID pattern as `T{level}S{sample index}` (the local README says `T` = turmeric, the number = adulteration level, `Sxx` = sample number; the publisher calls it a sample index). All 350 IDs match this convention, with each prefix mapping exactly to one target and each of the 50 suffix values occurring once at each level. The shared suffix values across train and test are therefore an index-pattern observation, not evidence that cross-class samples share a physical specimen or batch. Neither local documentation nor the publisher description says whether the 50 indexed samples per class are independent physical experimental units, repeated measurements, or draws from shared preparation batches. No sample-group field or detailed experimental protocol is present in the accessible project/data README files. Consequently, grouping cannot be defined from available evidence and group leakage cannot be ruled out; it is also not established by suffix overlap alone.
- **No direct FTIR duplication evidence:** No exact FTIR vectors or explicit target-derived feature columns were found, and preprocessing is fold-local. This rules out those specific simple failure modes, but not subtler source/batch/instrument effects or correlated replicate leakage.
- **The mechanism for perfect performance is not established.** Perfect FTIR scores may reflect strong, repeatable spectral separation of controlled concentrations. Available artifacts do not establish specimen independence or rule out group-level structure. The score should therefore be described as observed separability within this dataset, not proof of generalization.

## 5. Sample-ID / target-alignment and historical-result audit

The train/test ID CSVs are shuffled by `train_test_split`. Notebook 3 then filters the master target table and each modality table using `.isin(train_ids/test_ids)`. Pandas preserves each source table's row order. In this dataset, raw Color, FTIR, and Image ID row orders match; therefore the preprocessed feature arrays and saved y arrays produced by that historical procedure have the same original-row membership order. This explains why `y_train.csv` and `y_test.csv` differ from the shuffled ID lists positionally by **248/280** and **56/70** entries without proving that Notebook 3's corresponding feature/label arrays were misaligned.

The distinction matters: positional mismatch is a real hazard if those y arrays are later paired directly with the shuffled ID CSV order. Notebook 9 avoids that hazard by indexing raw targets/features with IDs. The Notebook 9 prediction and OOF CSVs include IDs and were independently checked against the raw ID-to-target mapping. Older Notebook 4–6 result tables do not contain row-level IDs; their generation path is order-preserving and appears aligned, but their saved aggregate outputs alone cannot independently prove every individual prediction's sample identity.

**Historical conclusions requiring qualification:** earlier held-out scores from Notebooks 4–6 should be treated as exploratory fixed-split comparisons. Their preprocessing in Notebook 3 fits scalers/PCA on training arrays and transforms test arrays, but the heldout split is evaluated repeatedly for many model/modality/regression configurations. Notebook 9 provides a cleaner CV-driven selection path, yet it cannot restore the test set's prior untouched status.

## 6. Classification/regression selection and research conclusions

- The saved artifact and metadata verify **FTIR + Logistic Regression** as the selected classification model/configuration; **FTIR + Random Forest Regressor** is the associated regression estimator.
- FTIR alone ties all tested FTIR-containing fusions at perfect measured CV scores; neither color nor image fusion improves those metrics. If only controlled-dataset CV performance and parsimony are considered, FTIR-only Logistic Regression is a defensible choice.
- This does not establish that FTIR will be best on new specimens, adulterants, devices, preparation batches, or laboratories.
- Regression conclusions are different: Color + FTIR Random Forest has better mean RMSE/R² than FTIR Random Forest in the restricted Notebook 9 CV set, but larger mean MAE. The instability and limited configuration scope preclude declaring one universally superior regression pipeline.
- No verified Notebook 9 experiment establishes a Transformer as superior. The evidence does not support novelty, certification, regulatory approval, or deployment-readiness claims.

## 7. Findings by evidence status

| Status | Finding |
|---|---|
| Confirmed safe (scoped to Notebook 9 code/artifacts) | ID joins and targets are correctly applied; no train/test ID overlap; modality targets agree; target and sample ID are excluded from features; fold-local scaling/PCA; CV and OOF metrics reconcile; final model metadata matches split hashes. |
| Confirmed issue | Saved y arrays are not in the shuffled split-ID order; pairing them positionally with those ID files would be wrong. Earlier Notebooks 4–6 repeatedly inspected the same holdout, so it is no longer an untouched final test. |
| Confirmed data observation | Two Image rows have identical embeddings within the training partition and the same target; no exact duplicate vectors cross train/test. |
| Partially documented; unresolved | `Sxx` is defined as the sample number/index within the target-coded prefix. The available source does not establish the underlying experimental unit, replicate structure, or batch relationships. Shared suffix values across target prefixes do not prove common specimens; group leakage cannot be ruled out without protocol/group metadata. |
| Unresolved | Whether the controlled samples represent independent naturally collected turmeric specimens, and whether instrument/acquisition batch effects drive separation. |
| Not established | Independent external validation; probability calibration; performance on other adulterants, concentrations, instruments, laboratories, or real-world products. |

## 8. Verification performed and methodology

This audit did **not** refit or retrain models. It used the configured project Python 3.13 venv, read-only loading of the existing raw CSVs and saved result CSVs, and metric recomputation from saved predictions:

1. Loaded the current source datasets using the existing `ml_service.experiments._load_data` path, which validates ID set membership, target agreement, class counts, split sizes, and the positional export convention.
2. Recomputed classification summary means and population standard deviations from the five rows per configuration in `fusion_cv_fold_results.csv`; verified them against `fusion_cv_results.csv`.
3. Verified every OOF `Actual` value against raw targets indexed by `Sample_ID`, and verified 280 unique OOF IDs per model/configuration.
4. Recomputed the final classification metrics and regression metrics from the 70 ID-tagged rows in `fusion_holdout_predictions.csv`; compared them with `fusion_holdout_results.csv`.
5. Checked exact duplicate feature-vector groups in each raw modality and whether any such group crossed the saved split.
6. Inspected executed source/output cells in Notebooks 3–6 and 9 to assess feature creation, split/filter ordering, preprocessing, and repeated test-set comparisons.

No additional model evaluation, fit, or new split was performed. Thus, the report contains **existing metrics**, plus **reproductions from saved fold/prediction outputs**, not newly trained-model results.

## 9. Recommended next actions

1. Obtain the original laboratory protocol or dataset authors' clarification on whether each `Sxx` sample number denotes an independent prepared specimen, a repeat measurement, or a shared preparation/batch unit. Do not use suffix values as groups unless that relationship is confirmed. If samples share experimental units, rerun evaluation with group-aware CV and group-disjoint test partitions.
2. Treat the existing 70-sample test as historically reused. Freeze model choices before collecting a new independent external test cohort; do not tune on that cohort.
3. For regression, predefine the candidate configurations and selection metric, evaluate them in training CV, and report CV and untouched-test results separately. Include all regression modality configurations only if scientifically justified.
4. Preserve raw ID-keyed targets/features in future intermediate artifacts so prediction identity is auditable end-to-end; do not pair the saved y arrays with shuffled IDs positionally.
5. Evaluate independent specimens from other preparations, instruments, operators, and laboratories, and assess calibration/uncertainty before any consequential use.

**Final judgment:** Notebook 9's computational results are internally reproducible and its inspected preprocessing/split implementation has no identified direct feature/target leakage. The scientific validity of the perfect scores remains conditional on unresolved sample grouping and dataset provenance, and the reused holdout cannot serve as fresh independent validation. Suitable for controlled-dataset research reporting only; **not ready for real-world performance claims or deployment decisions**.
