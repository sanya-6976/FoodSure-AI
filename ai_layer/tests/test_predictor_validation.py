"""Boundary checks against the saved predictor contract using real artifacts."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml_service.predictor import DEFAULT_MODEL_PATH, predict_sample


class _OverflowArray:
    def __array__(self, dtype=None, copy=None):
        raise OverflowError("forced array conversion overflow")


class _InvalidFloat(float):
    def __float__(self):
        raise ValueError("forced float conversion failure")


class TestSavedPredictorInputValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.model_path = cls.project_root / DEFAULT_MODEL_PATH.relative_to(
            cls.project_root
        )
        cls.metadata_path = cls.model_path.with_name(
            f"{cls.model_path.stem}_metadata.json"
        )
        if not cls.model_path.is_file() or not cls.metadata_path.is_file():
            raise unittest.SkipTest("Saved model artifact and metadata are required.")
        cls.metadata = json.loads(cls.metadata_path.read_text(encoding="utf-8"))
        cls.feature_names = cls.metadata["feature_order"]["FTIR"]
        cls.feature_count = len(cls.feature_names)

    def _copy_artifacts(self, directory: Path) -> tuple[Path, Path]:
        copied_model = directory / self.model_path.name
        copied_metadata = copied_model.with_name(
            f"{copied_model.stem}_metadata.json"
        )
        shutil.copy2(self.model_path, copied_model)
        shutil.copy2(self.metadata_path, copied_metadata)
        return copied_model, copied_metadata

    @staticmethod
    def _stubbed_bundle(
        classifier_result: object = None,
        regressor_result: object = None,
        scaler_feature_count: int = 2,
        classifier_classes: list[int] | None = None,
    ) -> dict[str, object]:
        class Scaler:
            n_features_in_ = scaler_feature_count

            @staticmethod
            def transform(features):
                return features.to_numpy()

        class Classifier:
            classes_ = np.array(classifier_classes or [0, 1])
            n_features_in_ = 2

            def predict(self, features):
                return [0] if classifier_result is None else classifier_result

        class Regressor:
            n_features_in_ = 2

            def predict(self, features):
                return [0.5] if regressor_result is None else regressor_result

        return {
            "model_version": "predictor-validation-test-v1",
            "modality_configuration": ["FTIR"],
            "feature_columns": {"FTIR": ["feature_1", "feature_2"]},
            "preprocessors": {
                "FTIR": {"scaler": Scaler(), "pca": None},
            },
            "classifier": Classifier(),
            "regressor": Regressor(),
            "class_labels": [0, 1],
        }

    def _predict_with_bundle(
        self,
        bundle: object,
        ftir_features: object | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "stubbed-model.joblib"
            model_path.touch()
            if metadata is not None:
                metadata_path = model_path.with_name(
                    f"{model_path.stem}_metadata.json"
                )
                metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            with patch("ml_service.predictor.joblib.load", return_value=bundle):
                return predict_sample(
                    ftir_features=np.zeros(2) if ftir_features is None else ftir_features,
                    model_path=model_path,
                )

    def _predict_with_stubbed_estimators(
        self,
        classifier_result: object,
        regressor_result: object,
    ) -> dict[str, object]:
        return self._predict_with_bundle(
            self._stubbed_bundle(classifier_result, regressor_result)
        )

    def test_wrong_feature_dimension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires .* features"):
            predict_sample(ftir_features=np.zeros(self.feature_count - 1))

    def test_missing_required_ftir_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing required model input.*FTIR"):
            predict_sample()

    def test_inputs_must_contain_exactly_one_sample(self):
        cases = (
            (
                "multiple dataframe rows",
                pd.DataFrame(
                    np.zeros((2, self.feature_count)),
                    columns=self.feature_names,
                ),
                "exactly one sample",
            ),
            (
                "three-dimensional array",
                np.zeros((1, 1, self.feature_count)),
                "one-dimensional vector or a single-row matrix",
            ),
        )
        for name, features, message in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, message):
                    predict_sample(ftir_features=features)

    def test_unsupported_and_ragged_inputs_are_rejected(self):
        cases = (
            ("unsupported object", object(), "must be a one-dimensional vector"),
            ("ragged sequence", [[0.0], [0.0, 1.0]], "rectangular numeric array"),
            (
                "array conversion overflow",
                [_OverflowArray(), 0],
                "rectangular numeric array",
            ),
        )
        for name, features, message in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, message):
                    predict_sample(ftir_features=features)

    def test_nan_and_infinite_features_are_rejected(self):
        for invalid in (np.nan, np.inf, -np.inf):
            with self.subTest(value=invalid):
                features = np.zeros(self.feature_count)
                features[0] = invalid
                with self.assertRaisesRegex(ValueError, "NaN or infinite"):
                    predict_sample(ftir_features=features)

    def test_oversized_integer_features_are_rejected_clearly(self):
        features = np.zeros(2, dtype=object)
        features[0] = 10**400

        with self.assertRaisesRegex(ValueError, "finite numeric values"):
            self._predict_with_bundle(self._stubbed_bundle(), ftir_features=features)

    def test_nonnumeric_features_are_rejected(self):
        features = np.zeros(self.feature_count, dtype=object)
        features[0] = "not numeric"
        with self.assertRaisesRegex(ValueError, "numeric values"):
            predict_sample(ftir_features=features)

    def test_numeric_text_features_are_not_coerced_to_measurements(self):
        cases = (
            ("string array", np.array(["1.25", "0"])),
            ("object array", np.array(["1.25", 0.0], dtype=object)),
        )
        for name, features in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, "numeric values"):
                    self._predict_with_bundle(
                        self._stubbed_bundle(),
                        ftir_features=features,
                    )

    def test_datetime_features_are_not_coerced_to_measurements(self):
        cases = (
            ("datetime array", np.array(["2026-10-19", "2026-10-20"], dtype="datetime64[D]")),
            ("timedelta array", np.array([1, 2], dtype="timedelta64[D]")),
            (
                "object datetime",
                np.array([np.datetime64("2026-10-19"), 0], dtype=object),
            ),
            ("object timedelta", np.array([np.timedelta64(1, "D"), 0], dtype=object)),
        )
        for name, features in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, "numeric values"):
                    self._predict_with_bundle(
                        self._stubbed_bundle(),
                        ftir_features=features,
                    )

    def test_complex_features_are_rejected_without_discarding_imaginary_parts(self):
        cases = (
            ("complex array", np.array([1 + 2j, 0])),
            ("object array", np.array([1 + 2j, 0], dtype=object)),
        )
        for name, features in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, "real numeric"):
                    self._predict_with_bundle(
                        self._stubbed_bundle(),
                        ftir_features=features,
                    )

    def test_boolean_features_are_rejected_instead_of_cast_to_zero_or_one(self):
        cases = (
            ("boolean array", np.array([True, False])),
            ("object array", np.array([True, 0.0], dtype=object)),
        )
        for name, features in cases:
            with self.subTest(input=name):
                with self.assertRaisesRegex(ValueError, "real numeric"):
                    self._predict_with_bundle(
                        self._stubbed_bundle(),
                        ftir_features=features,
                    )

    def test_masked_features_are_rejected_instead_of_using_hidden_values(self):
        features = np.ma.array([0.0, 0.75], mask=[False, True])
        with self.assertRaisesRegex(ValueError, "masked feature values"):
            self._predict_with_bundle(
                self._stubbed_bundle(),
                ftir_features=features,
            )

    def test_named_features_must_use_saved_order(self):
        cases = (
            ("reordered", list(reversed(self.feature_names))),
            ("missing", self.feature_names[:-1]),
            ("extra", [*self.feature_names, "unexpected_feature"]),
            (
                "duplicate",
                [*self.feature_names[:-1], self.feature_names[-2]],
            ),
        )
        for name, columns in cases:
            with self.subTest(columns=name):
                frame = pd.DataFrame(
                    np.zeros((1, len(columns))),
                    columns=columns,
                )
                with self.assertRaisesRegex(ValueError, "saved order exactly"):
                    predict_sample(ftir_features=frame)

    def test_valid_named_series_and_dataframe_match_positional_prediction(self):
        values = np.zeros(2)
        named_series = pd.Series(values, index=["feature_1", "feature_2"])
        unnamed_series = pd.Series(values)
        named_frame = pd.DataFrame([values], columns=["feature_1", "feature_2"])

        expected = self._predict_with_bundle(self._stubbed_bundle(), values)
        for name, features in (
            ("named series", named_series),
            ("unnamed positional series", unnamed_series),
            ("named dataframe", named_frame),
        ):
            with self.subTest(input=name):
                self.assertEqual(
                    self._predict_with_bundle(self._stubbed_bundle(), features),
                    expected,
                )

    def test_named_series_must_use_saved_order(self):
        series = pd.Series(
            np.zeros(self.feature_count),
            index=list(reversed(self.feature_names)),
        )
        with self.assertRaisesRegex(ValueError, "feature names must match"):
            predict_sample(ftir_features=series)

    def test_partially_named_series_is_rejected(self):
        series = pd.Series(
            np.zeros(2),
            index=["feature_1", 1],
        )
        with self.assertRaisesRegex(ValueError, "feature names must match"):
            self._predict_with_bundle(
                self._stubbed_bundle(),
                ftir_features=series,
            )

    def test_missing_model_artifact_has_clear_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.joblib"
            with self.assertRaisesRegex(FileNotFoundError, "not found"):
                predict_sample(ftir_features=np.zeros(self.feature_count), model_path=missing)

    def test_unstatable_model_artifact_has_clear_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "model.joblib"
            model_path.touch()
            with patch(
                "ml_service.predictor.Path.stat",
                side_effect=PermissionError("synthetic stat denial"),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not access FoodSure model artifact"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_model_path_resolution_failure_has_clear_failure(self):
        model_path = Path("C:/restricted/model.joblib")
        with patch(
            "ml_service.predictor.Path.resolve",
            side_effect=OSError("synthetic resolve denial"),
        ):
            with self.assertRaisesRegex(
                ValueError, "Could not resolve FoodSure model artifact path"
            ):
                predict_sample(
                    ftir_features=np.zeros(self.feature_count),
                    model_path=model_path,
                )

    def test_invalid_model_path_values_have_clear_failure(self):
        cases = (
            ("integer", 123),
            ("bytes", b"model.joblib"),
            ("unsupported object", object()),
            ("embedded null", "invalid\x00model.joblib"),
        )
        for name, model_path in cases:
            with self.subTest(path=name):
                with self.assertRaisesRegex(
                    ValueError, "Invalid FoodSure model artifact path"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_model_path_must_reference_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_directory = Path(tmp)
            with self.assertRaisesRegex(ValueError, "must be a file"):
                predict_sample(
                    ftir_features=np.zeros(self.feature_count),
                    model_path=model_directory,
                )

    def test_model_file_type_check_failure_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "model.joblib"
            model_path.touch()
            with patch(
                "ml_service.predictor.Path.is_file",
                side_effect=PermissionError("synthetic file-type denial"),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not inspect FoodSure model artifact"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_model_file_type_change_during_cached_load_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path, _ = self._copy_artifacts(Path(tmp))
            original_is_file = Path.is_file
            model_checks = 0

            def deny_cached_model_is_file(path):
                nonlocal model_checks
                if path.name == model_path.name:
                    model_checks += 1
                    if model_checks == 2:
                        raise PermissionError("synthetic cached model inspection denial")
                return original_is_file(path)

            with patch(
                "ml_service.predictor.Path.is_file",
                autospec=True,
                side_effect=deny_cached_model_is_file,
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not inspect FoodSure model artifact"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_metadata_sidecar_existence_check_failure_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "model.joblib"
            model_path.touch()
            metadata_path = model_path.with_name("model_metadata.json")
            original_exists = Path.exists

            def deny_metadata_exists(path):
                if path.name == metadata_path.name:
                    raise PermissionError("synthetic sidecar existence denial")
                return original_exists(path)

            with patch(
                "ml_service.predictor.Path.exists",
                autospec=True,
                side_effect=deny_metadata_exists,
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not inspect FoodSure model metadata sidecar"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_metadata_sidecar_file_type_check_failure_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / "model.joblib"
            model_path.touch()
            metadata_path = model_path.with_name("model_metadata.json")
            metadata_path.write_text("{}", encoding="utf-8")
            original_is_file = Path.is_file

            def deny_metadata_is_file(path):
                if path.name == metadata_path.name:
                    raise PermissionError("synthetic sidecar file-type denial")
                return original_is_file(path)

            with patch(
                "ml_service.predictor.Path.is_file",
                autospec=True,
                side_effect=deny_metadata_is_file,
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not inspect FoodSure model metadata sidecar"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_metadata_sidecar_change_during_cached_load_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path, metadata_path = self._copy_artifacts(Path(tmp))
            original_exists = Path.exists
            sidecar_checks = 0

            def deny_second_metadata_check(path):
                nonlocal sidecar_checks
                if path.name == metadata_path.name:
                    sidecar_checks += 1
                    if sidecar_checks == 2:
                        raise PermissionError("synthetic cached sidecar denial")
                return original_exists(path)

            with patch(
                "ml_service.predictor.Path.exists",
                autospec=True,
                side_effect=deny_second_metadata_check,
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not inspect FoodSure model metadata sidecar"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=model_path,
                    )

    def test_unreadable_model_artifact_has_clear_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            unreadable = Path(tmp) / "unreadable.joblib"
            unreadable.touch()
            with patch(
                "ml_service.predictor.joblib.load",
                side_effect=OSError("synthetic deserialization failure"),
            ):
                with self.assertRaisesRegex(ValueError, "Could not load FoodSure model"):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=unreadable,
                    )

    def test_artifact_fingerprint_read_failure_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied_model, _ = self._copy_artifacts(Path(tmp))
            with patch(
                "ml_service.predictor.Path.open",
                side_effect=PermissionError("synthetic read denial"),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Could not read artifact to validate"
                ):
                    predict_sample(
                        ftir_features=np.zeros(self.feature_count),
                        model_path=copied_model,
                    )

    def test_incompatible_sidecar_is_rejected_without_mutating_project_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            metadata["model_version"] = "incompatible-test-version"
            copied_metadata.write_text(json.dumps(metadata), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "does not match"):
                predict_sample(
                    ftir_features=np.zeros(self.feature_count),
                    model_path=copied_model,
                )

    def test_malformed_sidecar_is_rejected(self):
        deeply_nested_json = "[" * 10000 + "0" + "]" * 10000
        for case_name, sidecar_content, message in (
            ("invalid syntax", "{", "Could not read model metadata sidecar"),
            (
                "excessive nesting",
                deeply_nested_json,
                "Could not read model metadata sidecar",
            ),
            (
                "invalid UTF-8",
                b"\xff",
                "Could not read model metadata sidecar",
            ),
            ("non-object root", "[]", "must contain a JSON object"),
        ):
            with self.subTest(case=case_name):
                with tempfile.TemporaryDirectory() as tmp:
                    copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
                    if isinstance(sidecar_content, bytes):
                        copied_metadata.write_bytes(sidecar_content)
                    else:
                        copied_metadata.write_text(sidecar_content, encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, message):
                        predict_sample(
                            ftir_features=np.zeros(self.feature_count),
                            model_path=copied_model,
                        )

    def test_duplicate_sidecar_keys_are_rejected(self):
        bundle = self._stubbed_bundle()
        bundle["classifier"] = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 2,
                "predict": lambda self, features: [0],
            },
        )()
        bundle["regressor"] = type(
            "Ridge",
            (),
            {
                "n_features_in_": 2,
                "predict": lambda self, features: [0.5],
            },
        )()
        metadata = {
            "model_version": bundle["model_version"],
            "modality_configuration": bundle["modality_configuration"],
            "feature_order": bundle["feature_columns"],
            "class_labels_percentage": bundle["class_labels"],
            "classification_model": "Logistic Regression",
            "regression_model": "Ridge Regression",
            "pca_components_and_explained_variance": {
                "FTIR": {"components": None, "explained_variance": None}
            },
        }
        valid_sidecar = json.dumps(metadata)
        version_entry = f'"model_version": "{bundle["model_version"]}"'
        duplicate_sidecars = (
            (
                "top-level",
                valid_sidecar.replace(
                    version_entry,
                    f'"model_version": "conflicting-version", {version_entry}',
                    1,
                ),
                "duplicate key.*model_version",
            ),
            (
                "nested",
                valid_sidecar.replace(
                    '"components": null',
                    '"components": 1, "components": null',
                    1,
                ),
                "duplicate key.*components",
            ),
        )
        for name, sidecar_text, error in duplicate_sidecars:
            with self.subTest(duplicate_key=name):
                with tempfile.TemporaryDirectory() as tmp:
                    model_path = Path(tmp) / "stubbed-model.joblib"
                    model_path.touch()
                    model_path.with_name("stubbed-model_metadata.json").write_text(
                        sidecar_text, encoding="utf-8"
                    )
                    with patch("ml_service.predictor.joblib.load", return_value=bundle):
                        with self.assertRaisesRegex(ValueError, error):
                            predict_sample(
                                ftir_features=np.zeros(2),
                                model_path=model_path,
                            )

    def test_nonstandard_json_constants_are_rejected(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                with tempfile.TemporaryDirectory() as tmp:
                    copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
                    sidecar_text = copied_metadata.read_text(encoding="utf-8")
                    copied_metadata.write_text(
                        sidecar_text.replace(
                            "{", f'{{"extension": {constant},', 1
                        ),
                        encoding="utf-8",
                    )

                    with self.assertRaisesRegex(
                        ValueError,
                        f"Invalid model metadata sidecar.*{constant.lstrip('-')}",
                    ):
                        predict_sample(
                            ftir_features=np.zeros(self.feature_count),
                            model_path=copied_model,
                        )

    def test_metadata_sidecar_directory_has_clear_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
            copied_metadata.unlink()
            copied_metadata.mkdir()

            with self.assertRaisesRegex(ValueError, "metadata sidecar.*file"):
                predict_sample(
                    ftir_features=np.zeros(self.feature_count),
                    model_path=copied_model,
                )

    def test_sidecar_contract_fields_must_match_model_artifact(self):
        def change_version(metadata):
            metadata["model_version"] = "different-version"

        def change_modalities(metadata):
            metadata["modality_configuration"] = ["Color"]

        def change_feature_order(metadata):
            metadata["feature_order"]["FTIR"][0] = "unexpected_feature"

        def change_class_labels(metadata):
            metadata["class_labels_percentage"] = [0]

        def coerce_zero_class_label_to_boolean(metadata):
            labels = metadata["class_labels_percentage"]
            zero_index = labels.index(0)
            labels[zero_index] = False

        def change_classifier_name(metadata):
            metadata["classification_model"] = "Different Classifier"

        def blank_classifier_name(metadata):
            metadata["classification_model"] = " "

        def change_regressor_name(metadata):
            metadata["regression_model"] = "Different Regressor"

        def blank_regressor_name(metadata):
            metadata["regression_model"] = ""

        def omit_pca_details(metadata):
            metadata["pca_components_and_explained_variance"].pop("FTIR")

        def change_pca_component_count(metadata):
            details = metadata["pca_components_and_explained_variance"]["FTIR"]
            details["components"] += 1

        def set_boolean_pca_variance(metadata):
            metadata["pca_components_and_explained_variance"]["FTIR"][
                "explained_variance"
            ] = True

        def set_nonfinite_pca_variance(metadata):
            metadata["pca_components_and_explained_variance"]["FTIR"][
                "explained_variance"
            ] = float("nan")

        def set_oversized_pca_variance(metadata):
            metadata["pca_components_and_explained_variance"]["FTIR"][
                "explained_variance"
            ] = 10**400

        def change_pca_variance(metadata):
            details = metadata["pca_components_and_explained_variance"]["FTIR"]
            details["explained_variance"] -= 0.1

        cases = (
            ("model version", change_version, "model_version"),
            ("modality configuration", change_modalities, "modality_configuration"),
            ("feature order", change_feature_order, "feature_order"),
            ("class labels", change_class_labels, "class_labels_percentage"),
            (
                "boolean class label",
                coerce_zero_class_label_to_boolean,
                "class_labels_percentage",
            ),
            ("classifier name", change_classifier_name, "classification_model"),
            ("blank classifier name", blank_classifier_name, "non-empty string"),
            ("regressor name", change_regressor_name, "regression_model"),
            ("blank regressor name", blank_regressor_name, "non-empty string"),
            ("missing PCA details", omit_pca_details, "no PCA details"),
            (
                "inconsistent PCA details",
                change_pca_component_count,
                "do not match the saved estimator",
            ),
            (
                "boolean PCA variance",
                set_boolean_pca_variance,
                "do not match the saved estimator",
            ),
            (
                "non-finite PCA variance",
                set_nonfinite_pca_variance,
                "Invalid model metadata sidecar",
            ),
            (
                "oversized PCA variance",
                set_oversized_pca_variance,
                "do not match the saved estimator",
            ),
            (
                "inconsistent PCA variance",
                change_pca_variance,
                "do not match the saved estimator",
            ),
        )
        for name, change_metadata, message in cases:
            with self.subTest(sidecar_field=name):
                with tempfile.TemporaryDirectory() as tmp:
                    copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
                    metadata = json.loads(copied_metadata.read_text(encoding="utf-8"))
                    change_metadata(metadata)
                    copied_metadata.write_text(
                        json.dumps(metadata),
                        encoding="utf-8",
                    )

                    with self.assertRaisesRegex(ValueError, message):
                        predict_sample(
                            ftir_features=np.zeros(self.feature_count),
                            model_path=copied_model,
                        )

    def test_array_class_labels_match_json_sidecar(self):
        bundle = self._stubbed_bundle(classifier_classes=[0, 1])
        bundle["class_labels"] = np.array([0, 1])
        bundle["classifier"] = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 2,
                "predict": lambda self, features: [0],
            },
        )()
        bundle["regressor"] = type(
            "Ridge",
            (),
            {
                "n_features_in_": 2,
                "predict": lambda self, features: [0.5],
            },
        )()
        metadata = {
            "model_version": bundle["model_version"],
            "modality_configuration": bundle["modality_configuration"],
            "feature_order": bundle["feature_columns"],
            "class_labels_percentage": [0, 1],
            "classification_model": "Logistic Regression",
            "regression_model": "Ridge Regression",
            "pca_components_and_explained_variance": {
                "FTIR": {"components": None, "explained_variance": None}
            },
        }

        prediction = self._predict_with_bundle(bundle, metadata=metadata)
        self.assertEqual(prediction["predicted_class"], "0%")

    def test_invalid_classifier_predictions_are_rejected(self):
        cases = (
            ("empty", [], "exactly one class"),
            ("multiple", [0, 1], "exactly one class"),
            ("ragged", [[0], [0, 1]], "exactly one class"),
            (
                "masked",
                np.ma.array([0], mask=[True]),
                "must not return a masked class prediction",
            ),
            ("nonnumeric", ["0"], "non-numeric class label"),
            ("boolean", [True], "non-numeric class label"),
            ("unsupported", [4], "unsupported class label"),
            ("oversized integer", [10**400], "unsupported class label"),
            ("nonfinite", [np.nan], "unsupported class label"),
            ("array conversion overflow", _OverflowArray(), "exactly one class"),
            (
                "invalid float conversion",
                np.array([_InvalidFloat(0)], dtype=object),
                "unsupported class label",
            ),
        )
        for name, prediction, message in cases:
            with self.subTest(prediction=name):
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_stubbed_estimators(prediction, [0.5])

    def test_invalid_regression_predictions_are_rejected(self):
        cases = (
            ("empty", [], "exactly one estimate"),
            ("multiple", [0.5, 1.5], "exactly one estimate"),
            ("ragged", [[0.5], [0.5, 1.0]], "exactly one estimate"),
            (
                "masked",
                np.ma.array([0.5], mask=[True]),
                "must not return a masked regression estimate",
            ),
            ("boolean", [True], "non-numeric estimate"),
            ("numeric string", ["0.5"], "non-numeric estimate"),
            ("complex", [0.5 + 1j], "non-numeric estimate"),
            ("oversized integer", [10**400], "non-finite estimate"),
            ("infinite", [np.inf], "non-finite estimate"),
            ("nan", [np.nan], "non-finite estimate"),
            ("array conversion overflow", _OverflowArray(), "exactly one estimate"),
            (
                "invalid float conversion",
                np.array([_InvalidFloat(0.5)], dtype=object),
                "non-finite estimate",
            ),
        )
        for name, prediction, message in cases:
            with self.subTest(prediction=name):
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_stubbed_estimators([0], prediction)

    def test_invalid_preprocessor_outputs_are_rejected(self):
        cases = (
            ("wrong shape", np.zeros((1, 1)), "transformed feature shape"),
            ("non-finite", np.array([[0.0, np.nan]]), "non-finite transformed"),
            ("complex", np.array([[0.0, 1.0 + 2j]]), "non-numeric transformed"),
            ("boolean", np.array([[True, False]]), "non-numeric transformed"),
            (
                "numeric text",
                np.array([["1.25", "0"]]),
                "non-numeric transformed",
            ),
            (
                "datetime",
                np.array([["2026-10-19", "2026-10-20"]], dtype="datetime64[D]"),
                "non-numeric transformed",
            ),
            (
                "ragged",
                [[0.0], [0.0, 1.0]],
                "must return a rectangular transformed feature array",
            ),
            (
                "masked",
                np.ma.array([[0.0, 0.75]], mask=[[False, True]]),
                "masked transformed feature values",
            ),
            (
                "array conversion overflow",
                _OverflowArray(),
                "must return a rectangular transformed feature array",
            ),
            (
                "oversized integer",
                np.array([[10**400, 0]], dtype=object),
                "non-finite transformed features",
            ),
        )
        for name, transformed, message in cases:
            with self.subTest(output=name):
                bundle = self._stubbed_bundle()
                bundle["preprocessors"]["FTIR"]["scaler"].transform = (
                    lambda _features, result=transformed: result
                )
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_bundle(bundle)

    def test_invalid_pca_outputs_are_rejected(self):
        class Pca:
            n_features_in_ = 2
            n_components_ = 1
            explained_variance_ratio_ = np.array([0.9])

            def __init__(self, output):
                self.output = output

            def transform(self, _features):
                return self.output

        cases = (
            ("wrong shape", np.zeros((1, 2)), "transformed feature shape"),
            ("non-finite", np.array([[np.inf]]), "non-finite transformed"),
            ("complex", np.array([[1.0 + 1j]]), "non-numeric transformed"),
            (
                "array conversion overflow",
                _OverflowArray(),
                "must return a rectangular transformed feature array",
            ),
        )
        for name, output, message in cases:
            with self.subTest(output=name):
                bundle = self._stubbed_bundle()
                bundle["preprocessors"]["FTIR"]["pca"] = Pca(output)
                bundle["classifier"].n_features_in_ = 1
                bundle["regressor"].n_features_in_ = 1
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_bundle(bundle)

    def test_invalid_model_class_labels_are_rejected(self):
        cases = (
            ("missing labels", None, "non-empty sequence"),
            ("empty labels", [], "non-empty sequence"),
            ("boolean label", [False, 1], "numeric labels"),
            ("nonnumeric label", [0, "1"], "numeric labels"),
            ("non-finite label", [0, np.inf], "finite labels"),
            ("integer outside float range", [0, 10**10000], "finite labels"),
            ("invalid float conversion", [_InvalidFloat(0)], "finite labels"),
            ("duplicate labels", [0, 0], "duplicate labels"),
        )
        for name, labels, message in cases:
            with self.subTest(labels=name):
                bundle = self._stubbed_bundle()
                bundle["class_labels"] = labels
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_bundle(bundle)

    def test_malformed_model_bundles_are_rejected(self):
        class Pca:
            n_features_in_ = 2
            n_components_ = 1

            @staticmethod
            def transform(features):
                return features[:, :1]

        def set_array_pca_input_count(bundle):
            bundle["preprocessors"]["FTIR"]["pca"] = type(
                "InvalidPca",
                (),
                {
                    "n_features_in_": np.array([2]),
                    "n_components_": 1,
                    "transform": lambda self, features: features[:, :1],
                },
            )()
            bundle["classifier"].n_features_in_ = 1
            bundle["regressor"].n_features_in_ = 1

        def set_pca_components_above_input_dimension(bundle):
            bundle["preprocessors"]["FTIR"]["pca"] = type(
                "InvalidPca",
                (),
                {
                    "n_features_in_": 2,
                    "n_components_": 3,
                    "transform": lambda self, features: np.repeat(
                        features[:, :1], 3, axis=1
                    ),
                },
            )()
            bundle["classifier"].n_features_in_ = 3
            bundle["regressor"].n_features_in_ = 3

        cases = (
            (
                "blank model version",
                lambda bundle: bundle.update(model_version=" "),
                "model_version.*non-empty string",
            ),
            (
                "non-list modality configuration",
                lambda bundle: bundle.update(modality_configuration="FTIR"),
                "unique supported modalities",
            ),
            (
                "empty modality configuration",
                lambda bundle: bundle.update(modality_configuration=[]),
                "unique supported modalities",
            ),
            (
                "missing required field",
                lambda bundle: bundle.pop("classifier"),
                "missing required fields",
            ),
            (
                "non-dictionary feature columns",
                lambda bundle: bundle.update(feature_columns=[]),
                "feature_columns and preprocessors must be dictionaries",
            ),
            (
                "non-dictionary preprocessors",
                lambda bundle: bundle.update(preprocessors=[]),
                "feature_columns and preprocessors must be dictionaries",
            ),
            (
                "unsupported modality",
                lambda bundle: bundle.update(modality_configuration=["Unknown"]),
                "unique supported modalities",
            ),
            (
                "duplicate modality",
                lambda bundle: bundle.update(modality_configuration=["FTIR", "FTIR"]),
                "unique supported modalities",
            ),
            (
                "duplicate feature columns",
                lambda bundle: bundle["feature_columns"].update(
                    FTIR=["feature_1", "feature_1"]
                ),
                "invalid or duplicate feature columns",
            ),
            (
                "missing modality preprocessor",
                lambda bundle: bundle["preprocessors"].clear(),
                "no preprocessing bundle for FTIR",
            ),
            (
                "non-dictionary modality preprocessor",
                lambda bundle: bundle["preprocessors"].update(FTIR=None),
                "no preprocessing bundle for FTIR",
            ),
            (
                "scaler missing transform",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                scaler=type("ScalerWithoutTransform", (), {"n_features_in_": 2})()
                ),
                "scaler for FTIR has no transform",
            ),
            (
                "unreadable scaler transform",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    scaler=type(
                        "ScalerWithUnreadableTransform",
                        (),
                        {
                            "n_features_in_": 2,
                            "transform": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable scaler transform")
                                )
                            ),
                        },
                    )()
                ),
                "Could not inspect scaler transform for FTIR",
            ),
            (
                "scaler dimension mismatch",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    scaler=type(
                        "InvalidScaler",
                        (),
                        {
                            "n_features_in_": 3,
                            "transform": lambda self, features: features,
                        },
                    )()
                ),
                "scaler feature count",
            ),
            (
                "array scaler feature count",
                lambda bundle: setattr(
                    bundle["preprocessors"]["FTIR"]["scaler"],
                    "n_features_in_",
                    np.array([2]),
                ),
                "scaler feature count",
            ),
            (
                "unreadable scaler feature count",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    scaler=type(
                        "ScalerWithUnreadableFeatureCount",
                        (),
                        {
                            "n_features_in_": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable scaler metadata")
                                )
                            ),
                            "transform": lambda self, features: features,
                        },
                    )()
                ),
                "Could not read scaler feature count for FTIR",
            ),
            (
                "unreadable classifier class labels",
                lambda bundle: bundle.update(
                    classifier=type(
                        "ClassifierWithUnreadableClasses",
                        (),
                        {
                            "classes_": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable classifier metadata")
                                )
                            ),
                            "n_features_in_": 2,
                            "predict": lambda self, features: [0],
                        },
                    )()
                ),
                "Could not read classifier class labels",
            ),
            (
                "invalid classifier class metadata access",
                lambda bundle: bundle.update(
                    classifier=type(
                        "ClassifierWithInvalidClasses",
                        (),
                        {
                            "classes_": property(
                                lambda self: (_ for _ in ()).throw(
                                    TypeError("invalid classifier metadata")
                                )
                            ),
                            "n_features_in_": 2,
                            "predict": lambda self, features: [0],
                        },
                    )()
                ),
                "Could not read classifier class labels",
            ),
            (
                "unreadable classifier predict method",
                lambda bundle: bundle.update(
                    classifier=type(
                        "ClassifierWithUnreadablePredict",
                        (),
                        {
                            "classes_": np.array([0, 1]),
                            "n_features_in_": 2,
                            "predict": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable classifier method")
                                )
                            ),
                        },
                    )()
                ),
                "Could not inspect classifier predict method",
            ),
            (
                "unreadable regressor predict method",
                lambda bundle: bundle.update(
                    regressor=type(
                        "RegressorWithUnreadablePredict",
                        (),
                        {
                            "n_features_in_": 2,
                            "predict": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable regressor method")
                                )
                            ),
                        },
                    )()
                ),
                "Could not inspect regressor predict method",
            ),
            (
                "unreadable regressor input dimension",
                lambda bundle: bundle.update(
                    regressor=type(
                        "RegressorWithUnreadableFeatureCount",
                        (),
                        {
                            "n_features_in_": property(
                                lambda self: (_ for _ in ()).throw(
                                    RuntimeError("unreadable regressor metadata")
                                )
                            ),
                            "predict": lambda self, features: [0.5],
                        },
                    )()
                ),
                "Could not read regressor input dimension",
            ),
            (
                "PCA missing transform",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    pca=type("InvalidPca", (), {"n_features_in_": 2, "n_components_": 1})()
                ),
                "PCA for FTIR has no transform",
            ),
            (
                "unreadable PCA transform",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    pca=type(
                        "PcaWithUnreadableTransform",
                        (),
                        {
                            "n_features_in_": 2,
                            "n_components_": 1,
                            "transform": property(
                                lambda self: (_ for _ in ()).throw(
                                    TypeError("unreadable PCA transform")
                                )
                            ),
                        },
                    )()
                ),
                "Could not inspect PCA transform for FTIR",
            ),
            (
                "PCA input dimension mismatch",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    pca=type(
                        "InvalidPca",
                        (),
                        {
                            "n_features_in_": 3,
                            "n_components_": 1,
                            "transform": lambda self, features: features[:, :1],
                        },
                    )()
                ),
                "PCA input feature count",
            ),
            (
                "array PCA input feature count",
                set_array_pca_input_count,
                "PCA input feature count",
            ),
            (
                "PCA components exceed input dimension",
                set_pca_components_above_input_dimension,
                "PCA component count.*input feature count",
            ),
            (
                "PCA invalid component count",
                lambda bundle: bundle["preprocessors"]["FTIR"].update(
                    pca=type(
                        "InvalidPca",
                        (),
                        {
                            "n_features_in_": 2,
                            "n_components_": 0,
                            "transform": lambda self, features: features[:, :1],
                        },
                    )()
                ),
                "PCA for FTIR has invalid components",
            ),
            (
                "estimator input dimension mismatch",
                lambda bundle: setattr(bundle["classifier"], "n_features_in_", 3),
                "classifier input dimension",
            ),
            (
                "array estimator input dimension",
                lambda bundle: setattr(
                    bundle["classifier"], "n_features_in_", np.array([2])
                ),
                "classifier input dimension",
            ),
            (
                "regressor input dimension mismatch",
                lambda bundle: setattr(bundle["regressor"], "n_features_in_", 3),
                "regressor input dimension",
            ),
            (
                "classifier missing predict",
                lambda bundle: bundle.update(
                    classifier=type(
                        "ClassifierWithoutPredict",
                        (),
                        {"classes_": np.array([0, 1]), "n_features_in_": 2},
                    )()
                ),
                "classifier must provide predict",
            ),
            (
                "regressor missing predict",
                lambda bundle: bundle.update(
                    regressor=type("RegressorWithoutPredict", (), {})()
                ),
                "regressor must provide predict",
            ),
            (
                "classifier class mismatch",
                lambda bundle: setattr(
                    bundle["classifier"],
                    "classes_",
                    np.array([0, 2]),
                ),
                "class_labels do not match",
            ),
        )
        for name, corrupt, message in cases:
            with self.subTest(bundle_error=name):
                bundle = self._stubbed_bundle()
                corrupt(bundle)
                with self.assertRaisesRegex(ValueError, message):
                    self._predict_with_bundle(bundle)

        with self.assertRaisesRegex(ValueError, "must contain a dictionary"):
            self._predict_with_bundle(None)

        bundle = self._stubbed_bundle()
        bundle["preprocessors"]["FTIR"]["pca"] = Pca()
        bundle["classifier"] = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 1,
                "predict": lambda self, features: [0],
            },
        )()
        bundle["regressor"] = type(
            "Ridge",
            (),
            {
                "n_features_in_": 1,
                "predict": lambda self, features: [0.5],
            },
        )()
        prediction = self._predict_with_bundle(bundle)
        self.assertEqual(prediction["predicted_class"], "0%")
        self.assertEqual(prediction["predicted_percentage"], 0.5)
        self.assertEqual(prediction["modality_configuration"], ["FTIR"])
        self.assertIsNone(prediction["probabilities"])
        self.assertIn("not calibrated", prediction["probability_note"])

    def test_zero_dimensional_class_labels_are_rejected_clearly(self):
        bundle = self._stubbed_bundle()
        bundle["class_labels"] = np.array(0)

        with self.assertRaisesRegex(
            ValueError, "class_labels.*non-empty sequence"
        ):
            self._predict_with_bundle(bundle)

    def test_boolean_pca_component_count_is_rejected(self):
        bundle = self._stubbed_bundle()

        class Pca:
            n_features_in_ = 2
            n_components_ = 1
            explained_variance_ratio_ = np.array([0.9])

            @staticmethod
            def transform(features):
                return features[:, :1]

        classifier = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 1,
                "predict": lambda self, features: [0],
            },
        )()
        regressor = type(
            "Ridge",
            (),
            {
                "n_features_in_": 1,
                "predict": lambda self, features: [0.5],
            },
        )()
        bundle["preprocessors"]["FTIR"]["pca"] = Pca()
        bundle["classifier"] = classifier
        bundle["regressor"] = regressor
        metadata = {
            "model_version": bundle["model_version"],
            "modality_configuration": bundle["modality_configuration"],
            "feature_order": bundle["feature_columns"],
            "class_labels_percentage": bundle["class_labels"],
            "classification_model": "Logistic Regression",
            "regression_model": "Ridge Regression",
            "pca_components_and_explained_variance": {
                "FTIR": {
                    "components": True,
                    "explained_variance": 0.9,
                }
            },
        }

        with self.assertRaisesRegex(ValueError, "PCA details for FTIR"):
            self._predict_with_bundle(bundle, metadata=metadata)

    def test_boolean_pca_estimator_component_count_is_rejected(self):
        bundle = self._stubbed_bundle()

        class Pca:
            n_features_in_ = 2
            n_components_ = True

            @staticmethod
            def transform(features):
                return features[:, :1]

        bundle["preprocessors"]["FTIR"]["pca"] = Pca()
        bundle["classifier"].n_features_in_ = 1
        bundle["regressor"].n_features_in_ = 1

        with self.assertRaisesRegex(ValueError, "invalid components"):
            self._predict_with_bundle(bundle)

    def test_missing_pca_variance_metadata_is_rejected_clearly(self):
        bundle = self._stubbed_bundle()

        class Pca:
            n_features_in_ = 2
            n_components_ = 1

            @staticmethod
            def transform(features):
                return features[:, :1]

        bundle["preprocessors"]["FTIR"]["pca"] = Pca()
        bundle["classifier"] = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 1,
                "predict": lambda self, features: [0],
            },
        )()
        bundle["regressor"] = type(
            "Ridge",
            (),
            {
                "n_features_in_": 1,
                "predict": lambda self, features: [0.5],
            },
        )()
        metadata = {
            "model_version": bundle["model_version"],
            "modality_configuration": bundle["modality_configuration"],
            "feature_order": bundle["feature_columns"],
            "class_labels_percentage": bundle["class_labels"],
            "classification_model": "Logistic Regression",
            "regression_model": "Ridge Regression",
            "pca_components_and_explained_variance": {
                "FTIR": {"components": 1, "explained_variance": 0.9}
            },
        }

        with self.assertRaisesRegex(
            ValueError, "PCA.*explained variance ratio"
        ):
            self._predict_with_bundle(bundle, metadata=metadata)

    def test_pca_variance_array_conversion_overflow_is_rejected(self):
        bundle = self._stubbed_bundle()

        class Pca:
            n_features_in_ = 2
            n_components_ = 1
            explained_variance_ratio_ = _OverflowArray()

            @staticmethod
            def transform(features):
                return features[:, :1]

        bundle["preprocessors"]["FTIR"]["pca"] = Pca()
        bundle["classifier"] = type(
            "LogisticRegression",
            (),
            {
                "classes_": np.array([0, 1]),
                "n_features_in_": 1,
                "predict": lambda self, features: [0],
            },
        )()
        bundle["regressor"] = type(
            "Ridge",
            (),
            {
                "n_features_in_": 1,
                "predict": lambda self, features: [0.5],
            },
        )()
        metadata = {
            "model_version": bundle["model_version"],
            "modality_configuration": bundle["modality_configuration"],
            "feature_order": bundle["feature_columns"],
            "class_labels_percentage": bundle["class_labels"],
            "classification_model": "Logistic Regression",
            "regression_model": "Ridge Regression",
            "pca_components_and_explained_variance": {
                "FTIR": {"components": 1, "explained_variance": 0.9}
            },
        }

        with self.assertRaisesRegex(
            ValueError, "PCA explained variance ratio for FTIR is invalid"
        ):
            self._predict_with_bundle(bundle, metadata=metadata)

    def test_invalid_pca_variance_ratio_is_rejected(self):
        for ratio in (False, True, -0.1, 0, 1.1, 10**400):
            with self.subTest(ratio=ratio):
                bundle = self._stubbed_bundle()

                class Pca:
                    n_features_in_ = 2
                    n_components_ = 1
                    explained_variance_ratio_ = np.array([ratio])

                    @staticmethod
                    def transform(features):
                        return features[:, :1]

                bundle["preprocessors"]["FTIR"]["pca"] = Pca()
                bundle["classifier"] = type(
                    "LogisticRegression",
                    (),
                    {
                        "classes_": np.array([0, 1]),
                        "n_features_in_": 1,
                        "predict": lambda self, features: [0],
                    },
                )()
                bundle["regressor"] = type(
                    "Ridge",
                    (),
                    {
                        "n_features_in_": 1,
                        "predict": lambda self, features: [0.5],
                    },
                )()
                metadata = {
                    "model_version": bundle["model_version"],
                    "modality_configuration": bundle["modality_configuration"],
                    "feature_order": bundle["feature_columns"],
                    "class_labels_percentage": bundle["class_labels"],
                    "classification_model": "Logistic Regression",
                    "regression_model": "Ridge Regression",
                    "pca_components_and_explained_variance": {
                        "FTIR": {
                            "components": 1,
                            "explained_variance": ratio,
                        }
                    },
                }

                with self.assertRaisesRegex(
                    ValueError, "PCA.*explained variance ratio"
                ):
                    self._predict_with_bundle(bundle, metadata=metadata)

    def test_changed_sidecar_invalidates_cached_artifact_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
            sample = np.zeros(self.feature_count)
            predict_sample(ftir_features=sample, model_path=copied_model)

            metadata = json.loads(copied_metadata.read_text(encoding="utf-8"))
            original_version = metadata["model_version"]
            changed_version = (
                ("X" if original_version[0] != "X" else "Y")
                + original_version[1:]
            )
            original_text = copied_metadata.read_bytes()
            original_field = f'"model_version": "{original_version}"'.encode()
            changed_field = f'"model_version": "{changed_version}"'.encode()
            self.assertEqual(original_text.count(original_field), 1)
            original_stat = copied_metadata.stat()
            copied_metadata.write_bytes(original_text.replace(original_field, changed_field))
            rewritten_stat = copied_metadata.stat()
            self.assertEqual(rewritten_stat.st_size, original_stat.st_size)

            os.utime(
                copied_metadata,
                ns=(
                    rewritten_stat.st_atime_ns,
                    original_stat.st_mtime_ns + 2_000_000_000,
                ),
            )
            self.assertNotEqual(
                copied_metadata.stat().st_mtime_ns,
                original_stat.st_mtime_ns,
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                predict_sample(ftir_features=sample, model_path=copied_model)

    def test_same_size_sidecar_change_with_restored_mtime_is_revalidated(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied_model, copied_metadata = self._copy_artifacts(Path(tmp))
            sample = np.zeros(self.feature_count)
            predict_sample(ftir_features=sample, model_path=copied_model)

            original_text = copied_metadata.read_bytes()
            original_metadata = json.loads(original_text)
            original_version = original_metadata["model_version"]
            changed_version = (
                ("X" if original_version[0] != "X" else "Y")
                + original_version[1:]
            )
            original_field = f'"model_version": "{original_version}"'.encode()
            changed_field = f'"model_version": "{changed_version}"'.encode()
            self.assertEqual(original_text.count(original_field), 1)
            original_stat = copied_metadata.stat()
            copied_metadata.write_bytes(
                original_text.replace(original_field, changed_field)
            )
            self.assertEqual(copied_metadata.stat().st_size, original_stat.st_size)
            os.utime(
                copied_metadata,
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
            self.assertEqual(
                copied_metadata.stat().st_mtime_ns,
                original_stat.st_mtime_ns,
            )

            with self.assertRaisesRegex(ValueError, "does not match"):
                predict_sample(ftir_features=sample, model_path=copied_model)


if __name__ == "__main__":
    unittest.main()
