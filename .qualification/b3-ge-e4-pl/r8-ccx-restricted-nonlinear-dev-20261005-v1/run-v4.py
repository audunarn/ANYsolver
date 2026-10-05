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
exe=Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
(m.ROOT/'executed-script-v4.py').write_bytes(script.read_bytes())
(m.ROOT/'executed-tests-v4.py').write_bytes((m.REPO/'tests/test_stiffened_shell_e04_ccx_restricted_membrane.py').read_bytes())
(m.ROOT/'artifact-v4.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest()),indent=2))
m.supervise(['C:/Python/Python314/python.exe','-m','pytest',str(m.REPO/'tests/test_stiffened_shell_e04_ccx_restricted_membrane.py'),'-q','-p','no:cacheprovider','--basetemp',str(m.ROOT/'pytest-temp-v4')],'focused-source-v4',2*1024**3)
command=['C:/Python/Python314/python.exe',str(script),'--mode','full','--iteration-diagnostic','--exe',str(exe),'--output',str(m.ROOT/'full-v4'),'--native-input',str(m.REPO/'.qualification/b3-ge-e4-pl/r8-restricted-nonlinear-reference-dev-20261005-v1/native-screen-v3/native.json'),'--spring-control-json',str(m.ROOT/'spring-control-v3/status.json'),'--shell-control-json',str(m.ROOT/'shell-control-v3/status.json')]
m.supervise(command,'full-execution-v4',2*1024**3)