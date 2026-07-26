"""Tests for benchmark protocol."""
import json
import os
import tempfile


class TestBenchmarkProtocol:
    """Test benchmark framework utilities."""

    def test_metrics_mae(self):
        """MAE should compute correctly."""
        import numpy as np

        from benchmark.metrics import mae
        y_true = np.array([3, 5, 2, 7])
        y_pred = np.array([4, 4, 3, 6])
        result = mae(y_true, y_pred)
        # |3-4|=1, |5-4|=1, |2-3|=1, |7-6|=1 -> mean = 1.0
        assert abs(result - 1.0) < 1e-6

    def test_metrics_rmse(self):
        """RMSE should compute correctly."""
        import numpy as np

        from benchmark.metrics import rmse
        y_true = np.array([3, 5, 2, 7])
        y_pred = np.array([4, 4, 3, 6])
        result = rmse(y_true, y_pred)
        expected = ((1**2 + 1**2 + 1**2 + 1**2) / 4) ** 0.5
        assert abs(result - expected) < 1e-6

    def test_report_generation(self):
        """Report should include metadata."""
        from benchmark.reports import generate_report
        report = generate_report({"model_a": {"MAE": 1.5}}, "forecast")
        assert report["benchmark"] == "forecast"
        assert report["version"] == "2.0.0"
        assert "timestamp" in report
        assert report["results"]["model_a"]["MAE"] == 1.5

    def test_report_save(self):
        """Report should save to JSON."""
        from benchmark.reports import generate_report, save_report
        report = generate_report({"test": {"acc": 0.9}}, "test")
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        name = tmp.name
        tmp.close()
        try:
            save_report(report, name)
            with open(name) as f:
                loaded = json.load(f)
            assert loaded["benchmark"] == "test"
        finally:
            os.unlink(name)
