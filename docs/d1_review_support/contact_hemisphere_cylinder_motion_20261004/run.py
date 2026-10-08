from pathlib import Path
import os,sys,json,subprocess,time,hashlib
import psutil
ROOT=Path('C:/ANYworkspaceWork/contact_hemisphere_cylinder_motion_20261004')
APP=Path('C:/ANYworkspaceWork/ANYfem-contact-intent')
SOLVER=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
tag=sys.argv[1]
targets=sys.argv[2:]
dest=ROOT/tag
dest.mkdir()
env=dict(os.environ)
env.update(PYTHONPATH=f'{APP}/src;{SOLVER}/src;{SOLVER}',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    NUMBA_DISABLE_JIT='1',NUMBA_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
    MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',
    ANYSOLVER_DEVELOPMENT_SOURCE=str(SOLVER/'src/anysolver'),
    ANYSOLVER_DEVELOPMENT_RECORD=str(dest/'runtime.json'), CONTACT_APP_RECORD=str(dest/'imports.json'))
env['CONTACT_SOLVER_SOURCE_SHA']=subprocess.check_output(['git','-c',f'safe.directory={SOLVER}','rev-parse','HEAD'],cwd=SOLVER,text=True).strip()
installed=os.environ.get('CONTACT_INSTALLED_TARGET')
if installed:
    env['PYTHONPATH']=f'{installed};{SOLVER}'
    env['ANYSOLVER_DEVELOPMENT_SOURCE']=str(Path(installed)/'anysolver')
env['CONTACT_APP_EXPECTED_ROOT']=str(Path(installed)/'anyfem' if installed else APP/'src/anyfem')
env['CONTACT_SOLVER_EXPECTED_ROOT']=env['ANYSOLVER_DEVELOPMENT_SOURCE']
env['CONTACT_APP_RESULT_RECORD']=str(dest/'actual_result.json')
code='''import pytest, sys, os, json, hashlib
from pathlib import Path
rc=pytest.main(sys.argv[1:])
rows={n:{'path':str(Path(m.__file__).resolve()),'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
      for n,m in list(sys.modules.items()) if (n=='anyfem' or n.startswith('anyfem.') or n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
errors=[n for n,r in rows.items() if not Path(r['path']).is_relative_to(Path(os.environ['CONTACT_APP_EXPECTED_ROOT' if n.startswith('anyfem') else 'CONTACT_SOLVER_EXPECTED_ROOT']))]
Path(os.environ['CONTACT_APP_RECORD']).write_text(json.dumps({'modules':rows,'errors':errors},indent=2))
raise SystemExit(rc or bool(errors))
'''
if os.environ.get('CONTACT_APP_PREIMPORT') == '1':
    env.pop('PYTEST_DISABLE_PLUGIN_AUTOLOAD',None)
    code=code.replace('import pytest, sys', 'import anyfem, anysolver, pytest, sys')
command=[sys.executable,'-X','utf8','-c',code,'-q','-p','no:cacheprovider','-p','scripts.development_test_runtime',
         '--durations=5',f'--basetemp={dest}/temp',*targets]
if installed:
    command.extend(['-o', 'pythonpath='])
paths=[Path(t.partition('::')[0]) if Path(t.partition('::')[0]).is_absolute() else APP/t.partition('::')[0] for t in targets]
if targets in (['BUILD'], ['BUILD2']):
    dist=ROOT/('dist2' if targets==['BUILD2'] else 'dist')
    command=[sys.executable,'-m','pip','wheel','--no-cache-dir','--no-deps','--no-build-isolation','--wheel-dir',str(dist),str(SOLVER)]
    env['PIP_NO_INDEX']='1'
    paths=[SOLVER/'pyproject.toml']
elif targets in (['INSTALL'], ['INSTALL2']):
    dist=ROOT/('dist2' if targets==['INSTALL2'] else 'dist')
    target=ROOT/('installed2' if targets==['INSTALL2'] else 'installed')
    command=[sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(target),
             *map(str, sorted(dist.glob('*.whl')))]
    paths=list(dist.glob('*.whl'))
paths += [SOLVER/p for p in ('src/anysolver/general_contact/beam_hemisphere_cylinder_motion.py','tests/test_general_contact_hemisphere_cylinder_motion.py','examples/general_contact_hemisphere_cylinder_motion.py','src/anysolver/general_contact/beam_hemisphere_cylinder_work.py','src/anysolver/general_contact/beam_hemisphere_cylinder.py','tests/test_general_contact_hemisphere_cylinder_work.py','tests/test_general_contact_hemisphere_cylinder_static.py','tests/test_general_contact_multiple_hemisphere_cylinders.py','examples/general_contact_hemisphere_cylinder.py','src/anysolver/general_contact/beam_hemisphere_sphere.py','src/anysolver/general_contact/beam_radial_ends.py','src/anysolver/general_contact/multiple_beam_rigid.py','src/anysolver/general_contact/core.py')]
(dest/'inputs.json').write_text(json.dumps({'command':command,'source_sha':env['CONTACT_SOLVER_SOURCE_SHA'],
    'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    'timeout_s':180,'memory_limit_mib':953,'scope':'actual cylinder hemisphere code development; no acceptance'},indent=2))
started=time.monotonic();peak=0;status='completed'
with (dest/'run.log').open('wb') as log:
    child=subprocess.Popen(command,cwd=SOLVER,env=env,stdout=log,stderr=subprocess.STDOUT)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:
            family=[proc,*proc.children(recursive=True)]
            used=sum(p.memory_info().rss for p in family if p.is_running())
            peak=max(peak,used)
        except psutil.NoSuchProcess:
            pass
        if time.monotonic()-started>180 or peak>953*1024**2:
            status='timeout' if time.monotonic()-started>180 else 'memory_limit'
            try:
                for p in proc.children(recursive=True):
                    try:p.kill()
                    except psutil.NoSuchProcess:pass
                proc.kill()
            except psutil.NoSuchProcess:pass
            break
        time.sleep(.1)
    child.wait(timeout=10)
row={'status':status,'returncode':child.returncode,'elapsed_s':time.monotonic()-started,'peak_bytes':peak}
(dest/'resource.json').write_text(json.dumps(row,indent=2))
print(json.dumps(row))
print((dest/'run.log').read_text(encoding='utf-8',errors='replace')[-6000:])
raise SystemExit(child.returncode if status=='completed' else 124)
