"""Tests for the unified benchmark CLI (benchmark/run.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.run import INTERNAL_MODELS, main  # noqa: E402
from benchmark.schemas.validator import validate_result  # noqa: E402


def _valid_result() -> dict:
    return {
        "model": {"name": "my_model", "version": "1.0.0", "type": "policy"},
        "benchmark_version": "2.0.0",
        "timestamp": "2026-01-01T00:00:00Z",
        "metrics": {"decision": {"ndcg_at_3": 0.9}},
        "reproducibility": {"random_seed": 42},
    }


class TestValidator:
    def test_valid_result_passes(self):
        assert validate_result(_valid_result()) == []

    def test_missing_model_fails(self):
        errors = validate_result({"metrics": {"decision": {}}})
        assert any("model" in e for e in errors)

    def test_bad_model_type_fails(self):
        result = _valid_result()
        result["model"]["type"] = "nonsense"
        errors = validate_result(result)
        assert any("model.type" in e for e in errors)

    def test_missing_metrics_fails(self):
        result = _valid_result()
        del result["metrics"]
        errors = validate_result(result)
        assert any("metrics" in e for e in errors)

    def test_validate_result_file(self, tmp_path):
        p = tmp_path / "result.json"
        p.write_text(json.dumps(_valid_result()))
        from benchmark.schemas.validator import validate_result_file

        assert validate_result_file(p) == []


class TestRunCLI:
    def test_list_flag(self, capsys):
        assert main(["--list"]) == 0
        out = capsys.readouterr().out
        assert "two_step" in out
        assert "nyc" in out

    def test_internal_model_run(self, tmp_path, monkeypatch):
        out = tmp_path / "result.json"
        monkeypatch.chdir(ROOT)
        assert main(["--model", "two_step", "--city", "nyc", "--output", str(out)]) == 0
        record = json.loads(out.read_text())
        assert record["run"]["model"] == "two_step"
        assert record["run"]["evaluation_type"] == "simulator/historical_replay"
        assert record["run"]["city"] == "nyc"

    def test_source_validation_ok(self, tmp_path, monkeypatch):
        src = tmp_path / "ext.json"
        src.write_text(json.dumps(_valid_result()))
        out = tmp_path / "out.json"
        monkeypatch.chdir(ROOT)
        assert main(["--source", str(src), "--output", str(out)]) == 0

    def test_source_validation_rejects_bad(self, tmp_path, monkeypatch):
        src = tmp_path / "bad.json"
        src.write_text(json.dumps({"metrics": {}}))
        out = tmp_path / "out.json"
        monkeypatch.chdir(ROOT)
        assert main(["--source", str(src), "--output", str(out)]) == 1
        assert not out.exists()

    def test_unknown_internal_model_fails(self, monkeypatch):
        monkeypatch.chdir(ROOT)
        with pytest.raises(ValueError):
            main(["--model", "does_not_exist", "--city", "nyc"])

    def test_leaderboard_regeneration(self, tmp_path, monkeypatch):
        out = tmp_path / "leaderboard.md"
        monkeypatch.chdir(ROOT)
        assert main(["--leaderboard", "--output", str(out)]) == 0
        md = out.read_text(encoding="utf-8")
        assert "Leaderboard" in md
        assert "SIMULATOR" in md
        assert "two_step" in md or "Two-Step" in md


class TestInternalRegistry:
    def test_known_models_have_source_files(self):
        missing = [m for m, spec in INTERNAL_MODELS.items() if not (ROOT / spec["output"]).exists()]
        assert missing == [], f"internal models point at missing artifacts: {missing}"
