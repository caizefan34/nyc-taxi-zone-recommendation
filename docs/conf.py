"""Sphinx documentation configuration."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Urban Mobility Decision Intelligence"
author = "Zefan Cai"
copyright = f"2026, {author}"
release = "3.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx_rtd_theme",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# ~83 process/audit/release docs are intentionally not in any toctree (they
# would clutter the sidebar). They still build and stay reachable by URL.
# Suppress only toc.not_included so -W keeps catching real defects (xref,
# highlighting, image) while allowing these archived docs to exist.
suppress_warnings = ["toc.not_included"]
html_static_path = ["_static"]
html_extra_path = ["../assets"]

html_theme = "sphinx_rtd_theme"
html_title = f"{project} v{release}"
html_favicon = "../assets/favicon.ico" if os.path.exists("../assets/favicon.ico") else None
html_css_files = ["showcase.css"]
html_theme_options = {
    "style_external_links": True,
    "navigation_depth": 3,
    "collapse_navigation": False,
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# MathJax
mathjax3_config = {
    "tex": {
        "inlineMath": [["$", "$"], ["\\(", "\\)"]],
        "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
    }
}

myst_enable_extensions = ["dollarmath", "amsmath"]
