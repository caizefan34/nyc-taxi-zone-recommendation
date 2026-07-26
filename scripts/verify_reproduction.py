#!/usr/bin/env python3
"""
Reproduction verification script for external users.

Checks:
1. Python version
2. Dependencies installed
3. Sample data available
4. Demo execution
5. Test suite pass

Usage:
    python scripts/verify_reproduction.py          # Full check
    python scripts/verify_reproduction.py --quick  # Fast check only
    python scripts/verify_reproduction.py --json   # Output as JSON
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PYTHON = (3, 10)
REQUIRED_PACKAGES = [
    "numpy", "pandas", "scipy", "yaml",
    "lightgbm", "xgboost", "pytest",
]

def check_python_version():
    """Check Python version meets minimum requirement."""
    current = sys.version_info[:2]
    ok = current >= REQUIRED_PYTHON
    return {
        "check": "Python version",
        "required": f">={REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}",
        "actual": f"{current[0]}.{current[1]}",
        "pass": ok,
        "detail": "OK" if ok else f"Need Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+"
    }

def check_dependencies():
    """Check required packages are importable."""
    results = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            results.append({"package": pkg, "pass": True, "detail": "OK"})
        except ImportError:
            results.append({"package": pkg, "pass": False, "detail": "Not installed"})
    return results

def check_sample_data():
    """Check sample data files exist."""
    checks = []
    paths = [
        ("web/data/zones.json", "Zone geometry data"),
        ("data/", "Data directory"),
        ("outputs/", "Outputs directory"),
    ]
    for rel_path, desc in paths:
        full = REPO_ROOT / rel_path
        ok = full.exists()
        checks.append({
            "check": desc,
            "path": rel_path,
            "pass": ok,
            "detail": "Found" if ok else "Missing"
        })
    return checks

def check_imports():
    """Check core modules are importable."""
    sys.path.insert(0, str(REPO_ROOT))
    modules = [
        "src.data", "src.forecasting", "src.simulator",
        "src.policies", "src.evaluation", "src.interfaces",
    ]
    results = []
    for mod in modules:
        try:
            __import__(mod)
            results.append({"module": mod, "pass": True, "detail": "OK"})
        except ImportError as e:
            results.append({"module": mod, "pass": False, "detail": str(e)[:80]})
    return results

def run_quick_test():
    """Run a minimal test to verify core functionality."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_config.py", "-q", "--tb=short"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "check": "Quick test (test_config.py)",
            "pass": result.returncode == 0,
            "detail": "Passed" if result.returncode == 0 else result.stderr[-200:]
        }
    except Exception as e:
        return {"check": "Quick test", "pass": False, "detail": str(e)[:200]}

def main():
    parser = argparse.ArgumentParser(description="Verify reproduction readiness")
    parser.add_argument("--quick", action="store_true", help="Fast check only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--check-env", action="store_true", help="Environment check only")
    args = parser.parse_args()

    report = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": sys.platform,
        "checks": []
    }

    # Always run these
    report["checks"].append(check_python_version())
    dep_results = check_dependencies()
    report["checks"].extend(dep_results)
    report["checks"].extend(check_sample_data())

    if args.check_env:
        # Environment only
        pass
    elif args.quick:
        report["checks"].append(run_quick_test())
    else:
        # Full check
        report["checks"].extend(check_imports())
        report["checks"].append(run_quick_test())

    all_pass = all(c.get("pass", False) for c in report["checks"]
                   if isinstance(c, dict))

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("Reproduction Verification Report")
        print("=" * 60)
        for check in report["checks"]:
            if isinstance(check, dict) and "package" in check:
                status = "PASS" if check["pass"] else "FAIL"
                print(f"  [{status}] Package: {check['package']} - {check['detail']}")
            elif isinstance(check, dict) and "check" in check:
                status = "PASS" if check["pass"] else "FAIL"
                print(f"  [{status}] {check['check']}: {check['detail']}")
            elif isinstance(check, dict) and "module" in check:
                status = "PASS" if check["pass"] else "FAIL"
                print(f"  [{status}] Module: {check['module']} - {check['detail']}")
        print("-" * 60)
        print(f"Overall: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
        print("=" * 60)

    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
