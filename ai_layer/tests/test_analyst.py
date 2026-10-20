import unittest

from ai_layer.analyst import (
    AnalystInputError,
    AnalystError,
    _parse_llm_output,
    analyze,
)


class TestFoodSureAnalyst(unittest.TestCase):

    def setUp(self):
        self.payload = {
            "model_version": "research-model-v1",
            "modalities_used": ["color", "ftir"],
            "model_result": {
                "prediction": 3,
                "target_type": "classification",
            },
            "evidence": [
                "Example evidence supplied by a test fixture."
            ],
            "uncertainty_flags": [
                "External validation has not been established."
            ],
            "limitations": [
                "Evaluation uses a limited research dataset."
            ],
        }

    def test_deterministic_analysis(self):
        result = analyze(self.payload, use_llm=False)

        self.assertEqual(
            result["analysis_mode"],
            "deterministic_fallback",
        )
        self.assertEqual(
            result["model_result"]["prediction"],
            3,
        )
        self.assertIn("laboratory", result["recommended_verification"])

    def test_missing_model_result_is_rejected(self):
        invalid_payload = {
            "model_version": "test",
            "modalities_used": [],
        }

        with self.assertRaises(AnalystInputError):
            analyze(invalid_payload, use_llm=False)

    def test_missing_prediction_does_not_invent_one(self):
        payload = dict(self.payload)
        payload["model_result"] = {
            "target_type": "classification"
        }

        result = analyze(payload, use_llm=False)

        self.assertIsNone(result["model_result"]["prediction"])
        self.assertIn("does not contain a prediction", result["summary"])

    def test_missing_uncertainty_does_not_claim_certainty(self):
        payload = dict(self.payload)
        payload.pop("uncertainty_flags")

        result = analyze(payload, use_llm=False)

        self.assertIn("uncertainty is absent", result["uncertainty_notes"][0])

    def test_malformed_llm_fields_are_rejected(self):
        response = (
            '{"summary":"ok","model_result":{},"supporting_evidence":[{}],'
            '"interpretation":"ok","uncertainty_notes":[],"limitations":[],'
            '"recommended_verification":"verify"}'
        )
        with self.assertRaisesRegex(AnalystError, "supporting_evidence"):
            _parse_llm_output(response)

    def test_non_finite_llm_json_is_rejected(self):
        response = (
            '{"summary":"ok","model_result":{},"supporting_evidence":[],'
            '"interpretation":"ok","uncertainty_notes":[],"limitations":[],'
            '"recommended_verification":"verify","extra":NaN}'
        )
        with self.assertRaisesRegex(AnalystError, "valid JSON"):
            _parse_llm_output(response)


if __name__ == "__main__":
    unittest.main()