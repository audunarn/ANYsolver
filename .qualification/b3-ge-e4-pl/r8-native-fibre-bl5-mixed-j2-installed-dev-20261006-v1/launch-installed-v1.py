from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
remaining=347.54534339986276-json.loads((ROOT/'build-resource-receipt-v1.json').read_text())['elapsed_seconds'];reserve=40.;limit=min(240.,remaining-reserve)
assert limit>0
(ROOT/'installed-budget-v1.json').write_text(json.dumps(dict(inherited_remaining_seconds=347.54534339986276,build_seconds=347.54534339986276-remaining,remaining_before_test_seconds=remaining,installed_limit_seconds=limit,reserve_seconds=reserve),indent=2)+'\n')
previous=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-released-reference-dev-20261005-v1/original-supervisor.py';function=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-weak-continuum-dev-20261006-v1/supervisor-function-v3.py'
spec=importlib.util.spec_from_file_location('bounded',previous);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);s.ROOT=ROOT;s.ENV=os.environ.copy()
for n in ('PYTHONOPTIMIZE','OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES'):s.ENV.pop(n,None)
s.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',INSTALLED_PROCESS_CAP=str(limit))
s.ENV['PYTHONPATH']=os.pathsep.join((str(ROOT/'installed-host-v1'),str(REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'),str(ROOT/'check-stage-v1')))
exec(compile(function.read_text().replace('> 600:', '> '+repr(limit)+':').replace('seconds_limit=600,','seconds_limit='+repr(limit)+','),str(function),'exec'),s.__dict__)
WMI=Path('C:/Python/Python314/DLLs/_wmi.pyd').resolve();original=s.threads

def classified(proc):
    records=original(proc)
    for row in records:
        row['original_numeric_or_unresolved']=row['numeric_or_unresolved'];row['exact_WMI_support']=row['query_status']==0 and row['start_module'] is not None and Path(row['start_module']).resolve()==WMI
        if row['exact_WMI_support']:row['numeric_or_unresolved']=False
    return records
s.threads=classified
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
(ROOT/'runner-freeze-v1.json').write_text(json.dumps(dict(files={p.name:sha(p) for p in (ROOT/'build-entry-v1.py',ROOT/'launch-build-v1.py',ROOT/'installed-entry-v1.py',ROOT/'launch-installed-v1.py')},supervisor_sha256=sha(previous),supervisor_function_sha256=sha(function),wmi_sha256=sha(WMI)),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'installed-entry-v1.py')],'installed-job-v1',2*1024**3)
