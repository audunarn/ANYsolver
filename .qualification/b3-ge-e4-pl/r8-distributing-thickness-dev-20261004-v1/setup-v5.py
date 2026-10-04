from pathlib import Path
ROOT=Path(__file__).resolve().parent
run=(ROOT/'run-v4.py').read_text(encoding='utf-8').replace('probe-v4','probe-v5').replace('binding-v4','binding-v5').replace("kind+'-v4'","kind+'-v5'").replace("'ccx-'+name+'-v1'","'ccx-'+name+'-v5'")
run=run.replace("if kind=='parse':", "if kind in ('checks','prepare'):\n command=[sys.executable,'-u',str(ROOT/'probe-v5.py'),kind]\nelif kind=='parse':")
probe=(ROOT/'probe-v4.py').read_text(encoding='utf-8').replace('binding-v4','binding-v5').replace('execution-v4','execution-v5').replace('parsed-v4','parsed-v5').replace('comparison-v4','comparison-v5').replace("'ccx-'+name+'-v1'","'ccx-'+name+'-v5'").replace('checks-runtime-v1','checks-runtime-v5').replace('pytest-v1','pytest-v5')
probe=probe.replace("tests=('tests/test_r8_e02_distributing_thickness.py','tests/test_r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_solid_area.py')", "tests=('tests/test_r8_e02_distributing_thickness.py',)")
probe=probe.replace(" binding=dict(scope=", " prior=OLD/'paired-comparison-v1.json'\n assert sha(prior)=='cf6f6c62339ca37008c7ce82fd59fd2d2c1c9ab6b3cff7dd10b165cbd56917b7'\n binding=dict(prior_comparison=str(prior),prior_comparison_sha256=sha(prior),drivers={n:sha(ROOT/n) for n in ('run-v5.py','probe-v5.py')},scope=")
for name,text in [('run-v5.py',run),('probe-v5.py',probe)]:
 compile(text,name,'exec');(ROOT/name).open('x',encoding='utf-8',newline='').write(text)
print('Fresh v5 syntax/control/prepare/execution/parse; prior failed v4 untouched')
