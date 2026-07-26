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
        assert "map.js" in content, "index.html must include map.js"
        js_content = _read_utf8(WEB_DIR / "js" / "map.js")
        assert "createElementNS" in js_content, "map.js must use SVG"

    def test_index_html_has_disclaimer(self):
        content = _read_utf8(WEB_DIR / "index.html")
        assert "simulation" in content.lower(), "Must have simulation disclaimer"

    def test_all_js_referenced_in_html(self):
        html_content = _read_utf8(WEB_DIR / "index.html")
        js_files = ["main.js", "map.js", "simulation.js", "charts.js"]
        for js in js_files:
            assert js in html_content, f"{js} must be referenced in index.html"

    def test_css_referenced_in_html(self):
        html_content = _read_utf8(WEB_DIR / "index.html")
        assert "style.css" in html_content, "style.css must be referenced in index.html"

