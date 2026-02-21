import importlib.util
import sys
import unittest
from pathlib import Path


def load_module(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class GenerateReleaseReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.module = load_module(
            "generate_release_report", root / "scripts" / "generate_release_report.py"
        )

    def test_build_report_marks_go_when_all_pass(self):
        gate = self.module.GateResult(
            name="structural",
            passed=True,
            command="python3 scripts/validate_release.py",
            output="ok",
            exit_code=0,
        )
        report = self.module.build_report([gate])
        self.assertIn("Final decision: **GO**", report)
        self.assertIn("PASS: `structural`", report)

    def test_build_report_marks_no_go_on_failure(self):
        ok = self.module.GateResult(
            name="structural",
            passed=True,
            command="python3 scripts/validate_release.py",
            output="ok",
            exit_code=0,
        )
        bad = self.module.GateResult(
            name="canary",
            passed=False,
            command="python3 scripts/check_canary_evidence.py --enforce",
            output="fail",
            exit_code=1,
        )
        report = self.module.build_report([ok, bad])
        self.assertIn("Final decision: **NO-GO**", report)
        self.assertIn("`canary` failed", report)


if __name__ == "__main__":
    unittest.main()
