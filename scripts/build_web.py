# -*- coding: utf-8 -*-
"""Build self-contained web/index.html from source files."""
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / 'web'


def build():
    css = (WEB / 'css' / 'style.css').read_text(encoding='utf-8')
    main_js = (WEB / 'js' / 'main.js').read_text(encoding='utf-8')
    map_js = (WEB / 'js' / 'map.js').read_text(encoding='utf-8')
    sim_js = (WEB / 'js' / 'simulation.js').read_text(encoding='utf-8')
    charts_js = (WEB / 'js' / 'charts.js').read_text(encoding='utf-8')
    zones_data = json.loads(
        (WEB / 'data' / 'zones.json').read_text(encoding='utf-8')
    )
    zones_json_str = json.dumps(zones_data)

    # Replace whole loadZones function body with synchronous version
    main_js_modified = re.sub(
        r'loadZones: function\(\) \{\s+return fetch\("data/zones.json"\).*?'
        r'\]\s*;\s*\n\s*\}\);\s*\n\s*\},\n',
        'loadZones: function() { return new Promise(function(r){ r(); }); },\n',
        main_js,
        flags=re.DOTALL,
    )
    # Remove original AppState declaration
    main_js_modified = re.sub(
        r'^var AppState = \{.*?\};\s*$',
        '',
        main_js_modified,
        flags=re.MULTILINE,
    )

    # Build inlined JS with AppState pre-populated
    inlined_js = (
        '// === Inlined build ===\n'
        'var AppState = { zones: ' + zones_json_str + '["zones"],'
        ' selectedZone: null };\n\n'
        + main_js_modified + '\n\n'
        + map_js + '\n\n'
        + sim_js + '\n\n'
        + charts_js
    )

    # Verify brace/paren balance
    if inlined_js.count('{') != inlined_js.count('}'):
        raise SystemExit('Brace mismatch in inlined JS')
    if inlined_js.count('(') != inlined_js.count(')'):
        raise SystemExit('Paren mismatch in inlined JS')

    # Build HTML
    html = (WEB / 'index.html').read_text(encoding='utf-8')
    html = re.sub(
        r'<link rel="stylesheet" href="css/style\.css" />',
        '<style>' + css + '</style>',
        html,
    )
    for name in ('main', 'map', 'simulation', 'charts'):
        html = re.sub(
            r'<script src="js/' + re.escape(name) + r'\.js"></script>\s*',
            '',
            html,
        )
    html = html.replace(
        '</body>', '<script>' + inlined_js + '</script>\n</body>'
    )
    html = re.sub(
        r'<div id="mapLoading"[^>]*>Loading NYC zone map...</div>\s*',
        '',
        html,
    )
    html = re.sub(
        r'<script>document\.addEventListener\("DOMContentLoaded".*?mapLoading.*?</script>\s*',
        '',
        html,
    )
    # Remove dead image reference (doesn't exist in repo)
    html = html.replace(
        '<img src="../release_dashboard.png" alt="Release Dashboard"'
        ' onerror="this.style.display=\'none\'" />',
        '',
    )

    (WEB / 'index.html').write_text(html, encoding='utf-8')
    print(f'OK: {len(html.encode("utf-8"))} bytes')


if __name__ == '__main__':
    build()
