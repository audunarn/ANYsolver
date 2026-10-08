from pathlib import Path
import importlib.util,json,hashlib
p=Path.home()/'AppData/Local/Temp/r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('supervisor',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=Path(__file__).resolve().parent
m.ENV.update(NUMEXPR_NUM_THREADS='1',CCX_NPROC_RESULTS='1',CCX_NPROC_EQUATION_SOLVER='1',NUMBER_OF_CPUS='1')
m.ENV['PYTHONPATH']=str(m.REPO/'src')
script=m.REPO/'scripts/r8_e04_ccx_restricted_membrane.py'
(m.ROOT/'executed-script-v5.py').write_bytes(script.read_bytes())
(m.ROOT/'executed-tests-v5.py').write_bytes((m.REPO/'tests/test_stiffened_shell_e04_ccx_restricted_membrane.py').read_bytes())
(m.ROOT/'artifact-v5.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),kind='focused-tests-and-offline-existing-failure-only'),indent=2))
m.supervise(['C:/Python/Python314/python.exe','-m','pytest',str(m.REPO/'tests/test_stiffened_shell_e04_ccx_restricted_membrane.py'),'-q','-p','no:cacheprovider','--basetemp',str(m.ROOT/'pytest-temp-v5')],'focused-source-v5',2*1024**3)
spec=importlib.util.spec_from_file_location('ccx_failure_parser',script)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
for version in (3,4):
 source=m.ROOT/f'full-v{version}'
 summary=a.failed_iteration_summary((source/'reference.cvg').read_text(),(source/'reference.sta').read_text(),a.ITERATION_DIAGNOSTIC_CONTROLS if version==4 else None)
 summary['source_sha256']={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('reference.cvg','reference.sta','status.json')}
 summary['parser_sha256']=hashlib.sha256(script.read_bytes()).hexdigest()
 summary['kind']='OFFLINE_FAILED_RUN_DIAGNOSTIC_ONLY'
 a.save(m.ROOT/f'failed-iteration-analysis-v{version}-parser-v5.json',summary)
 print(json.dumps(dict(version=version,observed_max_iteration=summary['observed_max_iteration'],budget_exceeded=summary['budget_exceeded'],accepted_steps=summary['accepted_steps'])))