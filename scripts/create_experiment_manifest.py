#!/usr/bin/env python3
"""Generate reproducible experiment manifest capturing current environment state."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone


def run(cmd):
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def get_packages():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, check=True,
        )
        return {p["name"]: p["version"] for p in json.loads(r.stdout)}
    except Exception:
        return {"error": "pip list failed"}


def main():
    manifest = {
        "experiment_manifest_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": {
            "commit_hash": run(["git", "rev-parse", "HEAD"]),
            "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "status": run(["git", "status", "--short"]),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(), "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": get_packages(),
        "configs": {},
    }
    if os.path.isdir("configs"):
        try:
            import yaml
            for fn in sorted(os.listdir("configs")):
                if fn.endswith((".yaml", ".yml")):
                    with open(os.path.join("configs", fn), encoding="utf-8") as f:
                        manifest["configs"][fn] = yaml.safe_load(f)
        except ImportError:
            manifest["configs"] = {"error": "pyyaml not available"}
        except Exception as e:
            manifest["configs"] = {"error": str(e)}
    os.makedirs("outputs", exist_ok=True)
    out = os.path.join("outputs", "experiment_manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"Created {out}")
    print(f"  Git commit: {manifest['git']['commit_hash'][:12]}")
    print(f"  Branch: {manifest['git']['branch']}")
    print(f"  Python: {manifest['python']['version']}")
    print(f"  Packages: {len(manifest.get('packages', {}))}")
    print(f"  Configs loaded: {len(manifest.get('configs', {}))}")


if __name__ == "__main__":
    main()
