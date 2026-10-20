import unittest

from ai_layer.uncertainty import (
    UncertaintyInputError,
    assess_uncertainty,
)


class TestUncertainty(unittest.TestCase):

    def test_missing_evidence_triggers_caution(self):
        result = assess_uncertainty(
            model_result={"prediction": 3},
            modalities_used=["color"],
            evidence=[],
        )

        self.assertEqual(result["status"], "caution")
        self.assertTrue(any("evidence" in flag.lower() for flag in result["flags"]))

    def test_out_of_distribution_triggers_high_caution(self):
        result = assess_uncertainty(
            model_result={"prediction": 3},
            modalities_used=["color", "ftir"],
            evidence=[{"description": "Example supplied evidence"}],
            out_of_distribution=True,
        )

        self.assertEqual(result["status"], "high_caution")
        self.assertTrue(
            any("out-of-distribution" in flag.lower() for flag in result["flags"])
        )

    def test_uncalibrated_confidence_is_flagged(self):
        result = assess_uncertainty(
            model_result={"prediction": 3},
            modalities_used=["color"],
            evidence=["Example evidence"],
            confidence=0.95,
            confidence_calibrated=False,
        )

        self.assertTrue(
            any("not documented as calibrated" in flag for flag in result["flags"])
        )

    def test_invalid_confidence_is_rejected(self):
        with self.assertRaises(UncertaintyInputError):
            assess_uncertainty(
                model_result={"prediction": 3},
                modalities_used=["color"],
                confidence=1.5,
            )

    def test_missing_prediction_triggers_high_caution(self):
        result = assess_uncertainty(
            model_result={},
            modalities_used=[],
        )

        self.assertEqual(result["status"], "high_caution")

    def test_unassessed_model_scope_is_not_assumed_supported(self):
        result = assess_uncertainty(
            model_result={"prediction": 3},
            modalities_used=["ftir"],
            evidence=[{"description": "Synthetic test fixture."}],
            model_scope_supported=None,
        )

        self.assertEqual(result["status"], "caution")
        self.assertTrue(any("scope was not assessed" in flag for flag in result["flags"]))

    def test_unreported_external_validation_is_not_assumed_unavailable(self):
        result = assess_uncertainty(
            model_result={"prediction": 3},
            modalities_used=["ftir"],
            evidence=[{"description": "Synthetic test fixture."}],
            external_validation_available=None,
        )

        self.assertTrue(
            any("availability was not supplied" in flag for flag in result["flags"])
        )


if __name__ == "__main__":
    unittest.main()