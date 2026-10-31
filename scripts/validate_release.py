"""Validate distributable Odoo addon files without importing Odoo."""
import ast
import csv
from html.parser import HTMLParser
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'cpabooks_chart_of_accounts'
errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


class StorePage(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        check(tag not in ('script', 'iframe', 'style'), 'Forbidden store HTML tag: ' + tag)
        for key, value in attrs.items():
            check(not key.startswith('on'), 'Inline HTML event handler')
            if key in ('href', 'src'):
                if value.startswith('mailto:') and key == 'href':
                    continue
                check(':' not in value and not value.startswith('//'), 'External store asset/link: ' + value)
                if not value.startswith('#'):
                    check((MODULE / 'static/description' / value).is_file(), 'Missing store asset: ' + value)


manifest = ast.literal_eval((MODULE / '__manifest__.py').read_text())
check(len(manifest['name']) <= 25, 'App name exceeds 25 characters')
check(manifest['version'].startswith('14.0.'), 'Wrong Odoo version')
check(manifest['license'] == 'LGPL-3', 'Unexpected license')
check(manifest['installable'], 'Module must be installable')
check('@' in manifest['support'], 'Missing support email')
for path in manifest['data'] + manifest.get('images', []):
    check((MODULE / path).is_file(), 'Missing manifest file: ' + path)
for path in MODULE.rglob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
for path in MODULE.rglob('*.xml'):
    ET.parse(path)
with (MODULE / 'security/ir.model.access.csv').open() as stream:
    access = list(csv.DictReader(stream))
check(all(row['group_id:id'] for row in access), 'Ungrouped model access')
check(len({row['id'] for row in access}) == len(access), 'Duplicate ACL IDs')
StorePage().feed((MODULE / 'static/description/index.html').read_text())
check((MODULE / 'static/description/icon.png').is_file(), 'Missing icon')
check((ROOT / 'LICENSE').is_file() and (ROOT / 'LICENSE.LESSER').is_file(), 'Missing license texts')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print('PASS: manifest, Python syntax, XML, ACL groups, store HTML, assets and licenses')
