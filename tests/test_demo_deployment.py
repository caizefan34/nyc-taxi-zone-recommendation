"""Tests for demo deployment readiness."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_requirements_demo_exists():
    assert (REPO_ROOT / "requirements-demo.txt").exists()


def test_readme_demo_exists():
    assert (REPO_ROOT / "README_demo.md").exists()


def test_dockerfile_demo_exists():
    assert (REPO_ROOT / "Dockerfile.demo").exists()


def test_web_index_exists():
    assert (REPO_ROOT / "web" / "index.html").exists()


def test_app_streamlit_exists():
    assert (REPO_ROOT / "app" / "app.py").exists()
