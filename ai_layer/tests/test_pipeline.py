"""Integration tests for the FoodSure predictor/AI-layer adapter."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from ai_layer.analyst import AnalystError
from ai_layer.pipeline import (
    PipelineInputError,
    PipelineOutputError,
    run_pipeline,
)


class TestFoodSurePipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.model_path = Path(self.temp_dir.name) / "synthetic-test-model.joblib"
        self.metadata_path = self.model_path.with_name(
            f"{self.model_path.stem}_metadata.json"
        )
        self.metadata = {
            "model_version": "synthetic-test-v1",
            "classification_model": "Synthetic Test Classifier",
            "regression_model": "Synthetic Test Regressor",
            "modality_configuration": ["FTIR"],
            "feature_order": {"FTIR": ["synthetic_feature_1", "synthetic_feature_2"]},
            "pca_components_and_explained_variance": {"FTIR": None},
            "training_split": {
                "training_sample_count": 280,
                "heldout_sample_count": 70,
            },
            "class_labels_percentage": [0, 1, 2, 3, 5, 7, 9],
            "probability_calibration": "Not assessed; synthetic test fixture.",
        }
        self.metadata_path.write_text(
            json.dumps(self.metadata),
            encoding="utf-8",
        )
        self.request = {
            "ftir_features": pd.DataFrame(
                [[1.25, 2.5]],
                columns=["synthetic_feature_1", "synthetic_feature_2"],
            )
        }
        self.prediction = {
            "predicted_class": "3%",
            "predicted_percentage": 3.2,
            "modality_configuration": ["FTIR"],
            "model_version": "synthetic-test-v1",
            "probabilities": None,
            "probability_note": "Synthetic test output; no probability supplied.",
            "regression_note": "Synthetic test estimate.",
        }

    def _run_mocked(self, *, use_llm=False):
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            return run_pipeline(
                self.request,
                model_path=self.model_path,
                use_llm=use_llm,
            )

    def test_classification_and_regression_are_kept_separate(self):
        result = self._run_mocked()

        self.assertEqual(result["prediction"], self.prediction)
        self.assertEqual(
            result["evidence"]["model_result"]["classification_label"],
            "3%",
        )
        self.assertFalse(
            result["evidence"]["model_result"]["classification_label_is_measurement"]
        )
        self.assertEqual(
            result["evidence"]["model_result"]["regression_estimate"],
            3.2,
        )
        self.assertEqual(result["modalities_used"], ["FTIR"])

    def test_detector_and_calibration_facts_are_used_only_when_supplied(self):
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            result = run_pipeline(
                self.request,
                model_path=self.model_path,
                detector_result={
                    "out_of_distribution": False,
                    "detector_name": "Synthetic test detector",
                },
                calibration_info={
                    "confidence": 0.8,
                    "calibrated": True,
                },
            )

        self.assertFalse(result["uncertainty"]["out_of_distribution"])
        self.assertEqual(result["uncertainty"]["confidence"], 0.8)
        self.assertTrue(result["uncertainty"]["confidence_calibrated"])

    def test_missing_metadata_and_evidence_are_reported_as_unknown(self):
        self.metadata_path.unlink()
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            result = run_pipeline(self.request, model_path=self.model_path)

        self.assertIsNone(result["model_metadata"])
        self.assertTrue(any("sidecar is unavailable" in flag for flag in result["uncertainty_warnings"]))
        self.assertTrue(any("No sample-specific feature attribution" in flag for flag in result["uncertainty_warnings"]))
        self.assertTrue(any("scope was not assessed" in flag for flag in result["uncertainty_warnings"]))
        self.assertTrue(any("availability was not supplied" in flag for flag in result["uncertainty_warnings"]))

    def test_malformed_request_and_invalid_feature_dimension_are_rejected(self):
        with self.assertRaises(PipelineInputError):
            run_pipeline({}, model_path=self.model_path)
        with self.assertRaises(PipelineInputError):
            run_pipeline(
                {"unexpected_features": [1, 2]},
                model_path=self.model_path,
            )

        with patch(
            "ai_layer.pipeline.predict_sample",
            side_effect=ValueError("FTIR requires 2 features; received 1"),
        ):
            with self.assertRaisesRegex(ValueError, "requires 2 features"):
                run_pipeline(self.request, model_path=self.model_path)

    def test_predictor_exception_is_reported(self):
        with patch(
            "ai_layer.pipeline.predict_sample",
            side_effect=RuntimeError("synthetic predictor failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic predictor failure"):
                run_pipeline(self.request, model_path=self.model_path)

    def test_invalid_predictor_output_and_version_mismatch_are_rejected(self):
        invalid = dict(self.prediction, probabilities=[0.1, 0.9])
        with patch("ai_layer.pipeline.predict_sample", return_value=invalid):
            with self.assertRaisesRegex(PipelineOutputError, "probabilities"):
                run_pipeline(self.request, model_path=self.model_path)

        invalid = dict(self.prediction, model_version="unexpected-version")
        with patch("ai_layer.pipeline.predict_sample", return_value=invalid):
            with self.assertRaisesRegex(PipelineOutputError, "does not match"):
                run_pipeline(self.request, model_path=self.model_path)

    def test_unsupported_class_and_non_finite_regression_output_are_rejected(self):
        invalid = dict(self.prediction, predicted_class="4%")
        with patch("ai_layer.pipeline.predict_sample", return_value=invalid):
            with self.assertRaisesRegex(PipelineOutputError, "not supported"):
                run_pipeline(self.request, model_path=self.model_path)

        invalid = dict(self.prediction, predicted_percentage=float("inf"))
        with patch("ai_layer.pipeline.predict_sample", return_value=invalid):
            with self.assertRaisesRegex(PipelineOutputError, "finite numeric"):
                run_pipeline(self.request, model_path=self.model_path)

        invalid = dict(self.prediction, predicted_percentage=None)
        with patch("ai_layer.pipeline.predict_sample", return_value=invalid):
            with self.assertRaisesRegex(PipelineOutputError, "finite numeric"):
                run_pipeline(self.request, model_path=self.model_path)

    def test_malformed_metadata_class_list_is_rejected(self):
        self.metadata["class_labels_percentage"] = ["not-a-class"]
        self.metadata_path.write_text(json.dumps(self.metadata), encoding="utf-8")
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            with self.assertRaisesRegex(PipelineOutputError, "class_labels_percentage"):
                run_pipeline(self.request, model_path=self.model_path)

    def test_unavailable_llm_uses_deterministic_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with patch(
                "ai_layer.analyst._call_llm",
                side_effect=AnalystError("synthetic provider unavailable"),
            ):
                result = self._run_mocked(use_llm=True)

        self.assertEqual(
            result["explanation"]["analysis_mode"],
            "deterministic_fallback",
        )
        self.assertIn("provider_note", result["explanation"])

    def test_unverified_llm_claim_is_excluded_from_report(self):
        unsupported_analysis = {
            "summary": "The product is FSSAI certified.",
            "model_result": {
                "prediction": "3%",
                "target_type": "classification label",
            },
            "supporting_evidence": ["Unsupported claim."],
            "interpretation": "The result is certainly accurate.",
            "uncertainty_notes": [],
            "limitations": [],
            "recommended_verification": "No verification is necessary.",
            "analysis_mode": "llm",
        }
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            with patch("ai_layer.pipeline.analyze", return_value=unsupported_analysis):
                result = run_pipeline(
                    self.request,
                    model_path=self.model_path,
                    use_llm=True,
                )

        self.assertEqual(
            result["explanation"]["analysis_mode"],
            "deterministic_fallback",
        )
        self.assertNotIn("FSSAI certified", result["report"]["analysis"]["summary"])
        self.assertTrue(any("LLM-generated narrative was excluded" in flag for flag in result["uncertainty_warnings"]))

    def test_report_is_json_serializable_without_fabricated_probabilities_or_explanations(self):
        result = self._run_mocked()
        serialized = json.dumps(result["report"], allow_nan=False)

        self.assertIn('"model_version": "synthetic-test-v1"', serialized)
        self.assertIsNone(result["prediction"]["probabilities"])
        self.assertTrue(any("No sample-specific feature attribution" in flag for flag in result["uncertainty_warnings"]))
        self.assertFalse(
            any("feature_contributions" in item for item in result["evidence"]["evidence"])
        )
        self.assertFalse(
            any("SHAP" in item.get("description", "") for item in result["evidence"]["evidence"])
        )

    def test_caller_evidence_is_explicitly_marked_unverified(self):
        with patch("ai_layer.pipeline.predict_sample", return_value=self.prediction):
            result = run_pipeline(
                self.request,
                model_path=self.model_path,
                evidence_items=[{
                    "description": "Synthetic test evidence",
                    "source": "synthetic test fixture",
                }],
            )
        caller_evidence = next(
            item
            for item in result["evidence"]["evidence"]
            if item["description"] == "Synthetic test evidence"
        )
        self.assertIn("not independently verified", caller_evidence["source"])

    def test_invalid_calibration_metadata_is_rejected_before_inference(self):
        with patch("ai_layer.pipeline.predict_sample") as predictor:
            with self.assertRaisesRegex(PipelineInputError, "confidence from 0 to 1"):
                run_pipeline(
                    self.request,
                    model_path=self.model_path,
                    calibration_info={"confidence": float("nan"), "calibrated": True},
                )
        predictor.assert_not_called()

    def test_data_loader_rejoins_modalities_and_targets_by_sample_id(self):
        from ml_service.experiments import _load_data

        root = Path(__file__).resolve().parents[2]
        loaded = _load_data(root)
        train_ids = set(loaded["train_ids"])
        test_ids = set(loaded["test_ids"])
        self.assertEqual(len(train_ids), 280)
        self.assertEqual(len(test_ids), 70)
        self.assertFalse(train_ids & test_ids)
        for modality, features in loaded["features"].items():
            self.assertEqual(features.index.nunique(), 350)
            self.assertEqual(features.loc[loaded["train_ids"]].shape[0], 280)
            self.assertEqual(features.loc[loaded["test_ids"]].shape[0], 70)
            self.assertEqual(
                loaded["paths"][modality].name,
                {"Color": "Hunter_Lab_colorimeter.csv", "FTIR": "FTIR_Data.csv",
                 "Image": "EfficientNetB0_Image_Features.csv"}[modality],
            )
        color_targets = pd.read_csv(loaded["paths"]["Color"]).set_index("Sample_ID")[
            "Target"
        ]
        color_targets.index = color_targets.index.astype(str).str.strip()
        color_targets = pd.to_numeric(
            color_targets.astype(str).str.replace("%", "", regex=False)
        )
        self.assertEqual(
            loaded["y_train"].tolist(),
            color_targets.loc[loaded["train_ids"]].tolist(),
        )
        self.assertEqual(
            loaded["y_test"].tolist(),
            color_targets.loc[loaded["test_ids"]].tolist(),
        )
        self.assertGreater(loaded["saved_train_mismatches"], 0)
        self.assertGreater(loaded["saved_test_mismatches"], 0)

    def test_real_saved_model_integration_when_artifacts_and_data_are_available(self):
        project_root = Path(__file__).resolve().parents[2]
        artifact = project_root / "models" / "foodsure_multimodal_v1.joblib"
        metadata_path = project_root / "models" / "foodsure_multimodal_v1_metadata.json"
        raw_csv = (
            project_root.parent
            / "Multimodal Dataset for Turmeric Adulteration Detec"
            / "FTIR Spectroscopy"
            / "FTIR_Data.csv"
        )
        train_ids_path = project_root / "notebook" / "train_sample_ids.csv"
        if not all(path.is_file() for path in (artifact, metadata_path, raw_csv, train_ids_path)):
            self.skipTest("Saved model, metadata, split IDs, or raw FTIR data is unavailable.")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        train_ids = pd.read_csv(train_ids_path)["Sample_ID"].astype(str).str.strip()
        raw = pd.read_csv(raw_csv)
        raw["Sample ID"] = raw["Sample ID"].astype(str).str.strip()
        row = raw.set_index("Sample ID").loc[train_ids.iloc[0]]
        feature_names = metadata["feature_order"]["FTIR"]
        features = row[feature_names].apply(pd.to_numeric).to_frame().T
        result = run_pipeline(
            {"ftir_features": features},
            model_path=artifact,
            use_llm=False,
        )

        self.assertEqual(result["model_version"], metadata["model_version"])
        self.assertEqual(result["modalities_used"], metadata["modality_configuration"])
        self.assertEqual(result["model_metadata"]["feature_order"]["FTIR"], feature_names)
        json.dumps(result["report"], allow_nan=False)


if __name__ == "__main__":
    unittest.main()
