"""Tests for reproduction verification script."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_verify_script_exists():
    assert (REPO_ROOT / "scripts" / "verify_reproduction.py").exists()


def test_verify_check_env():
    result = subprocess.run(
        [sys.executable, "scripts/verify_reproduction.py", "--check-env", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert "checks" in report
    assert len(report["checks"]) > 0


def test_verify_quick():
    result = subprocess.run(
        [sys.executable, "scripts/verify_reproduction.py", "--quick", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    checks = report["checks"]
    for check in checks:
        if isinstance(check, dict) and "pass" in check:
            assert check["pass"], f"Check failed: {check}"


def test_external_submission_demo_exists():
    demo_dir = REPO_ROOT / "examples" / "external_submission_demo"
    assert demo_dir.exists()
    assert (demo_dir / "README.md").exists()
    assert (demo_dir / "custom_policy.py").exists()
    assert (demo_dir / "run_benchmark.py").exists()
