"""Check every distributable addon without loading an Odoo database."""
import ast
import csv
import json
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []

class Page(HTMLParser):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'iframe', 'style') or any(k.startswith('on') for k in attrs):
            ERRORS.append(str(self.directory) + ': unsafe HTML')
        if tag == 'img':
            source = attrs.get('src', '')
            if not source or ':' in source or not (self.directory / source).is_file():
                ERRORS.append(str(self.directory) + ': missing/local image ' + source)

entries = json.loads((ROOT / 'module_names.json').read_text())
for entry in entries:
    module = ROOT / entry['technical']
    manifest = ast.literal_eval((module / '__manifest__.py').read_text())
    for condition, message in [
        (len(manifest['name']) <= 25, 'name exceeds 25 characters'),
        (manifest['version'].startswith('14.0.'), 'incorrect series'),
        (manifest.get('installable'), 'not installable'),
        (manifest.get('support'), 'missing support'),
        (manifest.get('license'), 'missing license'),
    ]:
        if not condition:
            ERRORS.append(module.name + ': ' + message)
    for key in ('data', 'demo', 'qweb', 'images'):
        for relative in manifest.get(key, []):
            if not (module / relative).is_file():
                ERRORS.append(module.name + ': missing ' + relative)
    for path in module.rglob('*'):
        if not path.is_file():
            continue
        try:
            if path.suffix == '.py':
                ast.parse(path.read_text(), filename=str(path))
            elif path.suffix == '.xml':
                ET.parse(path)
            if path.suffix in ('.py', '.xml', '.js', '.csv', '.html'):
                content = path.read_text()
                for old in (item['original'] for item in entries):
                    if re.search(r'(?<!\w)' + re.escape(old) + r'(?!\w)', content):
                        ERRORS.append(str(path.relative_to(ROOT)) + ': old namespace ' + old)
        except (SyntaxError, ET.ParseError, UnicodeError) as exc:
            ERRORS.append(str(path.relative_to(ROOT)) + ': ' + str(exc))
    description = module / 'static/description'
    access_path = module / 'security/ir.model.access.csv'
    if access_path.exists():
        with access_path.open() as stream:
            access = list(csv.DictReader(stream))
        if any(not row['group_id:id'] for row in access):
            ERRORS.append(module.name + ': ungrouped model access')
        if len({row['id'] for row in access}) != len(access):
            ERRORS.append(module.name + ': duplicate access identifiers')
    if not (description / 'icon.png').is_file():
        ERRORS.append(module.name + ': missing icon')
    Page(description).feed((description / 'index.html').read_text())
    print(module.name + ': source and packaging checked')
if ERRORS:
    print('\n'.join(ERRORS), file=sys.stderr)
    sys.exit(1)
print('PASS: all 8 manifests, source syntax, XML, assets, descriptions and renamed namespaces')
