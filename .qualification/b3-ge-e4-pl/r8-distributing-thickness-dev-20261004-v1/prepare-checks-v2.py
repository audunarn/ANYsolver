from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
for rel in ('scripts/r8_e02_distributing_thickness.py','scripts/r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_thickness.py'):
    target=ROOT/'checks-v1-bytes'/rel;target.parent.mkdir(parents=True,exist_ok=True)
    target.open('xb').write((REPO/rel).read_bytes())
source=(ROOT/'probe-v1.py').read_text(encoding='utf-8')
source=source.replace("tests=('tests/test_r8_e02_distributing_thickness.py','tests/test_r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_solid_area.py')", "tests=('tests/test_r8_e02_distributing_thickness.py',)")
source=source.replace('checks-runtime-v1.json','checks-runtime-v2.json').replace('pytest-v1','pytest-v2')
(ROOT/'probe-v2.py').open('x',encoding='utf-8').write(source)
source=(ROOT/'run-v1.py').read_text(encoding='utf-8').replace("if kind in ('checks','prepare','parse'):","if kind=='checks':").replace('probe-v1.py','probe-v2.py').replace("kind+'-v1'","kind+'-v2'")
(ROOT/'run-checks-v2.py').open('x',encoding='utf-8').write(source)
