from pathlib import Path
import hashlib,json,shutil,subprocess,sys
T=Path(__file__).resolve().parent
R=T/'r8-bl5-consumer-installed-v1'
W=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
S=T/'r8-bl5-finite-installed-v3'
R.mkdir();B=R/'build-source';B.mkdir()
for p in W.iterdir():
    if p.is_file() and p.name in ('pyproject.toml','setup.py','setup.cfg','README.md','LICENSE','MANIFEST.in'):
        shutil.copy2(p,B/p.name)
shutil.copytree(W/'src',B/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
(R/'tests').mkdir();shutil.copy2(W/'tests/test_experimental_stiffened_shell_consumer.py',R/'tests/test_experimental_stiffened_shell_consumer.py')
for name in ('pytest.ini','run_bounded.py'):shutil.copy2(S/name,R/name)
(R/'wheels').mkdir();shutil.copy2(next((S/'wheels').glob('anysolver-*.whl')),R/'wheels/anysolver-0.4.7-py3-none-any.whl')
with (R/'build.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','wheel','--no-cache-dir','--no-build-isolation','--no-deps','--wheel-dir',str(R/'wheels'),str(B)],stdout=log,stderr=subprocess.STDOUT,check=True)
with (R/'install.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','--no-deps','--no-compile','--target',str(R/'site')]+[str(p) for p in (R/'wheels').glob('*.whl')],stdout=log,stderr=subprocess.STDOUT,check=True)
runner=(S/'run_installed.py').read_text()
start=runner.index('selected=');end=runner.index('# Cross-version restoration') if '# Cross-version restoration' in runner else runner.index('# Cross-version restoration') if False else runner.index('# Cross-version')
runner=runner[:start]+'''selected=[root/'tests/test_experimental_stiffened_shell_consumer.py']
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--junitxml',str(root/'inventory.xml'),
    '--basetemp',str(root/'pytest-tmp')]+[str(p) for p in selected])
assert code==0,code
import xml.etree.ElementTree as ET
suites=ET.parse(root/'inventory.xml').getroot().findall('testsuite')
assert all(int(s.attrib['failures'])==int(s.attrib['errors'])==int(s.attrib['skipped'])==0 for s in suites)
'''+runner[runner.index('loaded='):]
old="Path("+repr(str(T/'r8-bl5-finite-installed-v2/site/anyfem'))+")"
runner=runner.replace(old,"Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src/anyfem')")
runner=runner.replace(",'history_examples':len(reports)"," ,'consumer_tests':sum(int(s.attrib['tests']) for s in suites)")
(R/'run_installed.py').write_text(runner)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={p.relative_to(R).as_posix():sha(p) for p in (R/'tests').glob('*.py')}
for name in ('run_installed.py','run_bounded.py','pytest.ini'):inputs[name]=sha(R/name)
manifest={'classification':'explicit experimental BL5 consumer integration; not native-project or G2 acceptance','solver_product':'2d9ab38dd4037eda5ad808ffe6e4eb000b326970','consumer_source':'527a48da plus separate BL5 schema extension','inputs':inputs,'wheels':{p.name:sha(p) for p in (R/'wheels').glob('*.whl')}}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True))
print(json.dumps({'root':str(R),'wheels':manifest['wheels'],'inputs':len(inputs)}))
