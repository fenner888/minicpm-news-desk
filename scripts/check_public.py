"""Offline export, local-link and dependency checks; no installs or network."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
expected=set(json.loads((root/'EXPORT-ALLOWLIST.json').read_text())['files'])
listed=subprocess.check_output(['git','-C',str(root),'ls-files','--cached','--others','--exclude-standard']).decode().splitlines()
actual=set(listed)
errors=[]
if expected!=actual:errors.append({'export_missing':sorted(expected-actual),'export_unexpected':sorted(actual-expected)})
for name in sorted(expected):
    path=root/name
    if not path.is_file():continue
    if name.endswith('.md'):
        for target in re.findall(r'\]\(([^\s)]+)',path.read_text()):
            if '://' in target or target.startswith(('#','mailto:')):continue
            dest=target.split('#')[0]
            if dest and not (path.parent/dest).exists():errors.append({'broken_link':name,'target':target})
    if name.endswith('.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            imports=[]
            if isinstance(node,ast.Import):imports=[a.name.split('.')[0] for a in node.names]
            elif isinstance(node,ast.ImportFrom) and not node.level and node.module:imports=[node.module.split('.')[0]]
            for module in imports:
                if module not in sys.stdlib_module_names and module!='newsdesk':errors.append({'external_import':name,'module':module})
    if name.endswith(('.py','.md','.json','.yml')):
        raw=path.read_bytes()
        for pattern in [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b',rb'\bAKIA[A-Z0-9]{16}\b',rb'\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}\b']:
            if re.search(pattern,raw):errors.append({'secret_pattern':name})
print(json.dumps({'checked_files':len(expected),'errors':errors},indent=2))
raise SystemExit(bool(errors))
