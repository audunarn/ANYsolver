"""Preserve scoped source/runtime evidence; never stage installed caches."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
# Recover only explicitly recorded portable-run roots, not a temporary catalog.
records=[]
for log in ROOT.glob('*.log'):
    text=log.read_text(encoding='utf-8-sig',errors='replace')
    match=re.search(r'record=([^\r\n]+)',text)
    if match:
        origin=Path(match[1]);destination=ROOT/('portable-'+log.stem)
        destination.mkdir(exist_ok=False)
        for name in ('selection.json','runtime.json','resource.json'):
            source=origin/name
            if source.is_file():(destination/name).write_bytes(source.read_bytes())
        records.append(dict(log=log.name,origin=str(origin),copied=[p.name for p in destination.iterdir()]))
record=dict(scope='development integration only',portable_records=records,
    final=dict(tests=131,example='PASS',route_seconds=141.90342330001295,
        sampled_peak_tree_bytes=211599360,failed_continuation='1.01: preserved v7/v9'),
    archive_limit='intermediate sources not all byte archived; final and v7 source snapshots are exact',
    local_artifact_limit='site and wheel bytes retained locally, hashes archived; caches not staged')
(ROOT/'delivery-inventory.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
files=[]
for entry in ROOT.iterdir():
    if entry.is_file():files.append(entry)
    elif entry.name.startswith(('source-','consumer-','run-','diagnosis-','replay-','installed-','portable-')):
        files.extend(p for p in entry.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths=sorted(str(p.relative_to(REPO)).replace('\\','/') for p in files)
(ROOT/'stage-paths.txt').open('x',encoding='utf-8').write('\n'.join(paths)+'\n')
print(json.dumps(dict(files=len(paths),bytes=sum((REPO/p).stat().st_size for p in paths))))
