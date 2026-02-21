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


class CheckHumanSignoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.module = load_module("check_human_signoff", root / "scripts" / "check_human_signoff.py")

    def test_evaluate_signoff_passes(self):
        signoff = {
            "eric_transcript_reviews": 3,
            "voice_quality_approved": True,
            "archive_clarity_approved": True,
            "approved_by": "Eric Porres",
            "approved_at": "2026-02-20T20:00:00Z",
        }
        report = self.module.evaluate_signoff(signoff, min_reviews=3)
        self.assertEqual(report["failures"], [])

    def test_evaluate_signoff_fails_when_requirements_not_met(self):
        signoff = {
            "eric_transcript_reviews": 1,
            "voice_quality_approved": False,
            "archive_clarity_approved": False,
            "approved_by": "",
            "approved_at": "",
        }
        report = self.module.evaluate_signoff(signoff, min_reviews=3)
        text = "\n".join(report["failures"])
        self.assertIn("below required minimum", text)
        self.assertIn("voice_quality_approved is false", text)
        self.assertIn("archive_clarity_approved is false", text)
        self.assertIn("approved_by is empty", text)
        self.assertIn("approved_at is empty", text)


if __name__ == "__main__":
    unittest.main()
