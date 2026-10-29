import unittest

import pandas as pd

from ui.integration import parse_ftir_csv
from ui.integration import dataset_sample


class TestFtirCsvValidation(unittest.TestCase):
    def setUp(self):
        self.columns = ["wave_1", "wave_2", "wave_3"]

    def test_accepts_one_named_row_and_preserves_sample_id(self):
        payload = b"Sample_ID,wave_2,wave_1,wave_3\nT0S01,2,1,3\n"

        sample_id, features = parse_ftir_csv(payload, self.columns)

        self.assertEqual(sample_id, "T0S01")
        self.assertEqual(list(features.columns), self.columns)
        self.assertEqual(features.iloc[0].tolist(), [1.0, 2.0, 3.0])

    def test_rejects_multiple_samples(self):
        payload = b"wave_1,wave_2,wave_3\n1,2,3\n4,5,6\n"

        with self.assertRaisesRegex(ValueError, "exactly one"):
            parse_ftir_csv(payload, self.columns)

    def test_rejects_missing_or_unexpected_feature_columns(self):
        payload = b"wave_1,wave_2,other\n1,2,3\n"

        with self.assertRaisesRegex(ValueError, "columns must match"):
            parse_ftir_csv(payload, self.columns)

    def test_rejects_target_columns(self):
        payload = b"wave_1,wave_2,wave_3,Target\n1,2,3,0\n"

        with self.assertRaisesRegex(ValueError, "Remove target"):
            parse_ftir_csv(payload, self.columns)

    def test_rejects_non_numeric_values(self):
        payload = b"wave_1,wave_2,wave_3\n1,invalid,3\n"

        with self.assertRaisesRegex(ValueError, "must be numeric"):
            parse_ftir_csv(payload, self.columns)

    def test_rejects_non_finite_values(self):
        payload = b"wave_1,wave_2,wave_3\n1,inf,3\n"

        with self.assertRaisesRegex(ValueError, "finite"):
            parse_ftir_csv(payload, self.columns)

    def test_dataset_sample_joins_target_by_sample_id(self):
        data = {
            "features": {
                "FTIR": pd.DataFrame(
                    [[10, 20, 30], [40, 50, 60]],
                    columns=self.columns,
                    index=["T1S01", "T0S01"],
                )
            },
            "train_ids": ["T1S01"],
            "y_train": pd.Series([1.0]),
            "test_ids": ["T0S01"],
            "y_test": pd.Series([0.0]),
        }

        features, actual = dataset_sample(data, "T0S01", self.columns)

        self.assertEqual(features.iloc[0].tolist(), [40, 50, 60])
        self.assertEqual(actual, 0.0)


if __name__ == "__main__":
    unittest.main()
