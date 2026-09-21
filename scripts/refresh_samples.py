"""Regenerate only the public fictional daily fixture, never real source data."""
from pathlib import Path
import shutil
import sys
import tempfile
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from newsdesk.digest import demo

with tempfile.TemporaryDirectory(prefix='newsdesk-sample-') as temporary:
    out=Path(temporary)/'demo'
    demo(out)
    for name in ('part-1.md','supporting-report.html','preview.html','manifest.json'):
        shutil.copyfile(out/name,root/'samples'/'daily-recap'/name)
print('Refreshed fictional daily sample; zero model calls or sends.')
