"""Registered, supervised finite-pad endpoint-space comparison.

Ten geometric cases each compare P1, hybrid and enriched constraints.
This diagnostic does not select a production space or close G0B.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import zipfile

import b3_e4_f03_area_feasibility as common


ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'.qualification/b3-ge-e4-pl/f03-area-axis-v1'
PARENT_REGISTRATION='39937c33ea2efa9e58516f09e6f9cdeb852e0be4c01337511b3d8baa451f84f7'
PARENT_STATES={
    'cst_cb_baseline':'39e83b455240c9197b807863b8c3d0db39684b3b7ea46c38c1c875dd7045822e',
    'cst_cb_beam_high':'c349e99a3cdfdf7c114c73ce837245920808a5a7321b7bf7acc095fdaebaecec',
    'cst_cb_beam_low':'bea000c1c070883da024a5f53380180bdd20fc679b74431af5b1fe012d8dcfbf',
    'cst_cb_mortar_high':'481f41514f133f2b5d4759892f58801ed37bf7349d28238a14f325b39a14a72e',
    'cst_cb_mortar_low':'fe1dbc7c43712b9253a92bcad6c1ac777f30bd9711ddd1c0860e2c04b6545aed',
    'q4_baseline':'63701b07a700aab0d34d07c8af585d5f991921dbf3a054c85894f222172299b3',
    'q4_beam_high':'4fb7103246ed583442f3f48dbf07290edb2710eab3718b8fcaa635397af98c78',
    'q4_beam_low':'66c7290e9b975773617ba4ece81dbdd31e7daf570170a04311a7b302d7a584e7',
    'q4_mortar_high':'420f76363ef379c3ccebb84e0d614dbb67a7fa5dc596152c8a0f801fdc854758',
    'q4_mortar_low':'ef55c65a5c912e7329cd0f507e3f9f7ebc03bc613496c1dc3f70ad7f6d5aa615'}
VARIANTS={'baseline':(16,8),'mortar_low':(16,4),'mortar_high':(16,16),
          'beam_low':(8,8),'beam_high':(32,8)}
CASES={f'{prefix}_{label}':(topology,8,16,*counts)
       for prefix,topology in (('q4','Q4'),('cst_cb','CST-CB'))
       for label,counts in VARIANTS.items()}
FAMILIES=('P1','hybrid','enriched')
SOURCE_NAMES=(
    'b3_e4_f03_endpoint_comparison.py','_b3_e4_f03_area_hybrid_loaded.py',
    '_b3_e4_f03_area_hybrid.py','_b3_e4_f03_hybrid_stability.py',
    '_b3_e4_f03_trace_dual.py','b3_e4_f03_area_feasibility.py',
    '_b3_e4_f03_area_loaded.py','_b3_e4_f03_area_line.py','_b3_e4_f03_area_port.py',
    '_b3_e4_f03_independent_beam.py','_b3_e4_f03_independent_line.py',
    '_b3_e4_f03_independent_shell.py','_b3_e4_f03_kkt_scaling.py')
LIMITS={'free_residual_scaled':1e-8,'weak_gap_scaled':1e-9,
        'balance_scaled_absolute_max':1e-8,'energy_scaled':1e-8,
        'enriched_energy_order_scaled':1e-8,
        'structural_solve_relative_residual':1e-8,
        'auxiliary_squared_norm_change':1e-3,'baseline_parity_ratio':1.,
        'nonpositive_schur_modes':0}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def parent_state(name: str) -> Path:
    if sha(PARENT/'registration.json')!=PARENT_REGISTRATION:
        raise ValueError('parent registration changed')
    path=PARENT/name/'solved_state.npz'
    if sha(path)!=PARENT_STATES[name]:
        raise ValueError('parent snapshot changed')
    return path


def parity(name: str, states: dict) -> float:
    import numpy as np
    with np.load(parent_state(name),allow_pickle=False) as previous:
        q=previous['physical_q']; lam=previous['physical_lambda']
    if (q.shape!=states['P1_q'].shape or lam.shape!=states['P1_lambda'].shape or
            not np.all(np.isfinite(q)) or not np.all(np.isfinite(lam))):
        raise ValueError('invalid parent state layout')
    return max(float(np.max(np.abs(states['P1_q']-q)/(1e-15+1e-10*np.abs(q)))),
               float(np.max(np.abs(states['P1_lambda']-lam)/(1e-5+1e-10*np.abs(lam)))))


def observable_event(directory: Path,name: str,spec: dict,capture_state: bool) -> dict:
    import numpy as np
    if capture_state is not True:
        raise ValueError('owned state capture required')
    path=directory/'solved_state.npz'
    keys={family+'_'+field for family in FAMILIES for field in ('q','lambda')}
    with zipfile.ZipFile(path) as archive:
        if sum(item.file_size for item in archive.infolist())>64*1024**2:
            raise ValueError('snapshot exceeds bounded array envelope')
    with np.load(path,allow_pickle=False) as stored:
        if set(stored.files)!=keys:
            raise ValueError('snapshot inventory mismatch')
        q_count=2*(2*spec['n_s']+1)*(spec['n_y']+1)+6*spec['n_beam']+4
        for family in FAMILIES:
            for field,count in (('q',q_count),('lambda',3*(spec['n_mortar']+
                                                       (3 if family=='enriched' else 1)))):
                array=stored[family+'_'+field]
                if (array.shape!=(count,) or array.dtype!=np.dtype('float64') or
                        not np.all(np.isfinite(array))):
                    raise ValueError('invalid owned state array')
    return {'phase':'observables','case':name,'sha256':sha(directory/'observables.json'),
            'state_sha256':sha(path)}


def child(root: Path,name: str) -> None:
    manifest=common._registered(root)
    if any(os.environ.get(key)!='1' for key in common.THREADS):
        raise ValueError('child thread environment mismatch')
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_area_hybrid_loaded as loaded
    pools=threadpool_info()
    if not pools or any(p['num_threads']!=1 for p in pools):
        raise ValueError('child numerical pools must be single-threaded')
    parent_state(name)
    print(json.dumps({'phase':'identity','case':name,'identity':common._identity(),
                      'registration_sha256':common._registration_hash(root),
                      'threadpools':pools}),flush=True)
    spec=manifest['cases'][name]
    partial_files={}

    def preserve_family(family: str,metrics: dict,q: np.ndarray,lam: np.ndarray) -> None:
        common._json_new(root/name/(family+'_observables.json'),metrics)
        path=root/name/(family+'_state.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream,physical_q=q,physical_lambda=lam)
        for filename in (family+'_observables.json',family+'_state.npz'):
            partial_files[filename]=sha(root/name/filename)

    data,states=loaded.solve_case(spec['n_s'],spec['n_y'],spec['n_beam'],
                                 spec['n_mortar'],spec['topology'],.05,
                                 family_sink=preserve_family)
    data['family_artifact_hashes']=partial_files
    data['baseline_parity_ratio']=parity(name,states)
    common._json_new(root/name/'observables.json',data)
    with (root/name/'solved_state.npz').open('xb') as stream:
        np.savez_compressed(stream,**states)
    print(json.dumps(observable_event(root/name,name,spec,True)),flush=True)


def measurements(data: dict,spec: dict) -> dict:
    """Independently recompute physical aggregate predicates for adjudication."""
    from _b3_e4_f03_kkt_scaling import E0,F0,M0
    if (data['topology']!=spec['topology'] or data['halfwidth_m']!=.05 or
            data['mesh']!=[spec[k] for k in ('n_s','n_y','n_beam','n_mortar')] or
            set(data['families'])!=set(FAMILIES)):
        raise ValueError('case physical contract mismatch')
    outcome={k:0. for k in LIMITS}
    energies={}
    for family in FAMILIES:
        row=data['families'][family]
        energies[family]=row['shell_energy_j']+row['beam_energy_j']
        energy=abs(2*energies[family]+row['interface_work_j']-row['external_work_j'])/E0
        balance=[sum(v[j] for v in row['support_wrenches'])/
                 (M0 if j==2 else F0)+(1. if j==1 else .5 if j==2 else 0.)
                 for j in range(3)]
        if len(row['support_wrenches'])!=3 or any(len(w)!=3 for w in row['support_wrenches']):
            raise ValueError('invalid physical support inventory')
        for j in range(3):
            part=row['root_elastic_wrench'][j]+row['root_port_wrench'][j]-row['root_load_wrench'][j]
            port=row['root_line_wrench'][j]+row['root_endpoint_wrench'][j]
            if (not math.isclose(part,row['support_wrenches'][2][j],rel_tol=1e-10,abs_tol=1e-5) or
                    not math.isclose(port,row['root_port_wrench'][j],rel_tol=1e-10,abs_tol=1e-5) or
                    not math.isclose(balance[j],row['balance_scaled'][j],rel_tol=1e-10,abs_tol=1e-12)):
                raise ValueError('physical reaction partition mismatch')
        if not math.isclose(energy,row['energy_scaled'],rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError('energy identity metric mismatch')
        stability=row['stability']
        eigenvalues=stability['generalized_eigenvalues']
        expected=3*(spec['n_mortar']+(3 if family=='enriched' else 1))
        if (len(eigenvalues)!=expected or
                any(not math.isfinite(x) for x in eigenvalues) or
                eigenvalues!=sorted(eigenvalues)):
            raise ValueError('invalid finite-model Schur spectrum')
        current={'free_residual_scaled':row['free_residual_scaled'],
                 'weak_gap_scaled':row['weak_gap_scaled'],
                 'balance_scaled_absolute_max':max(map(abs,balance)),
                 'energy_scaled':energy,
                 'structural_solve_relative_residual':stability['structural_solve_relative_residual'],
                 'auxiliary_squared_norm_change':stability['auxiliary_squared_norm_change'],
                 'nonpositive_schur_modes':sum(1 for x in eigenvalues if x<=0)}
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0
               for v in current.values()):
            raise ValueError('invalid or nonfinite diagnostic metric')
        for key,value in current.items():
            outcome[key]=max(outcome[key],value)
    order=max(0.,energies['enriched']-energies['P1'],energies['enriched']-energies['hybrid'])/E0
    if not math.isclose(order,data['enriched_energy_order_scaled'],rel_tol=1e-10,abs_tol=1e-12):
        raise ValueError('energy-order metric mismatch')
    outcome['enriched_energy_order_scaled']=order
    outcome['baseline_parity_ratio']=data['baseline_parity_ratio']
    if any(not math.isfinite(v) or v<0 for v in outcome.values()):
        raise ValueError('invalid diagnostic outcome')
    return outcome


def adjudicate(root: Path) -> bool:
    import numpy as np
    manifest=common._registered(root)
    missing=[name for name in manifest['cases']
             if not (root/name/'supervision.json').is_file()]
    if missing:
        raise ValueError(f'complete supervisor inventory required before adjudication: {missing}')
    digest=common._registration_hash(root)
    decisions={}
    for name,spec in manifest['cases'].items():
        directory=root/name
        try:
            receipt=read(directory/'supervision.json')
            if receipt['registration_sha256']!=digest:
                raise ValueError('supervisor registration identity mismatch')
            if receipt['reason']!='completed' or receipt['exit_code']!=0 or receipt['failure'] is not None:
                decisions[name]={'status':'FAILED_EXECUTION','supervision':receipt}
                continue
            events=[json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
            expected=observable_event(directory,name,spec,True)
            if (receipt['reason']!='completed' or receipt['exit_code']!=0 or receipt['failure'] is not None or
                    receipt['registration_sha256']!=digest or
                    receipt['phases']!=['identity','observables'] or
                    receipt['observables_sha256']!=expected['sha256'] or
                    not 0<=receipt['elapsed_seconds']<=900 or
                    not 0<=receipt['sampled_peak_rss_bytes']<=8*1024**3 or
                    len(events)!=2 or not all(isinstance(e,dict) for e in events) or
                    events[0].get('phase')!='identity' or events[0].get('case')!=name or
                    events[0].get('identity')!=manifest['identity'] or
                    events[0].get('registration_sha256')!=digest or
                    not events[0].get('threadpools') or
                    any(p.get('num_threads')!=1 for p in events[0]['threadpools']) or
                    events[1]!=expected):
                raise ValueError('raw source/state/resource receipt mismatch')
            data=read(directory/'observables.json')
            with np.load(directory/'solved_state.npz',allow_pickle=False) as stored:
                observed_parity=parity(name,stored)
                expected_files={family+suffix for family in FAMILIES
                                for suffix in ('_observables.json','_state.npz')}
                if set(data['family_artifact_hashes'])!=expected_files:
                    raise ValueError('incomplete family artifact inventory')
                for filename,file_hash in data['family_artifact_hashes'].items():
                    if sha(directory/filename)!=file_hash:
                        raise ValueError('family artifact hash mismatch')
                for family in FAMILIES:
                    if read(directory/(family+'_observables.json'))!=data['families'][family]:
                        raise ValueError('partial/final family observables differ')
                    with np.load(directory/(family+'_state.npz'),allow_pickle=False) as partial:
                        if (set(partial.files)!={'physical_q','physical_lambda'} or
                                not np.array_equal(partial['physical_q'],stored[family+'_q']) or
                                not np.array_equal(partial['physical_lambda'],stored[family+'_lambda'])):
                            raise ValueError('partial/final family states differ')
            if observed_parity!=data['baseline_parity_ratio']:
                raise ValueError('snapshot baseline parity metric mismatch')
            metrics=measurements(data,spec)
            decision=('PASSED_DIAGNOSTIC_CHECKS' if all(metrics[k]<=v for k,v in LIMITS.items())
                      else 'FAILED_DIAGNOSTIC_CHECKS')
            if metrics['auxiliary_squared_norm_change']>1e-3:
                decision='UNRESOLVED_AUXILIARY_NORM'
            decisions[name]={'status':decision,'measurements':metrics}
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,EOFError,
                zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE','reason':f'{type(exc).__name__}: {exc}'}
    common._json_new(root/'adjudication.json',{'identity':manifest['identity'],
                     'cases':decisions,'scope':common.SCOPE})
    print(json.dumps(decisions,sort_keys=True))
    return all(d['status']=='PASSED_DIAGNOSTIC_CHECKS' for d in decisions.values())


def configure() -> None:
    common.CASES=CASES
    common.RUNNER=Path(__file__).resolve()
    common.SOURCES=tuple(ROOT/'scripts'/name for name in SOURCE_NAMES)
    common.KIND='experimental-classical-endpoint-space-comparison-v1'
    common.SCOPE='bounded three-space classical diagnostic; no continuum convergence, native qualification, G0B or G1'
    common.PHYSICAL_MODEL={
        'halfwidth_m':.05,'load':'smooth','families':list(FAMILIES),
        'parent_registration_sha256':PARENT_REGISTRATION,'parent_state_hashes':PARENT_STATES,
        'auxiliary_subdivisions_per_mortar_cell':[32,64],
        'squared_norm_change_limit':1e-3,'launch_budget_seconds':1200,
        'reference_coordinate_rtol':1e-10,'reference_coordinate_atol':1e-15,
        'reference_multiplier_rtol':1e-10,'reference_multiplier_atol':1e-5}
    common.PARITY_REFERENCE={}
    common.CAPTURE_STATE=True
    common.LIMITS=LIMITS
    common.child=child
    common._observable_event=observable_event
    common.adjudicate=adjudicate


if __name__=='__main__':
    configure()
    raise SystemExit(common.main())
