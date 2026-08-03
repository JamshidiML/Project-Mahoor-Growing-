from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from score_cycle import WEIGHTS, calculate, child_signal_gate, classify, validate_privacy  # noqa: E402


def full_data(score: int | None = 3) -> dict:
    return {
        "metrics": {
            key: {"score": score, "evidence": "test"}
            for key in WEIGHTS
        },
        "child_experience_signals": {
            "felt_safe_at_home": "GREEN",
            "school_distress": "UNKNOWN",
        },
        "privacy_check": {
            "contains_child_audio": False,
            "contains_other_child_names": False,
            "contains_school_identifiers": False,
            "contains_medical_documents": False,
        },
    }


class ScoreCycleTests(unittest.TestCase):
    def test_all_three_scores_100(self) -> None:
        score, coverage, _results, missing = calculate(full_data(3))
        self.assertEqual(score, 100.0)
        self.assertEqual(coverage, 1.0)
        self.assertEqual(missing, [])
        self.assertEqual(classify(score), "GREEN")

    def test_all_two_scores_yellow(self) -> None:
        score, _coverage, _results, _missing = calculate(full_data(2))
        self.assertAlmostEqual(score or 0, 66.7, places=1)
        self.assertEqual(classify(score), "ORANGE")

    def test_insufficient_data(self) -> None:
        data = full_data(None)
        for index, key in enumerate(WEIGHTS):
            if index < 5:
                data["metrics"][key]["score"] = 3
        score, coverage, _results, _missing = calculate(data)
        self.assertIsNone(score)
        self.assertLess(coverage, 0.70)
        self.assertEqual(classify(score), "INSUFFICIENT_DATA")

    def test_red_child_signal_is_separate_gate(self) -> None:
        data = full_data(3)
        data["child_experience_signals"]["bullying_or_harm"] = "RED"
        red, invalid = child_signal_gate(data)
        self.assertIn("bullying_or_harm", red)
        self.assertEqual(invalid, [])

    def test_privacy_warning(self) -> None:
        data = full_data(3)
        data["privacy_check"]["contains_child_audio"] = True
        self.assertIn("contains_child_audio", validate_privacy(data))


if __name__ == "__main__":
    unittest.main()
