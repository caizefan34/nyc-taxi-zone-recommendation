#!/usr/bin/env python3
"""One-command quickstart: check environment, run demo, generate report.

Usage:
    python scripts/quickstart.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print(f"ERROR: Python 3.10+ required (found {v.major}.{v.minor})")
        sys.exit(1)
    print(f"  Python {v.major}.{v.minor}.{v.micro} — OK")


def check_imports():
    required = {"numpy", "pandas", "pyarrow", "scipy"}
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  {pkg} — OK")
        except ImportError:
            missing.append(pkg)
            print(f"  {pkg} — MISSING")
    if missing:
        print(f"\nInstall missing packages: pip install {' '.join(missing)}")
        return False
    return True


def run_demo():
    print("\n[3/4] Running demo strategy comparison...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_algorithm_math.py", "-q", "--tb=short"],
        cwd=ROOT, capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  Demo tests passed!")
        return True
    print("  Demo tests had issues (this is OK for quickstart)")
    print(f"  {result.stderr[-200:] if result.stderr else 'see pytest output'}")
    return False


def main():
    print("=" * 60)
    print("Dynamic Urban Mobility Decision System — Quickstart")
    print("=" * 60)

    print("\n[1/4] Checking Python version...")
    check_python()

    print("\n[2/4] Checking dependencies...")
    deps_ok = check_imports()

    demo_ok = run_demo()

    print("\n[4/4] Summary")
    print("  Python: OK")
    print(f"  Dependencies: {'OK' if deps_ok else 'Some missing'}")
    print(f"  Demo: {'OK' if demo_ok else 'Issues'}")

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  Run full test suite:    pytest tests/")
    print("  Run data pipeline:      python -m scripts.run_data_pipeline")
    print("  Run full benchmark:     make all")
    print("  Read the tutorial:      docs/tutorial_first_experiment.md")
    print("  Try the web demo:       streamlit run app/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
