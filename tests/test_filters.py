import unittest

import numpy as np
import pandas as pd

from src.new_project.filters import FilterSpec, apply_filters


class TestFilters(unittest.TestCase):
    def test_no_spec_returns_original(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        pd.testing.assert_frame_equal(apply_filters(df, None), df)

    def test_numeric_range(self) -> None:
        df = pd.DataFrame({"score": [1, 5, 10, np.nan]})
        spec = FilterSpec(column="score", kind="numeric", values=(2.0, 8.0))
        out = apply_filters(df, spec)
        self.assertEqual(out["score"].tolist(), [5.0])

    def test_categorical_keep(self) -> None:
        df = pd.DataFrame({"city": ["A", "B", "C"]})
        spec = FilterSpec(column="city", kind="categorical", values={"A", "C"})
        out = apply_filters(df, spec)
        self.assertEqual(out["city"].tolist(), ["A", "C"])

    def test_missing_column_is_ignored(self) -> None:
        df = pd.DataFrame({"a": [1]})
        spec = FilterSpec(column="missing", kind="numeric", values=(0.0, 1.0))
        pd.testing.assert_frame_equal(apply_filters(df, spec), df)


if __name__ == "__main__":
    unittest.main()
