from pathlib import Path
import hashlib,json,shutil,zipfile

w=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling').resolve()
temp=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp')
dest=w/'.qualification/b3-ge-e4-pl/r8-b2-integrity-ge-support-dev-20260930-v1'
assert dest.resolve().is_relative_to(w)
dest.mkdir(exist_ok=False)
(dest/'wheels').mkdir()
(dest/'.gitattributes').write_text('* -text\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
wheel_catalog={}; archives={}
for version in range(1,8):
    source=temp/f'r8-b2-point-integrity-installed-v{version}'
    out=dest/source.name;out.mkdir()
    for p in source.iterdir():
        if p.is_file():shutil.copy2(p,out/p.name)
    roots=[p for p in ('tests','scripts','consumer-tests','build-source') if (source/p).exists()]
    members={}
    with zipfile.ZipFile(out/'input-snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in roots:
            for p in sorted((source/name).rglob('*')):
                if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
                if name=='build-source' and ('build' in p.relative_to(source/name).parts or any(s.endswith('.egg-info') for s in p.parts)):continue
                relative=p.relative_to(source).as_posix()
                z.write(p,relative);members[relative]=sha(p)
    with zipfile.ZipFile(out/'input-snapshot.zip') as z:
        assert all(hashlib.sha256(z.read(name)).hexdigest()==h for name,h in members.items())
    (out/'input-members.json').write_text(json.dumps(members,indent=2)+'\n')
    archives[source.name]={'sha256':sha(out/'input-snapshot.zip'),'members':len(members)}
    for p in (source/'wheels').glob('*.whl'):
        h=sha(p);target=dest/'wheels'/f'{h}-{p.name}'
        if not target.exists():shutil.copy2(p,target)
        assert sha(target)==h
        wheel_catalog.setdefault(h,{'filename':target.name,'versions':[]})['versions'].append(version)
shutil.copy2(temp/'r8-b2-integrity-active-before-resume.md',dest/'active-note-before-resume.md')
shutil.copy2(temp/'r8_prepare_point_precision.py',dest/'prepare-installed-v7.py')
shutil.copy2(Path(__file__),dest/'archive.py')
manifest={'kind':'Level-A integrated correctness and supported-reference check; not a qualification execution',
 'base_head':'e60d220e10c171e83141d0df0433a1149ae02f7d','anyfem_head':'7cf1fd7ecec14ab16dab3ffb26bf4182c807af0c',
 'prospective_question':'One own-factor compensated correction removes binary64 support-role precision loss or exact equivalence stays withheld; no further numerical tuning.',
 'unchanged_criteria':{'support_role_relative':1e-10,'ge_equilibrium':1e-8,'ge_scaled_constraint':1e-9},
 'threads':1,'jit_disabled':True,'resource_limit_seconds':600,'resource_limit_bytes':8589934592,
 'f03_consumed':False,'foreign_script_sha256':'c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481',
 'numerical_command':['C:/Python/Python314/python.exe','-u','run_bounded.py'],
 'archives':archives,'wheels':wheel_catalog,
 'reconstruction':'Raw top-level run records and byte-verified input snapshots retain every version. Wheels reconstruct installed sites; v7 binds all source/wheel/site modules and actual imports.'}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'path':str(dest),'wheels':len(wheel_catalog),'files':sum(1 for p in dest.rglob('*') if p.is_file())}))
