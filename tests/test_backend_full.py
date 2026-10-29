"""Unit and integration test suite for FoodSure AI authentication, service, and history."""

import os
import unittest
from pathlib import Path
import pandas as pd

from backend.auth import (
    authenticate_user,
    init_auth_db,
    register_user,
    validate_email,
    validate_password,
)
from backend.history import (
    clear_user_history,
    delete_analysis,
    get_analysis_by_id,
    get_user_history,
    init_history_db,
    save_analysis,
)
from backend.service import (
    export_report_markdown,
    generate_followup_answer,
    get_dataset_sample_ids,
    get_metadata,
    get_spectrum_data,
    load_dataset_sample,
    load_resources,
    run_sample_analysis,
    validate_uploaded_ftir_csv,
)


class TestFoodSureAuthentication(unittest.TestCase):
    def setUp(self):
        init_auth_db()

    def test_password_validation(self):
        # Too short
        ok, msg = validate_password("Short1!")
        self.assertFalse(ok)
        self.assertIn("at least 8", msg)

        # No uppercase
        ok, msg = validate_password("lowercase123!")
        self.assertFalse(ok)
        self.assertIn("uppercase", msg)

        # No digit
        ok, msg = validate_password("NoDigitsHere!")
        self.assertFalse(ok)
        self.assertIn("number", msg)

        # Valid password
        ok, msg = validate_password("ValidPassword2026!")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_email_validation(self):
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("researcher.name@institute.ac.in"))
        self.assertFalse(validate_email("notanemail"))
        self.assertFalse(validate_email("user@"))
        self.assertFalse(validate_email("@domain.com"))

    def test_demo_user_seeded_and_authenticates(self):
        ok, msg, user = authenticate_user("researcher@foodsure.ai", "FoodSure2026!")
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "researcher@foodsure.ai")

    def test_registration_and_duplicate_prevention(self):
        import uuid
        test_email = f"scientist_{uuid.uuid4().hex[:8]}@test.com"
        ok, msg, user = register_user(test_email, "SecurePassword999!", "Dr. Unique")
        self.assertTrue(ok, msg)
        self.assertIsNotNone(user)

        # Duplicate registration must fail
        ok2, msg2, user2 = register_user(test_email, "SecurePassword999!", "Dr. Unique")
        self.assertFalse(ok2)
        self.assertIn("already exists", msg2)

    def test_invalid_login_rejected(self):
        ok, msg, user = authenticate_user("researcher@foodsure.ai", "WrongPassword!")
        self.assertFalse(ok)
        self.assertIn("Invalid", msg)
        self.assertIsNone(user)


class TestFoodSureHistory(unittest.TestCase):
    def setUp(self):
        init_history_db()
        self.user_a = "user_a_123"
        self.user_b = "user_b_456"

    def test_user_history_isolation(self):
        clear_user_history(self.user_a)
        clear_user_history(self.user_b)

        # Save for user A
        aid_a = save_analysis(
            user_id=self.user_a,
            sample_id="T0S01",
            input_source="Dataset",
            modality="FTIR",
            predicted_class="0%",
            predicted_percentage=0.0,
            actual_level=0.0,
            status="PURE TURMERIC",
            confidence_note="Note",
            analysis_mode="deterministic_fallback",
            summary="User A summary",
            full_report={"sample": "T0S01"},
        )

        # Save for user B
        aid_b = save_analysis(
            user_id=self.user_b,
            sample_id="T3S05",
            input_source="Dataset",
            modality="FTIR",
            predicted_class="3%",
            predicted_percentage=3.1,
            actual_level=3.0,
            status="ADULTERATED",
            confidence_note="Note",
            analysis_mode="gemini_ai",
            summary="User B summary",
            full_report={"sample": "T3S05"},
        )

        hist_a = get_user_history(self.user_a)
        hist_b = get_user_history(self.user_b)

        self.assertEqual(len(hist_a), 1)
        self.assertEqual(hist_a[0]["sample_id"], "T0S01")
        self.assertEqual(len(hist_b), 1)
        self.assertEqual(hist_b[0]["sample_id"], "T3S05")

        # User A cannot retrieve User B's record
        rec_b_from_a = get_analysis_by_id(aid_b, self.user_a)
        self.assertIsNone(rec_b_from_a)

        # User B can retrieve their own record
        rec_b = get_analysis_by_id(aid_b, self.user_b)
        self.assertIsNotNone(rec_b)
        self.assertEqual(rec_b["predicted_class"], "3%")


class TestFoodSureService(unittest.TestCase):
    def test_load_resources(self):
        res = load_resources()
        self.assertTrue(res["model_available"])
        self.assertTrue(res["metadata_available"])
        self.assertEqual(res["feature_count"], 2522)
        self.assertEqual(len(res["classes"]), 7)

    def test_dataset_sample_loading(self):
        sample_ids = get_dataset_sample_ids()
        self.assertGreater(len(sample_ids), 0)
        self.assertIn("T0S01", sample_ids)

        features, actual, meta = load_dataset_sample("T0S01")
        self.assertEqual(features.shape, (1, 2522))
        self.assertEqual(actual, 0.0)

        spectrum = get_spectrum_data(features)
        self.assertEqual(len(spectrum["wavenumbers"]), 2522)
        self.assertEqual(len(spectrum["absorbance"]), 2522)

    def test_end_to_end_analysis_execution(self):
        features, actual, meta = load_dataset_sample("T0S01")
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Test Suite",
            user_id="test_runner",
            use_gemini=False,  # deterministic in unit test
            sample_meta=meta,
        )
        self.assertEqual(result.sample_id, "T0S01")
        self.assertEqual(result.prediction.predicted_class, "0%")
        self.assertTrue(result.prediction.is_pure)
        self.assertEqual(result.prediction.status_label, "PURE TURMERIC")
        self.assertEqual(result.analysis_mode, "deterministic_fallback")

        # New: 8-section structured explanation must be present
        se = result.structured_explanation
        self.assertIsInstance(se, dict)
        for field in (
            "executive_summary",
            "result_interpretation",
            "evidence_and_reasoning",
            "scientific_explanation",
            "confidence_and_uncertainty",
            "practical_implications",
            "recommended_next_steps",
            "limitations",
        ):
            self.assertIn(field, se, f"Missing structured_explanation field: {field}")
        self.assertIsInstance(se["evidence_and_reasoning"], list)
        self.assertGreater(len(se["evidence_and_reasoning"]), 0)
        self.assertIsInstance(se["recommended_next_steps"], list)
        self.assertIsInstance(se["limitations"], list)
        self.assertEqual(result.explanation_depth, "detailed")

        # Markdown export includes new section headers
        md = export_report_markdown(result)
        self.assertIn("FoodSure AI", md)
        self.assertIn("PURE TURMERIC", md)
        self.assertIn("Executive Summary", md)
        self.assertIn("Evidence & Reasoning", md)

    def test_structured_explanation_adulterated_sample(self):
        """Test 8-section explanation for an adulterated sample."""
        features, actual, meta = load_dataset_sample("T3S05")
        result = run_sample_analysis(
            features=features,
            sample_id="T3S05",
            actual_level=actual,
            source_label="Test Suite",
            user_id="test_runner",
            use_gemini=False,
            sample_meta=meta,
        )
        se = result.structured_explanation
        # Executive summary must mention the prediction
        self.assertIn(result.prediction.predicted_class, se["executive_summary"])
        # Practical implications must be present
        self.assertTrue(se["practical_implications"].strip())

    def test_explanation_depth_quick(self):
        """depth='quick' accepted and stored."""
        features, actual, meta = load_dataset_sample("T0S01")
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Test Suite",
            user_id="test_runner",
            use_gemini=False,
            depth="quick",
            sample_meta=meta,
        )
        self.assertEqual(result.explanation_depth, "quick")
        self.assertIn("executive_summary", result.structured_explanation)

    def test_followup_answer_deterministic(self):
        """generate_followup_answer returns a non-empty string without LLM."""
        features, actual, meta = load_dataset_sample("T0S01")
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Test Suite",
            user_id="test_runner",
            use_gemini=False,
            sample_meta=meta,
        )
        answer = generate_followup_answer(
            "What does this result mean?",
            result,
            use_gemini=False,
        )
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 20)

    def test_followup_empty_question_handled(self):
        """Empty question returns a helpful message instead of crashing."""
        features, actual, meta = load_dataset_sample("T0S01")
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Test Suite",
            user_id="test_runner",
            use_gemini=False,
            sample_meta=meta,
        )
        answer = generate_followup_answer("", result, use_gemini=False)
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 0)

    def test_all_seven_classes_load_and_predict(self):
        """Verify that samples across all seven concentration levels load and predict."""
        sample_map = {
            "0%": "T0S01",
            "1%": "T1S01",
            "2%": "T2S01",
            "3%": "T3S01",
            "5%": "T5S01",
            "7%": "T7S01",
            "9%": "T9S01",
        }
        valid_classes = {"0%", "1%", "2%", "3%", "5%", "7%", "9%"}
        for target_label, sid in sample_map.items():
            features, actual, meta = load_dataset_sample(sid)
            result = run_sample_analysis(
                features=features,
                sample_id=sid,
                actual_level=actual,
                source_label="Batch Test",
                user_id="test_runner",
                use_gemini=False,
                sample_meta=meta,
            )
            self.assertIn(result.prediction.predicted_class, valid_classes)
            self.assertIsNotNone(result.prediction.predicted_percentage)
            self.assertIn("executive_summary", result.structured_explanation)

    def test_gemini_unavailable_fallback_does_not_crash(self):
        """When Gemini encounters an error or network drop, run_sample_analysis falls back gracefully."""
        features, actual, meta = load_dataset_sample("T0S01")
        # In sandboxed test runner, live outbound network is blocked, so use_gemini=True
        # automatically exercises the graceful fallback path without crashing.
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Fallback Test",
            user_id="test_runner",
            use_gemini=True,
            sample_meta=meta,
        )
        self.assertIsNotNone(result)
        self.assertIn(result.analysis_mode, ("deterministic_fallback", "gemini_llm"))
        self.assertIn("executive_summary", result.structured_explanation)

    def test_report_contains_no_secrets(self):
        """Exported markdown and JSON must never contain sensitive keys or tokens."""
        features, actual, meta = load_dataset_sample("T0S01")
        result = run_sample_analysis(
            features=features,
            sample_id="T0S01",
            actual_level=actual,
            source_label="Security Test",
            user_id="test_runner",
            use_gemini=False,
            sample_meta=meta,
        )
        md = export_report_markdown(result)
        json_data = str(result.to_dict())

        for sensitive in ("GEMINI_API_KEY", "AQ.Ab8", "FoodSure2026!", "password_hash"):
            self.assertNotIn(sensitive, md)
            self.assertNotIn(sensitive, json_data)

    def test_depth_modes_stored_and_structured(self):
        """Test all three depth modes: quick, detailed, technical."""
        features, actual, meta = load_dataset_sample("T0S01")
        for depth_val in ("quick", "detailed", "technical"):
            res = run_sample_analysis(
                features=features,
                sample_id="T0S01",
                actual_level=actual,
                source_label="Depth Test",
                user_id="test_runner",
                use_gemini=False,
                depth=depth_val,
                sample_meta=meta,
            )
            self.assertEqual(res.explanation_depth, depth_val)
            self.assertIn("executive_summary", res.structured_explanation)


if __name__ == "__main__":
    unittest.main()
