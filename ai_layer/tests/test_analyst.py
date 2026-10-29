"""Tests for ai_layer/analyst.py — new 8-section explanation schema."""
import json
import unittest

from ai_layer.analyst import (
    AnalystError,
    AnalystInputError,
    _parse_llm_output,
    analyze,
    deterministic_analysis,
)

# Minimal valid payload for all tests
_BASE_PAYLOAD = {
    "model_version": "research-model-v1",
    "modalities_used": ["ftir"],
    "model_result": {
        "prediction": "3%",
        "regression_estimate": 3.1,
        "target_type": "classification",
        "model_version": "foodsure-v1",
    },
    "evidence": [
        {"description": "Example evidence supplied by a test fixture.", "source": "test"}
    ],
    "uncertainty_flags": [
        "External validation has not been established."
    ],
    "limitations": [
        "Evaluation uses a limited research dataset."
    ],
}

_VALID_SCHEMA_RESPONSE = json.dumps({
    "executive_summary": "The model predicted 3% adulteration.",
    "result_interpretation": "The classifier assigned class 3%.",
    "evidence_and_reasoning": [
        {
            "evidence": "ATR-FTIR spectrum processed through PCA.",
            "meaning": "Spectral fingerprint compressed to 13 components.",
            "connection": "Components matched 3% training cluster.",
            "limitation": "No feature importance available.",
        }
    ],
    "scientific_explanation": "Turmeric adulteration means wheat flour was added.",
    "confidence_and_uncertainty": "Probabilities are not calibrated.",
    "practical_implications": "Submit to lab for confirmation.",
    "recommended_next_steps": ["Confirm with HPLC.", "Document chain of custody."],
    "limitations": ["Research prototype only.", "FTIR-trained on 350 samples."],
    "follow_up_questions": [
        "What does this class mean?",
        "Why differ from regression?",
        "How reliable is FTIR?",
        "What lab test confirms this?",
        "What are the model limitations?",
    ],
})


class TestDeterministicAnalysis(unittest.TestCase):

    def test_returns_8_section_dict(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
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
            self.assertIn(field, result, f"Missing field: {field}")

    def test_analysis_mode_is_deterministic(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
        self.assertEqual(result["analysis_mode"], "deterministic_fallback")

    def test_prediction_preserved_in_exec_summary(self):
        result = deterministic_analysis(_BASE_PAYLOAD)
        # The executive summary must mention the prediction
        self.assertIn("3%", result["executive_summary"])

    def test_missing_prediction_does_not_invent_one(self):
        payload = dict(_BASE_PAYLOAD)
        payload["model_result"] = {"target_type": "classification"}
        result = analyze(payload, use_llm=False)
        # Should mention no prediction found
        self.assertIn("does not contain", result["executive_summary"])

    def test_no_prediction_summary_is_honest(self):
        payload = dict(_BASE_PAYLOAD)
        payload["model_result"] = {}
        result = analyze(payload, use_llm=False)
        self.assertIn("does not contain", result["executive_summary"])

    def test_uncertainty_flags_reflected(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
        conf = result["confidence_and_uncertainty"]
        self.assertIn("External validation", conf)

    def test_missing_uncertainty_does_not_claim_certainty(self):
        payload = dict(_BASE_PAYLOAD)
        payload.pop("uncertainty_flags")
        result = analyze(payload, use_llm=False)
        conf = result["confidence_and_uncertainty"]
        self.assertIn("uncertainty is absent", conf)

    def test_evidence_and_reasoning_is_list(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
        ear = result["evidence_and_reasoning"]
        self.assertIsInstance(ear, list)
        self.assertGreater(len(ear), 0)
        for item in ear:
            for key in ("evidence", "meaning", "connection", "limitation"):
                self.assertIn(key, item)

    def test_recommended_next_steps_is_list_of_str(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
        steps = result["recommended_next_steps"]
        self.assertIsInstance(steps, list)
        self.assertTrue(all(isinstance(s, str) for s in steps))

    def test_limitations_includes_prototype_warning(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False)
        lims = " ".join(result["limitations"])
        self.assertIn("research prototype", lims.lower())

    def test_depth_quick_accepted(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False, depth="quick")
        self.assertEqual(result["depth"], "quick")

    def test_depth_technical_accepted(self):
        result = analyze(_BASE_PAYLOAD, use_llm=False, depth="technical")
        self.assertEqual(result["depth"], "technical")


class TestPayloadValidation(unittest.TestCase):

    def test_missing_model_result_is_rejected(self):
        invalid = {
            "model_version": "test",
            "modalities_used": [],
        }
        with self.assertRaises(AnalystInputError):
            analyze(invalid, use_llm=False)

    def test_non_dict_model_result_is_rejected(self):
        invalid = dict(_BASE_PAYLOAD)
        invalid["model_result"] = "not a dict"
        with self.assertRaises(AnalystInputError):
            analyze(invalid, use_llm=False)

    def test_non_list_modalities_is_rejected(self):
        invalid = dict(_BASE_PAYLOAD)
        invalid["modalities_used"] = "ftir"
        with self.assertRaises(AnalystInputError):
            analyze(invalid, use_llm=False)

    def test_non_finite_payload_value_is_rejected(self):
        import math
        invalid = dict(_BASE_PAYLOAD)
        invalid["model_result"] = {"prediction": math.inf}
        with self.assertRaises(AnalystInputError):
            analyze(invalid, use_llm=False)


class TestParseLLMOutput(unittest.TestCase):

    def test_valid_schema_is_accepted(self):
        result = _parse_llm_output(_VALID_SCHEMA_RESPONSE)
        self.assertIn("executive_summary", result)
        self.assertIn("evidence_and_reasoning", result)
        self.assertIsInstance(result["evidence_and_reasoning"], list)

    def test_missing_required_field_is_rejected(self):
        bad = json.loads(_VALID_SCHEMA_RESPONSE)
        del bad["executive_summary"]
        with self.assertRaises(AnalystError):
            _parse_llm_output(json.dumps(bad))

    def test_evidence_missing_subfield_is_rejected(self):
        bad = json.loads(_VALID_SCHEMA_RESPONSE)
        bad["evidence_and_reasoning"][0].pop("connection")
        with self.assertRaises(AnalystError):
            _parse_llm_output(json.dumps(bad))

    def test_empty_evidence_list_is_rejected(self):
        bad = json.loads(_VALID_SCHEMA_RESPONSE)
        bad["evidence_and_reasoning"] = []
        with self.assertRaises(AnalystError):
            _parse_llm_output(json.dumps(bad))

    def test_non_string_exec_summary_is_rejected(self):
        bad = json.loads(_VALID_SCHEMA_RESPONSE)
        bad["executive_summary"] = 42
        with self.assertRaises(AnalystError):
            _parse_llm_output(json.dumps(bad))

    def test_non_list_recommended_steps_is_rejected(self):
        bad = json.loads(_VALID_SCHEMA_RESPONSE)
        bad["recommended_next_steps"] = "confirm with HPLC"
        with self.assertRaises(AnalystError):
            _parse_llm_output(json.dumps(bad))

    def test_non_finite_json_is_rejected(self):
        response = (
            '{"executive_summary":"ok","result_interpretation":"ok",'
            '"evidence_and_reasoning":[{"evidence":"e","meaning":"m",'
            '"connection":"c","limitation":"l"}],'
            '"scientific_explanation":"ok","confidence_and_uncertainty":"ok",'
            '"practical_implications":"ok",'
            '"recommended_next_steps":[],"limitations":[],"extra":NaN}'
        )
        with self.assertRaisesRegex(AnalystError, "valid JSON"):
            _parse_llm_output(response)

    def test_non_dict_response_is_rejected(self):
        with self.assertRaises(AnalystError):
            _parse_llm_output('["not", "a", "dict"]')

    def test_invalid_json_is_rejected(self):
        with self.assertRaisesRegex(AnalystError, "valid JSON"):
            _parse_llm_output("this is not json at all")


if __name__ == "__main__":
    unittest.main()
