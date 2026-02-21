import importlib.util
import unittest
from pathlib import Path


def load_module(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckFixtureBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.module = load_module(
            "check_fixture_balance", root / "scripts" / "check_fixture_balance.py"
        )

    def test_evaluate_fixture_passes_when_all_requirements_met(self):
        rows = [
            {
                "id": f"m{i}",
                "gold_tier": (i % 3) + 1,
                "archive_safe": i % 3 == 0,
                "send_allowed": False,
                "scenario_tags": [
                    "work",
                    "personal",
                    "school",
                    "medical",
                    "finance",
                    "marketing",
                    "thread-reply",
                    "ambiguity",
                ],
            }
            for i in range(1, 13)
        ]
        report = self.module.evaluate_fixture(
            rows,
            min_cases=10,
            required_tags=[
                "work",
                "personal",
                "school",
                "medical",
                "finance",
                "marketing",
                "thread-reply",
                "ambiguity",
            ],
            min_tag_count=1,
            min_tier_count=2,
        )
        self.assertEqual(report["failures"], [])

    def test_evaluate_fixture_reports_missing_tags_and_low_case_count(self):
        rows = [
            {
                "id": "m1",
                "gold_tier": 1,
                "archive_safe": False,
                "send_allowed": False,
                "scenario_tags": ["work"],
            },
            {
                "id": "m2",
                "gold_tier": 2,
                "archive_safe": False,
                "send_allowed": False,
                "scenario_tags": ["personal"],
            },
        ]
        report = self.module.evaluate_fixture(
            rows,
            min_cases=5,
            required_tags=["work", "personal", "finance"],
            min_tag_count=1,
            min_tier_count=1,
        )
        failures = "\n".join(report["failures"])
        self.assertIn("Case count", failures)
        self.assertIn("Missing required tag coverage: finance", failures)


if __name__ == "__main__":
    unittest.main()
