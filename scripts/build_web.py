# -*- coding: utf-8 -*-
"""Build self-contained web/index.html from source files."""
import re, json
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / 'web'

def build():
    css = (WEB / 'css' / 'style.css').read_text(encoding='utf-8')
    main_js = (WEB / 'js' / 'main.js').read_text(encoding='utf-8')
    map_js = (WEB / 'js' / 'map.js').read_text(encoding='utf-8')
    sim_js = (WEB / 'js' / 'simulation.js').read_text(encoding='utf-8')
    charts_js = (WEB / 'js' / 'charts.js').read_text(encoding='utf-8')
    zones_data = json.loads((WEB / 'data' / 'zones.json').read_text(encoding='utf-8'))
    zones_json_str = json.dumps(zones_data)

    main_js_modified = re.sub(
        r'loadZones: function\(\) \{\s+return fetch\("data/zones.json"\).*?\]\s*;\s*\n\s*\}\);\s*\n\s*\},\n',
        'loadZones: function() { return new Promise(function(r){ r(); }); },\n',
        main_js, flags=re.DOTALL
    )
    main_js_modified = re.sub(r'^var AppState = \{.*?\};\s*$', '', main_js_modified, flags=re.MULTILINE)

    inlined_js = '// === Inlined build ===\nvar AppState = { zones: ' + zones_json_str + '["zones"], selectedZone: null };\n\n' + main_js_modified + '\n\n' + map_js + '\n\n' + sim_js + '\n\n' + charts_js

    if inlined_js.count('{') != inlined_js.count('}') or inlined_js.count('(') != inlined_js.count(')'):
        raise SystemExit('Brace/paren mismatch in inlined JS')

    html = (WEB / 'index.html').read_text(encoding='utf-8')
    html = re.sub(r'<link rel="stylesheet" href="css/style\.css" />', '<style>' + css + '</style>', html)
    for name in ['main', 'map', 'simulation', 'charts']:
        html = re.sub(r'<script src="js/' + re.escape(name) + r'\.js"></script>\s*', '', html)
    html = html.replace('</body>', '<script>' + inlined_js + '</script>\n</body>')
    html = re.sub(r'<div id="mapLoading"[^>]*>Loading NYC zone map...</div>\s*', '', html)
    html = re.sub(r'<script>document\.addEventListener\("DOMContentLoaded".*?mapLoading.*?</script>\s*', '', html)

    (WEB / 'index.html').write_text(html, encoding='utf-8')
    print(f'OK: {len(html.encode("utf-8"))} bytes')

if __name__ == '__main__':
    build()
