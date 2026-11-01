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
# Only standard Odoo 14 Community addons and bundled modules may be required.
# A private/local addon can otherwise pass syntax checks and block the entire
# repository when the Apps scanner resolves dependencies.
COMMUNITY_DEPENDENCIES = {
    'base', 'web', 'mail', 'base_setup', 'account', 'product', 'purchase',
    'sale', 'sale_management', 'sale_crm', 'sale_project', 'sale_timesheet',
    'stock', 'project', 'crm', 'hr', 'hr_timesheet', 'maintenance', 'mrp',
}
bundled = {entry['technical'] for entry in entries}
discovered = {path.parent.name for path in ROOT.glob('*/__manifest__.py')}
if discovered != bundled:
    ERRORS.append('Addon directories differ from module_names.json')
declared_xmlids = set()
for name in bundled:
    addon = ROOT / name
    metadata = ast.literal_eval((addon / '__manifest__.py').read_text())
    for relative in metadata.get('data', []):
        path = addon / relative
        if path.suffix != '.xml' or not path.is_file():
            continue
        try:
            for node in ET.parse(path).iter():
                identifier = node.get('id')
                if identifier and node.tag in ('record', 'template', 'menuitem', 'report'):
                    declared_xmlids.add(identifier if '.' in identifier else name + '.' + identifier)
        except ET.ParseError:
            pass  # The source checks below report the syntax error.
for entry in entries:
    module = ROOT / entry['technical']
    manifest = ast.literal_eval((module / '__manifest__.py').read_text())
    for dependency in manifest.get('depends', []):
        if dependency not in bundled | COMMUNITY_DEPENDENCIES:
            ERRORS.append(module.name + ': unavailable dependency ' + dependency)
        if dependency == module.name:
            ERRORS.append(module.name + ': depends on itself')
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
                tree = ET.parse(path)
                if str(path.relative_to(module)) in manifest.get('data', []):
                    for node in tree.iter('field'):
                        if node.get('name') == 'report_name' and node.text:
                            template = node.text.strip()
                            if template.split('.')[0] in bundled and template not in declared_xmlids:
                                ERRORS.append(str(path.relative_to(ROOT)) + ': missing report template ' + template)
                        reference = node.get('ref')
                        if node.get('name') != 'inherit_id' or not reference:
                            continue
                        reference = reference if '.' in reference else module.name + '.' + reference
                        if reference.split('.')[0] in bundled and reference not in declared_xmlids:
                            ERRORS.append(str(path.relative_to(ROOT)) + ': missing inherited view ' + reference)
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
print('PASS: all 8 manifests, dependencies, source syntax, XML, assets, descriptions and renamed namespaces')
