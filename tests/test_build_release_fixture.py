import importlib.util
import tempfile
import unittest
from pathlib import Path


def load_module(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildReleaseFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.module = load_module("build_release_fixture", root / "scripts" / "build_release_fixture.py")

    def test_build_fixture_merges_raw_and_labels(self):
        raw_rows = [
            {"id": "m1", "from": "a@example.com", "subject": "Subject 1"},
            {"id": "m2", "from": "b@example.com", "subject": "Subject 2"},
        ]
        label_rows = [
            {
                "id": "m1",
                "gold_tier": 1,
                "archive_safe": False,
                "send_allowed": False,
                "scenario_tags": ["work", "thread-reply"],
                "reviewer": "triage-a",
            },
            {
                "id": "m2",
                "gold_tier": 3,
                "archive_safe": True,
                "send_allowed": False,
                "scenario_tags": ["marketing"],
                "reviewer": "triage-a",
            },
        ]

        result = self.module.build_fixture(raw_rows, label_rows)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "m1")
        self.assertEqual(result[0]["gold_tier"], 1)
        self.assertEqual(result[0]["archive_safe"], False)
        self.assertEqual(result[0]["scenario_tags"], ["thread-reply", "work"])
        self.assertEqual(result[1]["gold_tier"], 3)

    def test_build_fixture_fails_when_label_missing(self):
        raw_rows = [{"id": "m1"}, {"id": "m2"}]
        label_rows = [
            {
                "id": "m1",
                "gold_tier": 2,
                "archive_safe": False,
                "send_allowed": False,
                "scenario_tags": ["personal"],
                "reviewer": "triage-a",
            }
        ]
        with self.assertRaisesRegex(ValueError, "Missing labels for 1 ids"):
            self.module.build_fixture(raw_rows, label_rows)

    def test_round_trip_jsonl(self):
        rows = [{"id": "m1", "gold_tier": 1, "archive_safe": False, "send_allowed": False}]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "fixture.jsonl"
            self.module.write_jsonl(output, rows)
            loaded = self.module.load_jsonl(output)
        self.assertEqual(rows, loaded)


if __name__ == "__main__":
    unittest.main()
