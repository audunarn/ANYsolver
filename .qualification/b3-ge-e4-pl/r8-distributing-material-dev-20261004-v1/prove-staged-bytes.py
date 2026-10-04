from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
FEM=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
records=[]
for repo in (REPO,FEM):
    git=['git','-c','safe.directory='+str(repo)]
    paths=subprocess.check_output(git+['diff','--cached','--name-only'],cwd=repo,text=True).splitlines()
    checked={};normalized=[]
    for path in paths:
        if path=='.gitattributes' or (repo==REPO and path.startswith('docs/')):
            normalized.append(path);continue
        blob=subprocess.check_output(git+['show',':'+path],cwd=repo)
        assert blob==(repo/path).read_bytes(),path
        checked[path]=hashlib.sha256(blob).hexdigest()
    records.append(dict(repo=str(repo),exact_bytes=checked,intentional_text_normalization=normalized))
(ROOT/'staged-byte-proof.json').open('x',encoding='utf-8').write(json.dumps(records,indent=2)+'\n')
print(json.dumps([dict(repo=r['repo'],checked=len(r['exact_bytes']),normalized=len(r['intentional_text_normalization'])) for r in records]))
