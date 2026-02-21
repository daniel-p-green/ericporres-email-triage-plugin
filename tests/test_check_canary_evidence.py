import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path


def load_module(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckCanaryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.module = load_module(
            "check_canary_evidence", root / "scripts" / "check_canary_evidence.py"
        )

    def test_evaluate_canary_passes_with_complete_week(self):
        start = date(2026, 2, 13)
        rows = []
        for offset in range(7):
            day = (start + timedelta(days=offset)).isoformat()
            rows.append(
                {
                    "date": day,
                    "run_id": f"{day}-1d",
                    "window_query": "newer_than:1d",
                    "email_count": 20,
                    "high_volume": False,
                    "is_success": True,
                    "unsafe_action": False,
                    "critical_misarchive": False,
                    "mcp_failure": False,
                    "reviewer": "qa",
                    "notes": "",
                }
            )
            rows.append(
                {
                    "date": day,
                    "run_id": f"{day}-3d",
                    "window_query": "newer_than:3d",
                    "email_count": 55 if offset == 2 else 30,
                    "high_volume": offset == 2,
                    "is_success": True,
                    "unsafe_action": False,
                    "critical_misarchive": False,
                    "mcp_failure": False,
                    "reviewer": "qa",
                    "notes": "",
                }
            )

        report = self.module.evaluate_canary(rows, required_days=7, runs_per_day=2)
        self.assertEqual(report["failures"], [])

    def test_evaluate_canary_fails_on_unsafe_action(self):
        rows = [
            {
                "date": "2026-02-20",
                "run_id": "r1",
                "window_query": "newer_than:1d",
                "email_count": 10,
                "high_volume": False,
                "is_success": True,
                "unsafe_action": True,
                "critical_misarchive": False,
                "mcp_failure": False,
                "reviewer": "qa",
                "notes": "",
            },
            {
                "date": "2026-02-20",
                "run_id": "r2",
                "window_query": "newer_than:3d",
                "email_count": 60,
                "high_volume": True,
                "is_success": True,
                "unsafe_action": False,
                "critical_misarchive": False,
                "mcp_failure": False,
                "reviewer": "qa",
                "notes": "",
            },
        ]
        report = self.module.evaluate_canary(rows, required_days=1, runs_per_day=2)
        self.assertTrue(any("Unsafe actions detected" in f for f in report["failures"]))


if __name__ == "__main__":
    unittest.main()
