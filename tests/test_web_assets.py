"""Tests for web/ interactive platform assets."""
import json
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


def _read_utf8(path):
    """Read a file with UTF-8 encoding (handles Windows default codec issue)."""
    return path.read_text(encoding="utf-8")


class TestWebAssets:
    """Test that all required web files exist and are valid."""

    def test_index_html_exists(self):
        assert (WEB_DIR / "index.html").exists(), "index.html is required"

    def test_css_exists(self):
        assert (WEB_DIR / "css" / "style.css").exists(), "style.css is required"

    def test_js_files_exist(self):
        required_js = ["main.js", "map.js", "simulation.js", "charts.js"]
        for js in required_js:
            assert (WEB_DIR / "js" / js).exists(), f"{js} is required"

    def test_zones_json_exists(self):
        assert (WEB_DIR / "data" / "zones.json").exists(), "zones.json is required"

    def test_zones_json_valid(self):
        with open(WEB_DIR / "data" / "zones.json") as f:
            data = json.load(f)
        assert "zones" in data, "zones.json must have zones key"
        assert len(data["zones"]) > 0, "zones.json must have at least one zone"
        for zone in data["zones"]:
            assert "id" in zone
            assert "name" in zone
            assert "lat" in zone
            assert "lng" in zone

    def test_index_html_has_svg_map(self):
        content = _read_utf8(WEB_DIR / "index.html")
        assert "MapModule" in content, "index.html must include MapModule"
        assert "createElementNS" in content, "index.html must use SVG"

    def test_index_html_has_disclaimer(self):
        content = _read_utf8(WEB_DIR / "index.html")
        assert "simulation" in content.lower(), "Must have simulation disclaimer"

    def test_all_js_merged_in_html(self):
        html_content = _read_utf8(WEB_DIR / "index.html")
        assert "AppState" in html_content, "index.html must contain AppState"
        assert "MapModule" in html_content, "index.html must contain MapModule"
        assert "SimulationModule" in html_content, "index.html must contain SimulationModule"
        assert "ChartsModule" in html_content, "index.html must contain ChartsModule"

    def test_css_inlined_in_html(self):
        html_content = _read_utf8(WEB_DIR / "index.html")
        assert "<style>" in html_content, "CSS must be inlined in index.html"
        assert "unpkg.com" not in html_content, "No unpkg CDN dependencies"

