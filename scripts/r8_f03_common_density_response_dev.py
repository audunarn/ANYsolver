"""Each saved BL5 case: original equations and physical endpoint observations.

Stdlib-only preparation. Authorized child does saved matrix/vector actions only;
no equilibrium solve, assembly, condensation, new gauge, or F03 acceptance.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/agent_plans/development/r8-f03-common-density-20261010/evidence/feedback-observer-v2'
NATIVE = ROOT / 'docs/agent_plans/development/r8-bl5-matched-comparison-20261001/refinement-v1-raw/native/n16'
CAPTURE = ROOT / 'docs/agent_plans/development/r8-bl5-external-operator-20261009/fy-fullgeneral-v3'
CROSS = ROOT / 'docs/agent_plans/development/r8-bl5-external-operator-20261009/crosscase-v1'
RESPONSES = ROOT / 'docs/agent_plans/development/r8-bl5-common-density-response-20261009/run-v2'
EXTERNAL = NATIVE.parents[1] / 'external/n16'
FROZEN = NATIVE.parent
FROZEN_EXTERNAL = EXTERNAL.parent
ENV = {k: '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS', 'NUMBA_DISABLE_JIT')}
RSS_CAP = 2*1024**3
BASE = {'operator': 'constant_elastic_reference', 'affine_force': 'zero',
        'prescribed_displacement': 'zero', 'prestress': 'zero',
        'reference_source': 'official_v3.8.0_ASD_noncorot_beam_nlGeo0_conditional_binary'}


class ContractRefusal(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractRefusal(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def validate_base(base):
    require(base == BASE, 'missing or changed operator/affine/load-base interpretation')


def endpoint_rows(layout, xyz):
    """Physical nodal endpoint maps; never substitute retained cell averages."""
    rows = layout['typed_physical_nodes']
    require(len(rows) == len(xyz) == 118, '118 typed physical coordinates required')
    beam = [(r, p) for r, p in zip(rows, xyz) if r['domain'] == 'beam']
    require(len(beam) == 33, '33 beam physical nodes required')
    root, tip = beam[0], beam[-1]
    require(root[0]['q_offset'] == 510 and tip[0]['q_offset'] == 702 and
            root[0]['external_node'] == 100001 and tip[0]['external_node'] == 100033,
            'actual typed endpoint identity changed')
    length = Fraction(tip[1][0])-Fraction(root[1][0])
    require(length == 1 and tip[1][1:] == root[1][1:], 'one-metre straight beam axis required')
    y = [Fraction(0)]*708
    torsion = y.copy()
    y[703], y[511], y[515] = Fraction(1), Fraction(-1), -length
    torsion[705], torsion[513] = Fraction(1), Fraction(-1)
    return {'flexure_y_m': y, 'relative_torsion_rad': torsion}


def rigid_rows(layout, xyz, domain, full=False):
    """Six rigid motions about the actual domain root, exact represented geometry."""
    n = 1092 if full else 708
    out = [[Fraction(0)]*n for _ in range(6)]
    selected = [(r, p) for r, p in zip(layout['typed_physical_nodes'], xyz) if r['domain'] == domain]
    require(selected, 'typed domain missing')
    # All archived wrench maps use the beam-root origin, also for the shell.
    origin = list(map(Fraction, next(p for r,p in zip(layout['typed_physical_nodes'],xyz) if r['domain']=='beam')))
    for row, point in selected:
        i = row['q_offset']
        x, y, z = [Fraction(a)-b for a, b in zip(point, origin)]
        for a in range(3):
            out[a][i+a] = 1
            out[3+a][i+3+a] = 1
        out[3][i+1], out[3][i+2] = -z, y
        out[4][i], out[4][i+2] = z, -x
        out[5][i], out[5][i+1] = -y, x
    if full and domain == 'beam':
        for member in layout['retained_members']:
            slots = member['cell_rotation_slots']
            require(len(slots) == 6, 'two actual half-cell rotations required')
            for a in range(3):
                out[3+a][slots[a]] = out[3+a][slots[a+3]] = 1
    return out


def prove_annihilation(observers, motions):
    require(all(len(row)==len(motion) for row in observers.values() for motion in motions),
            'complete physical/retained work-map dimensions required')
    for name, row in observers.items():
        require(all(sum(a*b for a, b in zip(row, motion)) == 0 for motion in motions),
                name+' does not annihilate all six actual rigid motions')


def validate_rigid_map(actual, expected):
    require(len(actual)==len(expected)==6 and all(len(a)==len(b) and
            all(Fraction(x)==Fraction(y) for x,y in zip(a,b)) for a,b in zip(actual,expected)),
            'actual complete nodal/half-cell rigid work map differs')


def storage_action(flat, size, vector, order):
    """Small exact source control: explicit capture order, no symmetrization."""
    require(order in ('F', 'C') and len(flat) == size*size and len(vector) == size,
            'explicit valid capture storage required')
    return [sum(Fraction(flat[j*size+i if order == 'F' else i*size+j])*Fraction(vector[j])
                for j in range(size)) for i in range(size)]


def physical_density(native):
    """Exact inverse T.T of common.native_density, preserving all signs."""
    require(len(native) == 40, 'native density40 required')
    return [v for j in range(8) for v in
            (-native[j], -native[8+j], -native[16+j], native[32+j], -native[24+j])]


def original_supports(fixed, free):
    require(len(fixed) == 35 and len(set(fixed)) == 35 and
            all(0 <= i < 708 for i in fixed) and 515 not in fixed and
            list(free) == [i for i in range(1092) if i not in fixed],
            'original35 supports/full1092 free inventory required; rz515 stays free')


def same_contract(actual, expected, label):
    """Exact represented inventory equality; not a numerical tolerance."""
    require(actual == expected, 'stale saved '+label)


def density_receipt(actual_source, expected_source, actual_rho, expected_rho):
    require(actual_source==expected_source,'mixed density/region source receipt')
    same_contract(actual_rho,expected_rho,'regional source density receipt')


def regional_wrench(source):
    """Exact P0 integral about beam root, supports2..5, including force arm."""
    require(len(source) == 40, 'physical density40 required')
    total = [Fraction(0)]*6
    for j in range(2, 6):
        tx, ty, tz, mx, my = map(Fraction, source[5*j:5*j+5])
        x = Fraction(2*j+1, 16)
        value = (-tx, -ty, -tz, -Fraction(1,20)*ty-mx,
                 Fraction(1,20)*tx+x*tz-my, -x*ty)
        total = [a+b/Fraction(8) for a,b in zip(total,value)]
    return total


def frozen_density_measures():
    """Execute only two inspected pure integration functions, no model imports."""
    path = FROZEN_EXTERNAL/'b3_e4_bl5_external_p0_enforcement_dev.py'
    tree = ast.parse(path.read_text())
    functions = [n for n in tree.body if isinstance(n,ast.FunctionDef) and
                 n.name in ('polynomial_integral','density_measures')]
    require(len(functions) == 2, 'frozen pure measure functions required')
    space = {'math':math}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),'exec'),space)
    return space['density_measures']


def coupled_feedback(case, op, kn, cn, layout, inputs, qn, density, fn, rn, arrays):
    """Direct saved-state witness; never solve, eliminate or fix delta_rz515."""
    import numpy as np
    from scripts import r8_f03_common_density_dev as common
    with np.load(NATIVE/case/'raw-state.npz',allow_pickle=False) as archive:
        state = {k:archive[k].copy() for k in archive.files}
    meta = json.loads((NATIVE/case/'raw-state.json').read_text())
    require(meta['arrays_sha256']==sha(NATIVE/case/'raw-state.npz') and
            meta['counts']==layout['counts'] and meta['status']=='completed', 'coupled state provenance differs')
    for key in ('C_data','C_indices','C_indptr','C_shape','fixed','free','coordinate_scale',
                'constraint_scale','shell_node_ids','beam_node_ids'):
        same_contract(state[key].tolist(),op[key].tolist(),key)
    same_contract(state['xyz_m'].tolist(),inputs['xyz_m'],'typed xyz')
    same_contract(state['external_ids'].tolist(),[r['external_node'] for r in layout['typed_physical_nodes']], 'typed external IDs')
    same_contract(state['load'].tolist(),fn.tolist(),'original full load')
    original_supports(state['fixed'].tolist(),state['free'].tolist())
    qc, lam = state['q'],state['multipliers']
    require(qc.shape==(1092,) and lam.shape==(40,) and
            all(np.isfinite(a).all() for a in state.values()), 'finite coupled inventory required')
    require(not np.count_nonzero(qc[state['fixed']]),'coupled homogeneous original supports differ')
    kq, ct, gap = kn@qc,cn.T@lam,cn@qc
    # Same represented operators and action order must reproduce archived arrays.
    for key,value in (('Kq',kq),('constraint_resisting',ct),('connection_exerted',-ct),
                      ('weak_gaps',gap),('full_equilibrium',kq+ct-fn)):
        same_contract(value.tolist(),state[key].tolist(),key+' action/sign')
    reactions = np.zeros(1092);reactions[state['fixed']] = state['full_equilibrium'][state['fixed']]
    same_contract(reactions.tolist(),state['reactions'].tolist(),'fixed reaction sign/free zero')
    rho = np.asarray(physical_density(lam))
    same_contract(common.native_density(rho),lam.tolist(),'T.T inverse signs/order')
    dq, drho = qc-qn,rho-density
    lhs = kn@dq+cn.T@np.asarray(common.native_density(drho))
    correction = state['full_equilibrium']
    equilibrium_identity = lhs-(correction-rn)
    weak_lhs = np.asarray(physical_density(cn@dq))
    weak_correction = np.asarray(physical_density(state['weak_gaps']))
    weak_ideal = -np.asarray(physical_density(cn@qn))
    weak_identity = weak_lhs-(weak_correction+weak_ideal)
    free,scale = state['free'],state['coordinate_scale']
    denom = max(float(np.sum(np.abs((fn-ct)[free]*scale[free]))),1e-12)
    ratio = float(np.sum(np.abs(correction[free]*scale[free])))/denom
    require(ratio<=1e-8,'coupled original supported equation criterion failed')
    original = json.loads((NATIVE/case/'result.json').read_text())
    require(original['physical_checks']['weak_gap']<=1e-9,'archived native weak-law criterion failed')
    x,pblocks = common.role_indices(layout);p=[i for b in pblocks for i in b]
    def dimensional(v):
        return {'nodal_force_max_abs_N':float(np.max(np.abs(v[:708].reshape(-1,6)[:,:3]))),
                'nodal_moment_max_abs_Nm':float(np.max(np.abs(v[:708].reshape(-1,6)[:,3:]))),
                'retained_cell_rotation_dual_max_abs_Nm':float(np.max(np.abs(v[list(x)[708:]]))),
                'resultant_stationarity_max_abs_UNASSESSED':float(np.max(np.abs(v[p])))}
    for key,value in (('coupled_q',qc),('coupled_rho',rho),('delta_q',dq),('delta_rho',drho),
                      ('feedback_equilibrium_lhs',lhs),('coupled_original_residual',correction),
                      ('feedback_ideal_rhs',-rn),('feedback_equilibrium_identity_roundoff',equilibrium_identity),
                      ('feedback_weak_lhs',weak_lhs),('feedback_weak_correction',weak_correction),
                      ('feedback_weak_ideal_rhs',weak_ideal),('feedback_weak_identity_roundoff',weak_identity),
                      ('coupled_reactions',reactions)):
        arrays[case+'_'+key]=value
    return {'all_saved_contract_and_action_equalities':True,'roles':{'x':len(x),'p':len(p)},
            'original_free_work_denominator_J':denom,'original_free_work_ratio':ratio,
            'historical_equation_limit_1e-8_met':True,'archived_weak_gap_limit_1e-9_met':True,
            'delta_rz515_rad':float(dq[515]),'delta_original_support_max_abs':float(np.max(np.abs(dq[state['fixed']]))),
            'equilibrium_identity_roundoff_UNASSESSED':dimensional(equilibrium_identity),
            # Full correction includes actual fixed support reactions; only its
            # original free rows are coupled residual roundoff. Ideal -rN is a
            # free-row approximation, never the full supported identity.
            'coupled_original_residual_including_fixed_reactions_UNASSESSED':dimensional(correction),
            'weak_identity_roundoff_UNASSESSED':{'translation_m2':float(np.max(np.abs(weak_identity.reshape(8,5)[:,:3]))),
                                               'director_m_rad':float(np.max(np.abs(weak_identity.reshape(8,5)[:,3:])))},
            'scope':'three saved RHS witness only; no influence bound, uniform stability or F03 acceptance'}


def regional_observation(case,rho_native,rho_external,inputs,arrays,fixed):
    import numpy as np
    from types import SimpleNamespace
    from scripts import r8_f03_common_density_dev as common
    root = np.asarray((0.,0.,.0675)); stations=json.loads((NATIVE/'station-traces.json').read_text())
    constants=inputs['reference_constants']
    require(constants['BEAM_BOTTOM_ARM_M']==-.05 and constants['BEAM_AXIS_Z_M']==root[2], 'regional arm/origin changed')
    reference=SimpleNamespace(BEAM_BOTTOM_ARM_M=constants['BEAM_BOTTOM_ARM_M'])
    supports=[{'interval_m':[j/8,(j+1)/8]} for j in range(8)]
    external_map=frozen_density_measures()
    def native_map(rho):
        lam=np.asarray(common.native_density(rho)); terms=[];station_values=[]
        for s in stations:
            port=s['beam_port']; rb=np.asarray(port['frame'])
            require(np.array_equal(rb,np.eye(3)),'regional global frame changed')
            d=np.asarray(s['density_basis'])@lam[s['multiplier_rows']]
            force=rb@d[:3];director=rb@np.asarray(s['reference_director'])
            moment=np.cross(rb@np.asarray(s['reference_arm_m']),force)+np.cross(director,rb@np.asarray(s['director_basis']).T@d[3:])
            xyz=np.asarray(inputs['xyz_m'])[85:];i,j=port['node_indices'];w=port['weight']
            xb=(1-w)*xyz[i]+w*xyz[j]+rb@np.asarray(port['lift_m'])
            shell=(1-s['shell_alpha'])*np.asarray(s['shell_reference_m'])[0]+s['shell_alpha']*np.asarray(s['shell_reference_m'])[1]
            value=np.r_[force,moment+np.cross(xb-root,force)];station_values.append(value)
            if .25<shell[0]<.75: terms.append(s['measure_m']*value)
        return np.sum(terms,axis=0),np.asarray(station_values)
    recovered=json.loads((EXTERNAL/case/'recovered-actions.json').read_text())
    external_inputs=json.loads((EXTERNAL/case/'inputs.json').read_text())
    external_raw=json.loads((EXTERNAL/case/'raw-inventory.json').read_text())
    layout=json.loads((NATIVE/'layout.json').read_text())
    capture=json.loads((CAPTURE/'raw.json').read_text())['raw_inventory']
    same_contract(external_inputs['arms_m'],{'beam_normal':-.05,'shell_top':.0175},'regional physical arms')
    same_contract(external_inputs['model']['moment_origin_m'],root.tolist(),'regional global origin')
    same_contract(external_inputs['load'],inputs['loads'][case],'regional applied load')
    same_contract(external_raw['loads'],{str(layout['typed_physical_nodes'][-1]['external_node']):inputs['loads'][case]},'regional actual load')
    same_contract(external_inputs['rows'],capture['equations'],'regional integrated physical law rows')
    same_contract(external_raw['equations'],capture['equations'],'regional actual constraint rows')
    same_contract(external_raw['fixes'],capture['fixes'],'regional original supports')
    same_contract(external_inputs['model']['fixes'],capture['fixes'],'regional model supports')
    raw_fixed=[r['q_offset']+d for r in layout['typed_physical_nodes']
               for d,flag in enumerate(external_raw['fixes'].get(str(r['external_node']),[0]*6)) if flag]
    same_contract(sorted(raw_fixed),sorted(fixed.tolist()),'regional native/external physical supports')
    for row,point in zip(layout['typed_physical_nodes'],inputs['xyz_m']):
        same_contract(external_inputs['model']['nodes'][str(row['external_node'])],point,'regional model geometry')
        same_contract(external_raw['nodes'][str(row['external_node'])],point,'regional actual geometry')
    same_contract([s['interval_m'] for s in external_inputs['supports']],
                  [s['interval_m'] for s in supports],'regional P0 support measures')
    # Separate captured inference rho from the historical coupled archive rho.
    rho_archived_external=np.asarray(recovered['row_density_multipliers'],dtype=float)
    require(rho_archived_external.shape==(40,) and np.isfinite(rho_archived_external).all(),
            'finite archived external coupled physical rho required')
    transfer=json.loads((NATIVE/case/'physical-transfer.json').read_text())
    windows=json.loads((NATIVE/case/'fixed-windows.json').read_text())
    saved_external=recovered['continuous_density_measures']['fixed_region_025_075']
    load_scale=max(map(abs,inputs['loads'][case]))
    # Keep the historical 1e-8/Lref1m force-equivalent regional check.
    def compare(a,b,label):
        delta=np.asarray(a)-np.asarray(b); scaled=float(np.max(np.abs(delta)))/load_scale
        require(scaled<=1e-8,label+' same-rho regional sign/frame/arm/measure check failed')
        return {'roundoff_N_Nm_UNASSESSED':delta.tolist(),'historical_scaled_1e-8_met':True,'scaled_remainder':scaled}
    result={'observable':'beam exerted Fy[N],Mx[Nm]; x in(.25,.75); root(0,0,.0675); identity global frame',
            'no_endpoint_atoms':True,'same_geometry_support_load_physical_law_contracts':True,
            'density_sources':{'witness_external_inferred':str((CROSS/'arrays.npz').relative_to(ROOT)),
                              'historical_external_coupled':str((EXTERNAL/case/'recovered-actions.json').relative_to(ROOT)),
                              'native_coupled':str((NATIVE/case/'raw-state.npz').relative_to(ROOT))},
            'same_rho_maps':{}}
    arrays[case+'_historical_external_coupled_rho']=rho_archived_external
    integrals={}
    for label,rho in (('native_coupled_rho',rho_native),('external_inferred_response_rho',rho_external),
                      ('external_archived_coupled_rho',rho_archived_external)):
        exact=np.asarray(regional_wrench(rho),dtype=float)
        native,sv=native_map(rho);external=external_map(supports,rho.tolist(),reference)['fixed_region_025_075']['open']
        result['same_rho_maps'][label]={'native_vs_exact':compare(native,exact,label+' native'),
                                     'external_vs_exact':compare(external,exact,label+' external')}
        integrals[label]=exact;arrays[case+'_regional_'+label]=exact
        if label=='native_coupled_rho':
            saved_stations=np.asarray([r['beam_wrench_about_root_density'] for r in transfer['station_records']])
            result['native_saved_stations']=compare(sv,saved_stations,'native station density')
            for key,value in [('transfer',transfer['fixed_region_025_075_wrench']),('open',windows['open']),('closed',windows['closed'])]:
                result['native_saved_'+key]=compare(native,value,'native archived '+key)
            require(not any(windows['endpoint_atoms']),'native endpoint atoms changed')
        elif label=='external_archived_coupled_rho':
            density_receipt('historical_external_coupled','historical_external_coupled',
                            rho.tolist(),recovered['row_density_multipliers'])
            for key in ('open','closed'):
                result['external_saved_'+key]=compare(external,saved_external[key],'external archived '+key)
            require(not any(saved_external['endpoint_atoms']),'external endpoint atoms changed')
    difference=integrals['native_coupled_rho']-integrals['external_archived_coupled_rho']
    result['external_inferred_minus_archived_rho_UNASSESSED']=(rho_external-rho_archived_external).tolist()
    result['external_inferred_minus_archived_regional_N_Nm_UNASSESSED']=(
        integrals['external_inferred_response_rho']-integrals['external_archived_coupled_rho']).tolist()
    result['coupled_native_minus_external_N_Nm_UNASSESSED']=difference.tolist()
    result['selected_Fy_Mx']={k:{'native':float(integrals['native_coupled_rho'][i]),'external':float(integrals['external_archived_coupled_rho'][i]),
                                'native_minus_external':float(difference[i])} for k,i in (('Fy_N',1),('Mx_Nm',3))}
    result['interpretation']='Same-rho maps agree; any coupled regional difference is density redistribution. No law-versus-discretization causal allocation.'
    return result


def binding():
    paths = [Path(__file__).resolve(), ROOT/'tests/test_r8_f03_common_density_response_dev.py',
             ROOT/'scripts/r8_f03_common_density_dev.py']
    inputs = [NATIVE/name for name in ('operators.npz', 'layout.json', 'inputs.json', 'station-traces.json')]
    inputs += [CAPTURE/'raw.json', CAPTURE/'executed-capture-source.py',
               CROSS/'arrays.npz', CROSS/'result.json', CROSS/'receipt.json',
               RESPONSES/'arrays.npz', RESPONSES/'result.json', RESPONSES/'receipt.json', RESPONSES/'executed-source.py']
    inputs += [NATIVE/case/'raw-state.npz' for case in ('fy', 'mx', 'mz')]
    inputs += [ROOT/'scripts/b3_e4_bl5_matched_p0_native_refinement_dev.py',
               ROOT/'scripts/b3_e4_bl5_external_p0_refinement_dev.py']
    inputs += [NATIVE/'summary.json']
    for case in ('fy','mx','mz'):
        inputs += [NATIVE/case/name for name in ('raw-state.json','physical-transfer.json','fixed-windows.json','result.json')]
        inputs += [EXTERNAL/case/name for name in ('recovered-actions.json','inputs.json','raw-inventory.json')]
    frozen_ids = {
        FROZEN/'b3_e4_bl5_matched_p0_native_refinement_dev.py':'143297217ec7a4851fb79f83155d23adce7d38971bc82760e94c82a5a1f83fd7',
        FROZEN/'b3_e4_bl5_coherent_aggregation_dev.py':'9bd47696851110764486016f7d91f3de786818e87e4da88829dd76d5931f1fce',
        FROZEN/'b3_e4_bl5_matched_mz_native_dev.py':'92fa4515f1c61008f24bafe932e8fa2c50ea298903f2a1e5499e5be6c7dfaefb',
        FROZEN_EXTERNAL/'b3_e4_bl5_external_p0_enforcement_dev.py':'180e2c33d1df17239fbf30f66d9c6b400eebbfa9e5f961d83e7c9b68bdc5fdac',
        FROZEN_EXTERNAL/'b3_e4_bl5_external_p0_refinement_dev.py':'0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0'}
    for path, identity in frozen_ids.items():
        require(sha(path)==identity,'frozen producer/helper identity changed: '+str(path))
    inputs += list(frozen_ids)
    known = {NATIVE/'operators.npz': 'dd14400f93f5eaf53f54cc89300917c87326a8913aec2c1c1588d39c0af5c0d5',
             CAPTURE/'raw.json': 'ebacac2ea27341decc25a1a8ace6ca388b9b99391331f10f33297106804255b5',
             CROSS/'arrays.npz': '26e0b304296b9e6b98e9722cc4f31cc0b8d69e4d73f91494333fe1574a991dcb',
             RESPONSES/'arrays.npz': '15ba027afca89c94b9e541b381e1ab16275a9b17901cf598198074abb8f48a55',
             RESPONSES/'executed-source.py': '16474093ef69978173283c0095cdc56cf7e07a13d1862df04d5102493935aae8'}
    for path, identity in known.items():
        require(sha(path) == identity, 'protected saved input identity changed: '+str(path))
    receipt = json.loads((RESPONSES/'receipt.json').read_text())
    require(receipt['arrays_sha256']==sha(RESPONSES/'arrays.npz') and
            receipt['result_sha256']==sha(RESPONSES/'result.json'), 'saved response receipt binding differs')
    validate_base(BASE)
    return {'sources': {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
            'inputs': {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs},
            'base': BASE, 'controls': 9, 'saved_cases': ['fy', 'mx', 'mz'],
            'scope': 'saved actions only; no equilibrium or new gauge; no qualification'}


def observe(folder=None):
    import numpy as np
    from scipy import sparse
    from scripts import r8_f03_common_density_dev as common
    common.source_binding()
    layout = json.loads((NATIVE/'layout.json').read_text())
    inputs = json.loads((NATIVE/'inputs.json').read_text())
    raw = json.loads((CAPTURE/'raw.json').read_text())
    validate_base(BASE)
    x, pblocks = common.role_indices(layout)
    p = [i for block in pblocks for i in block]
    rows = endpoint_rows(layout, inputs['xyz_m'])
    wn_def = rigid_rows(layout, inputs['xyz_m'], 'beam', True)
    we = np.asarray(rigid_rows(layout, inputs['xyz_m'], 'beam'), dtype=float)
    ws = np.asarray(rigid_rows(layout, inputs['xyz_m'], 'shell'), dtype=float)
    prove_annihilation(rows, we.tolist())
    native_rows = {k: v+[Fraction(0)]*384 for k, v in rows.items()}
    prove_annihilation(native_rows, wn_def)
    ce, ids = common.external_physical_rows(raw, layout)
    full = common.decode_fullgeneral(raw)
    ke = full[np.ix_(ids, ids)]
    kc = full.T[np.ix_(ids, ids)]
    # Same integrated physical interface geometry in both typed inventories.
    for row, point in zip(layout['typed_physical_nodes'], inputs['xyz_m']):
        require(raw['raw_inventory']['nodes'][str(row['external_node'])] == point,
                'external/native physical geometry differs')
    with np.load(NATIVE/'operators.npz', allow_pickle=False) as archive:
        op = {k: archive[k].copy() for k in archive.files}
    kn, cn = [sparse.csr_matrix((op[tag+'_data'], op[tag+'_indices'], op[tag+'_indptr']),
                                shape=tuple(op[tag+'_shape'])) for tag in ('K', 'C')]
    wn = op['beam_rigid_work_map']
    validate_rigid_map(wn.tolist(), wn_def)
    wsn = op['shell_rigid_work_map']
    require(np.array_equal(wsn[:, :708], ws) and not np.count_nonzero(wsn[:, 708:]),
            'actual native shell rigid work map differs')
    with np.load(CROSS/'arrays.npz', allow_pickle=False) as archive:
        cross = {k: archive[k].copy() for k in archive.files}
    with np.load(RESPONSES/'arrays.npz', allow_pickle=False) as archive:
        saved = {k: archive[k].copy() for k in archive.files}
    require(np.array_equal(cross['external_yaw'], we[5]) and
            np.array_equal(cross['native_yaw'], wn[5]), 'actual saved yaw fields differ')
    fixed = np.asarray(op['fixed'], dtype=int)
    require(len(fixed) == 35 and np.all(fixed < 708) and 515 not in fixed, 'original35 support changed')
    free_e = np.asarray([i for i in range(708) if i not in fixed])
    free_n = np.asarray([i for i in range(1092) if i not in fixed])
    scale = op['coordinate_scale']
    actions = common.common_actions(cn.toarray(), ce)
    output = {'base': BASE, 'qualification': False, 'native_roles': {'x': len(x), 'p': len(p)},
              'actual_rigid_observer_work': {k: (np.asarray(v, dtype=float)@wn.T).tolist() for k,v in native_rows.items()},
              'original_support_count': 35, 'free_gauge_index': 515,
              'physical_K_F_minus_C_max_abs_mixed_units_UNASSESSED': float(np.max(np.abs(ke-kc))),
              'cases': {}}
    arrays = {}
    for case in ('fy', 'mx', 'mz'):
        qn, qe = saved[case+'_native_full_q'], saved[case+'_external_q']
        f, fn = cross[case+'_frozen_load'], cross[case+'_native_load']
        require(qn.shape==(1092,) and qe.shape==f.shape==(708,) and fn.shape==(1092,) and
                all(np.isfinite(a).all() for a in (qn,qe,f,fn)), 'finite original response/load dimensions required')
        with np.load(NATIVE/case/'raw-state.npz', allow_pickle=False) as archive:
            require(np.array_equal(fn, archive['load']), 'actual native applied load differs')
        require(np.array_equal(fn[:708], f) and not np.count_nonzero(fn[708:]), 'common applied tip load differs')
        density = cross[case+'_inferred_source_density']
        require(np.array_equal(np.asarray(common.native_density(density)), cross[case+'_native_density']), 'native density sign/order differs')
        en, ee = -actions.native@density, -actions.external@density
        en_old, ee_old = saved[case+'_native_full_connection'], saved[case+'_external_connection']
        rn, rf, rc = kn@qn+en-fn, ke@qe+ee-f, kc@qe+ee_old-f
        delta_k, delta_g = (ke-kc)@qe, ee-ee_old
        # These are common physical integrated dual traces, not pointwise
        # identification of native cell rotations with external nodal fields.
        trace_n, trace_e = -actions.native.T@qn, -actions.external.T@qe
        weak_gap = trace_n-trace_e
        require(qe[515] == qn[515] == 0 and not np.count_nonzero(qe[fixed]) and
                not np.count_nonzero(qn[fixed]), 'saved homogeneous supports/representative changed')
        endpoint = {}
        for name, row in rows.items():
            l = np.asarray(row, dtype=float)
            nv, ev, coupled = float(l@qn[:708]), float(l@qe), float(l@cross[case+'_u'])
            endpoint[name] = {'native': nv, 'external_saved_C': ev, 'native_minus_external_saved_C': nv-ev,
                              'external_original_coupled': coupled, 'saved_C_minus_original_coupled': ev-coupled}
        def residual_record(r, load, free, scales):
            denom = max(float(np.sum(np.abs(load[free]*scales[free]))), 1e-12)
            ratio = float(np.sum(np.abs(r[free]*scales[free])))/denom
            return {'original_work_denominator_J': denom, 'original_free_work_ratio': ratio,
                    'historical_equation_limit_1e-8_met': bool(ratio <= 1e-8),
                    'free_yaw_row_Nm': float(r[515]),
                    'nodal_force_max_abs_N': float(np.max(np.abs(r[:708].reshape(-1,6)[:,:3]))),
                    'nodal_moment_max_abs_Nm': float(np.max(np.abs(r[:708].reshape(-1,6)[:,3:]))) }
        def body_record(q, kq, e, load, residual, wbeam, wshell, free, scales):
            rr = residual_record(residual, load-e, free, scales)
            reaction = np.zeros(len(q)); reaction[fixed] = residual[fixed]
            return dict(rr, applied_beam_wrench_N_Nm=(wbeam@load).tolist(),
                        connection_beam_wrench_N_Nm=(wbeam@e).tolist(),
                        connection_shell_wrench_N_Nm=(wshell@e).tolist(),
                        fixed_beam_reaction_N_Nm=(wbeam@reaction).tolist(),
                        fixed_shell_reaction_N_Nm=(wshell@reaction).tolist(),
                        beam_original_free_residual_wrench_N_Nm=(wbeam@(residual-reaction)).tolist(),
                        free_yaw_net_RHS_Nm=float(wbeam[5]@(load-e)),
                        quadratic_signed_work_J=float(q@kq), effective_load_work_J=float(q@(load-e)),
                        residual_work_J=float(q@residual))
        report = {'endpoint_observers_UNASSESSED': endpoint,
                  'coupled_feedback':coupled_feedback(case,op,kn,cn,layout,inputs,qn,density,fn,rn,arrays),
                  'physical_integrated_trace_UNASSESSED': {
                      'channel_order': list(common.SOURCE_CHANNELS),
                      'translation_trace_max_abs_m2': float(np.max(np.abs(weak_gap.reshape(8,5)[:,:3]))),
                      'director_trace_max_abs_m_rad': float(np.max(np.abs(weak_gap.reshape(8,5)[:,3:]))),
                      'density_paired_native_minus_external_connection_work_J': float(density@weak_gap),
                      'direct_connection_work_difference_J': float(qn@en-qe@ee)},
                  'native_original_full': body_record(qn,kn@qn,en,fn,rn,wn,wsn,free_n,scale),
                  'external_original_F': body_record(qe,ke@qe,ee,f,rf,we,ws,free_e,np.ones(708)),
                  'external_historical_C': residual_record(rc,f-ee_old,free_e,np.ones(708)),
                  'C_to_F_action_remainder_UNASSESSED': {'operator_force_max_abs_N': float(np.max(np.abs(delta_k.reshape(-1,6)[:,:3]))),
                       'operator_moment_max_abs_Nm': float(np.max(np.abs(delta_k.reshape(-1,6)[:,3:]))),
                       'row_action_force_max_abs_N': float(np.max(np.abs(delta_g.reshape(-1,6)[:,:3]))),
                       'row_action_moment_max_abs_Nm': float(np.max(np.abs(delta_g.reshape(-1,6)[:,3:]))),
                       'identity_max_abs_mixed_units': float(np.max(np.abs(rf-rc-delta_k-delta_g)))},
                  'native_saved_action_max_abs_mixed_units_UNASSESSED': float(np.max(np.abs(en-en_old))),
                  'native_cell_rotation_residual_max_abs_Nm': float(np.max(np.abs(rn[[i for i in x if i>=708]]))),
                  'native_resultant_force_stationarity_max_abs_m': float(np.max(np.abs(rn[np.asarray(pblocks)[:,:6]]))),
                  'native_resultant_moment_stationarity_max_abs_rad': float(np.max(np.abs(rn[np.asarray(pblocks)[:,6:]])))}
        output['cases'][case] = report
        if folder is not None:
            save(folder/(case+'-feedback-before-regional.json'),report['coupled_feedback'])
            np.savez_compressed(folder/(case+'-feedback-before-regional.npz'),**arrays)
        report['coupled_feedback']['regional']=regional_observation(
            case,arrays[case+'_coupled_rho'],density,inputs,arrays,fixed)
        for name, value in [('native_original_residual', rn), ('external_F_residual', rf), ('external_C_residual',rc),
                            ('external_operator_remainder',delta_k), ('external_row_remainder',delta_g),
                            ('native_physical_integrated_trace',trace_n), ('external_physical_integrated_trace',trace_e),
                            ('physical_integrated_trace_difference',weak_gap)]:
            arrays[case+'_'+name] = value
    return output, arrays


def child(folder):
    import psutil
    psutil.Process().cpu_affinity([0])
    import numpy as np
    import scipy
    import unittest
    from threadpoolctl import threadpool_info
    runtime = {'python': sys.version, 'optimization': sys.flags.optimize, 'numpy': np.__version__,
               'scipy': scipy.__version__, 'affinity': psutil.Process().cpu_affinity(),
               'environment': {k: os.environ.get(k) for k in ENV}, 'pools': threadpool_info(),
               'execution_scope':'NumPy/sparse saved actions only inside authorized child; no Numba import/kernel dispatch'}
    require(runtime['affinity'] == [0] and runtime['optimization'] == 0 and runtime['environment'] == ENV and
            runtime['pools'] and all(p['num_threads']==1 for p in runtime['pools']), 'effective runtime mismatch')
    save(folder/'runtime.json', runtime)
    spec = importlib.util.spec_from_file_location('response_controls',ROOT/'tests/test_r8_f03_common_density_response_dev.py')
    controls = importlib.util.module_from_spec(spec); spec.loader.exec_module(controls)
    suite = unittest.defaultTestLoader.loadTestsFromModule(controls)
    require(suite.countTestCases()==9, 'nine discriminator controls required')
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    save(folder/'controls.json', {'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)})
    if not result.wasSuccessful():
        return 1
    try:
        observed, arrays = observe(folder)
    finally:
        runtime_after={'affinity':psutil.Process().cpu_affinity(),'optimization':sys.flags.optimize,
                       'environment':{k:os.environ.get(k) for k in ENV},'pools':threadpool_info()}
        require(runtime_after['affinity']==[0] and runtime_after['optimization']==0 and runtime_after['environment']==ENV and
                all(p['num_threads']==1 for p in runtime_after['pools']),'effective runtime changed after observer')
        save(folder/'runtime-after.json',runtime_after)
    observed.update(runtime=runtime, runtime_after=runtime_after, binding=binding(),
                    status='saved_coupled_feedback_and_regional_maps_observed_development_only')
    np.savez_compressed(folder/'observed-arrays.npz', **arrays)
    observed['arrays_sha256'] = sha(folder/'observed-arrays.npz')
    save(folder/'result.json', observed)
    print(json.dumps({'status':observed['status'],'cases':list(observed['cases']),'controls':9}))
    return 0


def supervise(authority_path, attempt):
    require(not (OUT/'ledger.json').exists(), 'fresh observer authority only; closed ledgers never reused')
    authority = json.loads(authority_path.read_text())
    bound = binding()
    require(authority['status']=='AUTHORIZED' and authority['sole_slot_released'] is True and authority['binding']==bound,
            'root prospective source/input binding and sole numerical slot required')
    require(authority['budget_seconds']<=120 and authority['reserve_seconds']>=60 and authority['process_cap_seconds']<=30,
            'fresh120, reserve60, cap30 required')
    require(attempt.isascii() and attempt.replace('-','').isalnum(), 'simple unique attempt required')
    folder = OUT/('attempt-'+attempt); require(not folder.exists(), 'preserve prior attempt'); folder.mkdir(parents=True)
    import psutil
    for i,name in enumerate(bound['sources']):
        (folder/('source-'+str(i)+'-'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
    command = [sys.executable,str(Path(__file__).resolve()),'--child',str(folder)]
    env = os.environ.copy(); env.update(ENV,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',PYTHONOPTIMIZE='0')
    cap = min(authority['process_cap_seconds'],authority['budget_seconds']-authority['reserve_seconds'])
    receipt = {'command':command,'binding':bound,'authority_sha256':sha(authority_path),
               'process_cap_seconds':cap,'rss_cap_bytes':RSS_CAP,'peak_tree_rss_bytes':0,'environment':ENV}
    save(OUT/'ledger.json',dict(status='OPEN',budget_seconds=authority['budget_seconds'],reserve_seconds=authority['reserve_seconds']))
    start = time.perf_counter(); stopped = None
    with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
        while process.poll() is None:
            try:
                tree = [psutil.Process(process.pid),*psutil.Process(process.pid).children(recursive=True)]
                rss = sum(p.memory_info().rss for p in tree if p.is_running())
                receipt['peak_tree_rss_bytes'] = max(receipt['peak_tree_rss_bytes'],rss)
            except psutil.Error:
                tree,rss = [],0
            if time.perf_counter()-start>=cap or rss>RSS_CAP:
                stopped = 'timeout' if rss<=RSS_CAP else 'rss_limit'
                for p in reversed(tree):
                    try: p.kill()
                    except psutil.Error: pass
                if process.poll() is None: process.kill()
                break
            time.sleep(.01)
        process.wait()
    wall = time.perf_counter()-start
    receipt.update(status=stopped or ('completed' if process.returncode==0 else 'failed'),exit_code=process.returncode,
                   process_wall_seconds=wall,cumulative_used_seconds=wall,remaining_seconds=authority['budget_seconds']-wall,
                   stdout_sha256=sha(folder/'stdout.txt'),stderr_sha256=sha(folder/'stderr.txt'))
    if (folder/'result.json').exists(): receipt['result_sha256']=sha(folder/'result.json')
    save(folder/'receipt.json',receipt)
    save(OUT/'ledger.json',dict(status='CLOSED',budget_seconds=authority['budget_seconds'],reserve_seconds=authority['reserve_seconds'],
                              cumulative_used_seconds=wall,remaining_seconds=receipt['remaining_seconds'],disposition=receipt['status'],
                              unused_authority='discarded; terminal slice'))
    print(json.dumps({k:receipt[k] for k in ('status','exit_code','process_wall_seconds')}))
    return int(receipt['status']!='completed')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',type=Path);parser.add_argument('--child',type=Path)
    parser.add_argument('--authority',type=Path);parser.add_argument('--attempt');args=parser.parse_args()
    require(sum(bool(v) for v in (args.prepare,args.child,args.authority))==1,'prepare or root-authorized supervisor/child required')
    if args.prepare:
        args.prepare.parent.mkdir(parents=True,exist_ok=True); save(args.prepare,binding())
    elif args.child: sys.exit(child(args.child))
    else:
        require(args.attempt,'unique attempt required');sys.exit(supervise(args.authority,args.attempt))
