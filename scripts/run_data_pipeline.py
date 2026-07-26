"""Stable module entry point for the numeric data-clean directory."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "src/1_data_clean/clean.py"
    spec = importlib.util.spec_from_file_location("data_clean_entry", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--force-split", action="store_true")
    args = parser.parse_args()
    _module().run_pipeline(
        raw_path=args.raw,
        processed_dir=args.processed_dir,
        force_split=args.force_split,
    )


if __name__ == "__main__":
    main()
