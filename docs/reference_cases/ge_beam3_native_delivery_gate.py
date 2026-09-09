"""Final exact wheel and warmed legacy-path gates; no mechanics campaign rerun.

Run only from a clean frozen revision. Every child belongs to the existing
600-second/24GiB Windows Job; this complete wave is capped at1800 seconds.
The package wave is terminal before serial balanced performance starts.
"""
import argparse
import configparser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Event
import time
import zipfile

from docs.reference_cases.ge_beam3_retained_prestress_wave import guard, supervise, write, ROOT
from docs.reference_cases.ge_beam3_mixed_p3_package_gate import summarize_timings, balanced_orders

BASE = '09351645ba17a0a5b130a1c7a48007d36dd08ada'
PY = 'C:/Python/Python313/python.exe'
PY_HASH = '08a64dc73ac3e3776b49f0097c6306bdb9c8f7990a037065213324d328467bf5'
OPERATIONS = ('CONSTRUCTION','STIFFNESS','INTERNAL_FORCE','ASSEMBLY','SOLVE','RECOVERY','NONLINEAR_SOLVE','RESTART')
BOOT = "import os,sys,runpy; os.chdir(sys.argv[1]); sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name='__main__')"


def bind(path):
    path = Path(path)
    if path.is_symlink() or path.lstat().st_file_attributes & 0x400 or not path.is_file():
        raise ValueError('regular non-reparse artifact required')
    raw = path.read_bytes()
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


def inventory(root):
    return {p.relative_to(root).as_posix(): bind(p) for p in sorted(root.rglob('*')) if p.is_file()}


def verify_dependency_contents(directory, wheels):
    """All importable/data bytes must come from the hash-frozen wheels.

Only pip-generated installation bookkeeping and declared entry-point launchers
are extra. These are inventoried too, and no executable launcher is invoked.
"""
    expected={};generated=set()
    for row in wheels.values():
        with zipfile.ZipFile(row['path']) as z:
            names=z.namelist()
            for name in names:
                if name.endswith('/'):continue
                if '.data/' in name:raise ValueError('unregistered dependency wheel layout')
                if '.dist-info/' in name:
                    stem=name.split('.dist-info/',1)[0]+'.dist-info/'
                    generated.update(stem+k for k in ('INSTALLER','REQUESTED','direct_url.json','RECORD'))
                    if name.endswith('/RECORD'):continue
                raw=z.read(name);record=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
                if name in expected and expected[name]!=record:raise ValueError('dependency wheel collision')
                expected[name]=record
                if name.endswith('.dist-info/entry_points.txt'):
                    parser=configparser.ConfigParser();parser.optionxform=str
                    parser.read_string(raw.decode('utf8'))
                    for section in ('console_scripts','gui_scripts'):
                        if parser.has_section(section):
                            generated.update('bin/'+key+'.exe' for key in parser[section])
    actual=inventory(directory)
    if any(actual.get(name)!=record for name,record in expected.items()):
        raise ValueError('installed dependency differs from frozen wheel contents')
    if set(actual)-set(expected)-generated:raise ValueError('unregistered installed dependency files')
    return actual


def extract(archive, directory):
    directory.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if not (directory/item.filename).resolve().is_relative_to(directory.resolve()):
                raise ValueError('unsafe source archive')
        z.extractall(directory)


def prepare_inputs():
    # Definition construction only; formal computations occur in isolated probes.
    sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'src')]
    from test_ge_beam3_analysis_fibre_translation import analysis as fibre
    from test_ge_beam3_native_analysis import analysis
    from test_ge_beam3_elastic_seed_continuation import model
    from test_ge_beam3_durable_coupled import durable
    standalone = {}
    for name, owner in (('fibre', fibre()), ('generalized', analysis(model()))):
        standalone[name] = dict(definitions=[raw.decode('ascii') for raw in owner._definitions],
            boundaries=[dict(name=b.name,node_ids=b.node_ids,dof_constraints=b.dof_constraints)
                        for b in owner.model.boundary_conditions])
    coupled = {}
    for name in ('Q4', 'S3-V2D'):
        owner, _ = durable(name, False)
        v = json.loads(owner._snapshot())
        coupled[name] = {k:v[k] for k in ('definitions','boundaries','program','shell','controls','shell_density')}
    return dict(standalone=standalone, coupled=coupled)


def performance_summary(rows):
    if len(rows) != 12 or any(set(r) != {'base','candidate'} for r in rows):
        raise ValueError('complete twelve balanced pairs required')
    checks = {}; timing = {}
    for family in ('B2','B3'):
        checks[family] = {}; timing[family] = {}
        for operation in OPERATIONS:
            a = [r['base']['operations'][family][operation]['wall_ns'] for r in rows]
            b = [r['candidate']['operations'][family][operation]['wall_ns'] for r in rows]
            ratios = [y/x for x,y in zip(a,b)]
            summary = summarize_timings(ratios)
            checks[family][operation] = dict(median_paired_ratio=summary['median'],
                                             passed=summary['median'] <= 1.05)
            timing[family][operation] = dict(base=summarize_timings(a),candidate=summarize_timings(b),
                                             paired=summarize_timings(ratios))
    return dict(checks=checks,diagnostic_timings=timing,
        passed=all(v['passed'] for row in checks.values() for v in row.values()),
        pair_count=12,maximum_median_paired_ratio=1.05,
        mad_and_p95='DIAGNOSTIC_SAMPLE_STATISTICS_NOT_TAIL_CONFIDENCE')


def run(revision, output, dependency_setup):
    guard(revision)
    root = Path(output).resolve(); setup = Path(dependency_setup).resolve()
    if root.is_relative_to(ROOT.resolve()): raise ValueError('external output required')
    root.mkdir(exist_ok=False)
    deadline=time.monotonic()+1800.; stop=Event(); receipts=[]
    dependencies=setup.parent/'dependencies'
    frozen = json.loads((setup/'inputs.json').read_bytes())
    if bind(PY)['sha256'] != PY_HASH: raise ValueError('frozen interpreter mismatch')
    for info in frozen['dependency_wheels'].values():
        if bind(info['path']) != {k:info[k] for k in ('bytes','sha256')}:
            raise ValueError('frozen dependency wheel mismatch')
    dependency_hashes=verify_dependency_contents(dependencies,frozen['dependency_wheels'])
    write(root/'dependency-files.json',dependency_hashes)
    write(root/'dependency-authority.json',dict(setup=bind(setup/'inputs.json'),inputs=frozen))
    for name in ('ge_beam3_delivery_installed_probe.py','ge_beam3_delivery_performance_probe.py'):
        write(root/name,(ROOT/'docs/reference_cases'/name).read_bytes())
    def child(name, command):
        directory=root/name;directory.mkdir(exist_ok=False)
        write(directory/'command.json',command)
        result=supervise(command,directory,deadline,stop)
        receipts.append(dict(name=name,**result))
        print(name,result['reason'],round(result['elapsed'],2),flush=True)
        if not result['success']: raise RuntimeError('bounded child failed: '+name)
        return result
    def probe(name, script, arguments):
        return child(name,[PY,'-I','-B','-c',BOOT,str(root),str(root/script),*map(str,arguments)])
    child('export-candidate',['git','archive','--format=zip','--output='+str(root/'source.zip'),revision])
    extract(root/'source.zip',root/'source')
    child('export-base',['git','archive','--format=zip','--output='+str(root/'base.zip'),BASE,'src'])
    extract(root/'base.zip',root/'base')
    # Build one solver artifact, once, without isolated dependency installation.
    child('build',[PY,'-B','-m','build','--wheel','--no-isolation','--outdir',str(root/'wheels'),str(root/'source')])
    wheels=list((root/'wheels').glob('*.whl'))
    if len(wheels)!=1: raise ValueError('one exact solver wheel required')
    wheel=wheels[0];wheel_hash=bind(wheel)
    child('install',[PY,'-B','-m','pip','install','--no-index','--no-deps','--no-compile',
                     '--target',str(root/'target'),str(wheel)])
    sources={p.relative_to(root/'source/src').as_posix():bind(p)
             for p in sorted((root/'source/src/anysolver').rglob('*.py'))}
    actual={p.relative_to(root/'target').as_posix():bind(p)
            for p in sorted((root/'target/anysolver').rglob('*.py'))}
    if sources!=actual: raise ValueError('complete installed/source extent or hash mismatch')
    write(root/'source-hashes.json',sources)
    write(root/'inputs.json',prepare_inputs())
    targets=(('source-control',root/'source/src'),('installed-a',root/'target'),('installed-b',root/'target'))
    errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(probe,name,'ge_beam3_delivery_installed_probe.py',
            (path,dependencies,root/'inputs.json',root/(name+'-science'))) for name,path in targets]
        for future in futures:
            try: future.result()
            except BaseException as error: errors.append(str(error))
    if errors: raise RuntimeError('package wave failed after all children terminal: '+repr(errors))
    science=inventory(root/'source-control-science')
    if len(science)!=20: raise ValueError('complete twenty-record installed inventory required')
    if any(inventory(root/(name+'-science'))!=science for name in ('installed-a','installed-b')):
        raise ValueError('source/installed scientific disagreement')
    write(root/'package-pass.json',dict(revision=revision,wheel=dict(filename=wheel.name,**wheel_hash),
        source_file_count=len(sources),scientific_records=science,source_installed_replicas_equal=True))
    # Performance is serial, never concurrent with the package/scientific wave.
    rows=[];expected=None
    paths={'base':root/'base/src','candidate':root/'target'}
    for index,order in [(-1,('base','candidate')),*enumerate(balanced_orders(12))]:
        row={}
        for label in order:
            name='performance-%02d-%s'%(index+1,label);raw=root/(name+'.json')
            probe(name,'ge_beam3_delivery_performance_probe.py',(paths[label],dependencies,raw,index))
            value=json.loads(raw.read_bytes());row[label]=value
            if expected is None:expected=value['science']
            if value['science']!=expected:raise ValueError('legacy scientific/replay output changed')
        if index>=0:rows.append(row)
    performance=performance_summary(rows)
    write(root/'performance.json',performance)
    guard(revision)
    if bind(wheel)!=wheel_hash or inventory(dependencies)!=dependency_hashes:
        raise ValueError('wheel/dependencies changed during verification')
    if not performance['passed']:raise ValueError('unchanged-path performance gate failed')
    if time.monotonic()>=deadline:raise ValueError('complete delivery wave deadline')
    write(root/'complete.json',dict(schema='GE_BEAM3_FINAL_DELIVERY_GATES_V1',revision=revision,
        runtime_tree=subprocess.check_output(['git','rev-parse',revision+':src/anysolver'],cwd=ROOT,text=True).strip(),
        baseline=BASE,wheel=dict(filename=wheel.name,**wheel_hash),package_pass=bind(root/'package-pass.json'),
        performance=bind(root/'performance.json'),all_children_terminal=True,receipts=receipts,
        independent_final_acceptance='PENDING',default_changes=False,publication=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--dependency-setup',required=True)
    args=parser.parse_args();run(args.revision,args.output,args.dependency_setup)
