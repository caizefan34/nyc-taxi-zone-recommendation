# -*- coding: utf-8 -*-
"""Build self-contained web/index.html from source files."""
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / 'web'


def build():
    leaflet_css = (WEB / 'css' / 'leaflet.css').read_text(encoding='utf-8')
    leaflet_js = (WEB / 'js' / 'leaflet.min.js').read_text(encoding='utf-8')
    css = (WEB / 'css' / 'style.css').read_text(encoding='utf-8')
    map_js = (WEB / 'js' / 'map.js').read_text(encoding='utf-8')
    main_js = (WEB / 'js' / 'main.js').read_text(encoding='utf-8')
    sim_js = (WEB / 'js' / 'simulation.js').read_text(encoding='utf-8')
    charts_js = (WEB / 'js' / 'charts.js').read_text(encoding='utf-8')
    zones_data = json.loads(
        (WEB / 'data' / 'zones.json').read_text(encoding='utf-8')
    )
    zones_json_str = json.dumps(zones_data)

    main_js_modified = re.sub(
        r'loadZones: function\(\) \{\s+return fetch\("data/zones.json"\).*?'
        r'\]\s*;\s*\n\s*\}\);\s*\n\s*\},\n',
        'loadZones: function() { return new Promise(function(r){ r(); }); },\n',
        main_js,
        flags=re.DOTALL,
    )
    main_js_modified = re.sub(
        r'^var AppState = \{.*?\};\s*$', '', main_js_modified, flags=re.MULTILINE
    )

    inlined_js = (
        '// === Inlined build ===\n'
        'var AppState = { zones: ' + zones_json_str + '["zones"],'
        ' selectedZone: null };\n\n'
        + main_js_modified + '\n\n'
        + map_js + '\n\n'
        + sim_js + '\n\n'
        + charts_js
    )
    assert inlined_js.count('{') == inlined_js.count('}'), 'Brace mismatch'
    assert inlined_js.count('(') == inlined_js.count(')'), 'Paren mismatch'

    full_js = leaflet_js + ';\n' + inlined_js

    html = (WEB / 'index.html').read_text(encoding='utf-8')
    full_css = leaflet_css + '\n' + css
    html = re.sub(
        r'<link rel="stylesheet" href="css/style\.css" />',
        '<style>' + full_css + '</style>',
        html,
    )
    for name in ('main', 'map', 'simulation', 'charts'):
        html = re.sub(
            r'<script src="js/' + re.escape(name) + r'\.js"></script>\s*',
            '',
            html,
        )
    html = html.replace(
        '</body>', '<script>' + full_js + '</script>\n</body>'
    )
    html = re.sub(
        r'<div id="mapLoading"[^>]*>Loading NYC zone map...</div>\s*', '', html
    )
    html = re.sub(
        r'<script>document\.addEventListener\("DOMContentLoaded".*?mapLoading.*?</script>\s*',
        '',
        html,
    )
    html = html.replace(
        '<img src="../release_dashboard.png"'
        ' alt="Release Dashboard"'
        " onerror=\"this.style.display='none'\" />",
        '',
    )

    (WEB / 'index.html').write_text(html, encoding='utf-8')
    print(f'OK: {len(html.encode("utf-8"))} bytes')


if __name__ == '__main__':
    build()
