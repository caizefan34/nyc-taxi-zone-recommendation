"""Stable module entry point for the real planning parameter grid."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "src/2_recommendation_algorithm/parameter_selection.py"
    spec = importlib.util.spec_from_file_location("parameter_selection_entry", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
