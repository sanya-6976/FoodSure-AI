"""Contract test for the FoodSure AI layer.

Uses synthetic test data only. Does not load or evaluate an ML model.
"""

import unittest

from ai_layer.analyst import analyze
from ai_layer.evidence import build_evidence_payload
from ai_layer.report_generator import generate_report, report_to_json
from ai_layer.uncertainty import assess_uncertainty


class TestFoodSurePipelineContract(unittest.TestCase):

    def test_evidence_to_final_report(self):
        # 1. Synthetic model output for testing only.
        evidence_payload = build_evidence_payload(
            model_version="synthetic-test-v1",
            modalities_used=["color", "ftir"],
            model_result={
                "prediction": 3,
                "target_type": "classification",
            },
            feature_contributions=[
                {
                    "feature_name": "example_color_feature",
                    "value": 0.2,
                    "method": "synthetic_test_value",
                    "modality": "color",
                }
            ],
            uncertainty_flags=[
                "This is synthetic test data."
            ],
            limitations=[
                "This test does not represent a real sample."
            ],
        )

        # 2. Generate the explanation without requiring an API key.
        analyst_result = analyze(
            evidence_payload,
            use_llm=False,
        )

        # 3. Assess uncertainty using only supplied information.
        uncertainty_result = assess_uncertainty(
            model_result=evidence_payload["model_result"],
            modalities_used=evidence_payload["modalities_used"],
            evidence=evidence_payload["evidence"],
            out_of_distribution=None,
            external_validation_available=False,
            existing_flags=evidence_payload["uncertainty_flags"],
        )

        # 4. Assemble the report.
        report = generate_report(
            evidence_payload=evidence_payload,
            analyst_result=analyst_result,
            uncertainty_result=uncertainty_result,
        )

        # 5. Verify the contract.
        self.assertEqual(
            report["model_version"],
            "synthetic-test-v1",
        )
        self.assertEqual(
            report["model_result"]["prediction"],
            3,
        )
        self.assertEqual(
            report["analysis"]["analysis_mode"],
            "deterministic_fallback",
        )
        self.assertIn(
            "This is synthetic test data.",
            report["uncertainty"]["flags"],
        )
        self.assertTrue(report["disclaimer"])

        # Confirm that the complete report can be serialized.
        serialized = report_to_json(report)
        self.assertIsInstance(serialized, str)
        self.assertIn("synthetic-test-v1", serialized)


if __name__ == "__main__":
    unittest.main()