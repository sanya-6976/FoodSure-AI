import unittest

from ai_layer.report_generator import (
    ReportValidationError,
    generate_report,
    report_to_json,
)


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.evidence = {
            "model_version": "research-v1",
            "modalities_used": ["color"],
            "model_result": {
                "prediction": 3,
                "target_type": "classification",
            },
        }

        self.analysis = {
            "summary": "A test model prediction was supplied.",
            "interpretation": "This is not a laboratory finding.",
            "supporting_evidence": ["Test evidence"],
            "limitations": ["External validation is not established."],
            "recommended_verification": "Use validated laboratory testing.",
            "analysis_mode": "deterministic_fallback",
        }

        self.uncertainty = {
            "status": "caution",
            "flags": ["External validation is unavailable."],
            "recommendations": ["Verify independently."],
        }

    def test_report_contains_required_sections(self):
        report = generate_report(
            evidence_payload=self.evidence,
            analyst_result=self.analysis,
            uncertainty_result=self.uncertainty,
        )

        self.assertIn("model_result", report)
        self.assertIn("analysis", report)
        self.assertIn("uncertainty", report)
        self.assertIn("disclaimer", report)

    def test_report_preserves_model_prediction(self):
        report = generate_report(
            evidence_payload=self.evidence,
            analyst_result=self.analysis,
            uncertainty_result=self.uncertainty,
        )

        self.assertEqual(
            report["model_result"]["prediction"],
            3,
        )

    def test_json_export(self):
        report = generate_report(
            evidence_payload=self.evidence,
            analyst_result=self.analysis,
            uncertainty_result=self.uncertainty,
        )

        serialized = report_to_json(report)
        self.assertIn('"report_schema_version": "1.0"', serialized)

    def test_invalid_evidence_is_rejected(self):
        with self.assertRaises(ReportValidationError):
            generate_report(
                evidence_payload={},
                analyst_result=self.analysis,
                uncertainty_result=self.uncertainty,
            )

    def test_malformed_supporting_evidence_is_rejected(self):
        analysis = dict(self.analysis, supporting_evidence=[{"claim": "unverified"}])
        with self.assertRaisesRegex(ReportValidationError, "supporting_evidence"):
            generate_report(
                evidence_payload=self.evidence,
                analyst_result=analysis,
                uncertainty_result=self.uncertainty,
            )

    def test_empty_analysis_is_rejected(self):
        analysis = dict(self.analysis, summary=" ")
        with self.assertRaisesRegex(ReportValidationError, "non-empty string"):
            generate_report(
                evidence_payload=self.evidence,
                analyst_result=analysis,
                uncertainty_result=self.uncertainty,
            )


if __name__ == "__main__":
    unittest.main()