from pathlib import Path
from hashlib import sha256
import importlib.metadata,json,os,sys,time,traceback
import numpy,scipy,numba,llvmlite,psutil,anysolver
from threadpoolctl import threadpool_info
RAW=Path(__file__).resolve().parent;REPO=RAW.parents[2];TARGET=RAW/'installed-host-v1';CHECKS=RAW/'example-stage-v3'
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v3'
ART=json.loads((RAW/'artifact-provenance-v1.json').read_text());INPUT=json.loads((RAW/'example-input-binding-v3.json').read_text())
STARTED=time.monotonic();CAP=float(os.environ['INSTALLED_PROCESS_CAP']);SYS_PATH_INITIAL=list(sys.path)
sys.path.insert(0,str(CHECKS))
for n,d in INPUT['files'].items():assert sha256((CHECKS/n).read_bytes()).hexdigest()==sha256((REPO/n).read_bytes()).hexdigest()==d,n
assert sha256((RAW/ART['wheel']).read_bytes()).hexdigest()==ART['wheel_sha256']
assert importlib.metadata.version('ANYsolver')=='0.4.7'
assert str(REPO/'src') not in sys.path and not (CHECKS/'src').exists()
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve())
distributions={n:importlib.metadata.version(n) for n in ('ANYmaterial','ANYmesher','ANYfileio')}
sibling_baseline={};sibling_roots=('anymaterial','anymesh','anymesher','anyfileio')
def inspect(phase):
    pools=threadpool_info();affinity=psutil.Process().cpu_affinity()
    assert affinity==[0] and numba.get_num_threads()==1 and numba.config.DISABLE_JIT
    assert all(p['num_threads']==1 for p in pools)
    env={n:os.environ.get(n) for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT','PYTHONDONTWRITEBYTECODE')}
    forced={n:os.environ.get(n) for n in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')}
    assert all(v=='1' for v in env.values()) and not any(forced.values())
    imports={};siblings={}
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=Path(filename).resolve()
        if name=='anysolver' or name.startswith('anysolver.'):
            assert path.is_relative_to(TARGET.resolve()),(phase,name,str(path))
            relative=path.relative_to(TARGET.resolve()).as_posix();digest=sha256(path.read_bytes()).hexdigest()
            assert ART['payload'][relative]==digest,(phase,name,relative)
            imports[name]=dict(path=str(path),sha256=digest,payload_key=relative)
        elif any(name==p or name.startswith(p+'.') for p in sibling_roots):
            item=dict(path=str(path),sha256=sha256(path.read_bytes()).hexdigest())
            if name in sibling_baseline:assert item==sibling_baseline[name],(phase,name,'readonly sibling changed')
            else:sibling_baseline[name]=item
            siblings[name]=item
    assert {n:importlib.metadata.version(n) for n in distributions}==distributions
    record=dict(phase=phase,commit=ART['commit'],wheel_sha256=ART['wheel_sha256'],installed_version='0.4.7',actual_installed_import_count=len(imports),all_anysolver_imports_installed=True,imports=imports,readonly_sibling_modules=siblings,dependency_distributions=distributions,pins={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__) for m in (numpy,scipy,numba,llvmlite)},affinity=affinity,pools=pools,numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),unforced_backend=forced,environment=env,sys_path=list(sys.path),cwd=str(Path.cwd()))
    (RAW/('example-imports-'+phase+'-v3.json')).write_text(json.dumps(record,indent=2)+'\n')
    return record
inspect('before')
try:
    from examples.stiffened_shell_native_fibre_bl5_mixed_j2_displacement import workflow,definition
    from anysolver import b3_ge
    model=definition()
    declared=[beam.instantiate()[0] for beam in model.beams]
    expected_ids=[element.element_id for element in declared if type(element.section) is b3_ge.PhysicalFibreSection]
    assert expected_ids==[2]
    observed=[]
    def accepted(value):
        observed.append(dict(target=value.target,amplitude=value.amplitude,generation=value.generation,relative=value.free_equilibrium_ratio,gap=value.constraint_max,s3_alpha_max=max((max(row.alpha) for row in value.shell_s3_material),default=0.),physical_fibre_material_records=len(value.beam_fibre_material),physical_stations=[dict(element_id=r.element_id,cell=r.cell,station=r.station,xi=r.xi) for r in value.beam_fibre_material],physical_station_accumulated={str(element.element_id):list(value.beam_station_accumulated[i]) for i,element in enumerate(declared) if element.element_id in expected_ids}))
        (RAW/'example-accepted-v3.json').write_text(json.dumps(observed,indent=2)+'\n')
    begun=time.monotonic();result=workflow(on_accepted=accepted);elapsed=time.monotonic()-begun
    assert result['status']=='completed' and result['s3_alpha_max']>0 and result['fibre_alpha_max']>0
    assert result['history_generation']==3 and result['generation']==4
    assert [row['element_id'] for row in result['physical_fibre_members']]==expected_ids
    for row in result['physical_fibre_members']:
        values=row['station_accumulated'];stations=[station for station in observed[-1]['physical_stations'] if station['element_id']==row['element_id']]
        assert values and len(values)==len(stations)
        assert values==observed[-1]['physical_station_accumulated'][str(row['element_id'])]
        assert [(r['cell'],r['station']) for r in stations]==sorted((r['cell'],r['station']) for r in stations)
    assert result['fibre_alpha_max']==max(v for row in result['physical_fibre_members'] for v in row['station_accumulated'])
    assert result['s3_alpha_max']==observed[-1]['s3_alpha_max']
    assert result['fresh_restore_bytes_equal'] and result['continued_bytes_equal'] and not result['production_qualified']
    assert len(observed)==2 and observed[-1]['s3_alpha_max']>0 and observed[-1]['physical_fibre_material_records']>0
    (RAW/'example-result-v3.json').write_text(json.dumps(dict(status='completed',elapsed_seconds=elapsed,result=result,accepted=observed),indent=2)+'\n')
    final=inspect('after')
    for n,d in ART['payload'].items():assert sha256((TARGET/n).read_bytes()).hexdigest()==sha256((REPO/'src'/n).read_bytes()).hexdigest()==d
    for n,d in INPUT['files'].items():assert sha256((CHECKS/n).read_bytes()).hexdigest()==sha256((REPO/n).read_bytes()).hexdigest()==d
    print(json.dumps(dict(status='completed',result=result,actual_installed_imports=final['actual_installed_import_count'])))
except BaseException:
    (RAW/'example-failure-v3.txt').write_text(traceback.format_exc());raise
finally:
    inspect('terminal')
