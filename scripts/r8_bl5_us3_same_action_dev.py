"""Replay saved native shell action in US3, not coupled BL5 qualification.

Same physical nodes/supports and all six work-conjugate nodal components.
There is no beam, interface constraint or remapping of the recovered action.
Differences isolate a shell-response contribution under this action; they do
not allocate the remaining coupled discrepancy to beam or connection alone.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys

import numpy as np

EXE_SHA = '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
SUPERVISOR_SHA = '5837645ddf40e591451cbd58f8975ce8f026cb908e750044b848c8c04dcae5d4'
CASES = ('fy', 'mx', 'mz')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
HEADER = re.compile(r'^\s*displacements\s+\([^\n]*\)\s+for set\s+ALLNODES\s+and time\s+(\S+)\s*$', re.I|re.M)
NUMBER = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$')


def printed(token):
    if not NUMBER.fullmatch(token):
        raise ValueError('invalid DAT number')
    try:
        decimal = Decimal(token.replace('D', 'E').replace('d', 'E'))
        value = float(decimal)
        error = float(Decimal(5).scaleb(decimal.as_tuple().exponent-1))
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise ValueError('invalid DAT number') from exc
    if not math.isfinite(value) or not math.isfinite(error) or error <= 0:
        raise ValueError('nonfinite/unrepresentable DAT number')
    # Printed zeros are numerical zeros, not unknown values of order 5e-7.
    if decimal.is_zero():
        error = math.ulp(0.)
    else:
        error = math.nextafter(error+2*math.ulp(value), math.inf)
    return value, error


def cload_number(value):
    """CalculiX cloads.f reads a 20-character F20.0 magnitude field."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('finite CLOAD magnitude required')
    for precision in range(17, 0, -1):
        token = format(value, f'.{precision}g')
        if 'e' in token:
            mantissa, exponent = token.split('e')
            token = mantissa+'E'+format(int(exponent), '+d')
        if len(token) <= 20:
            decoded = float(token)
            if math.isfinite(decoded) and (value == 0. or abs(decoded-value)/abs(value) <= 1e-12):
                return token, decoded
    raise ValueError('CLOAD magnitude not representable in declared field')


def prepare(inputs, inventory, output):
    record = json.loads(inventory.read_text())
    hashes = record['member_sha256']
    files = ('layout.json', 'operators.npz')+tuple(
        f'{case}/{name}' for case in CASES for name in ('raw-state.npz','result.json'))
    bound = {}
    for name in files:
        path = inputs/name
        expected = hashes['n64/outputs/'+name]
        if sha(path) != expected:
            raise ValueError('protected input differs: '+name)
        bound[name] = expected
    layout = json.loads((inputs/'layout.json').read_text())
    ids = layout['shell_node_ids']
    if ids != list(range(1, 1106)):
        raise ValueError('exact frozen shell numbering required')
    fixed = sorted((int(node), int(dof)+1) for domain, node, dof in layout['fixed_coordinates']
                   if domain == 'shell')
    if len(fixed) != 102 or len(set(fixed)) != 102:
        raise ValueError('exact frozen shell-root supports required')
    with np.load(inputs/'operators.npz', allow_pickle=False) as saved:
        free = saved['free'].copy()
        scales = saved['coordinate_scale'][free].copy()
    native_checks = {}
    forces, native, xyz = [], [], None
    for case in CASES:
        accepted = json.loads((inputs/case/'result.json').read_text())
        if (accepted['status'] != 'COMPLETED_DEVELOPMENT_ONLY' or accepted['failures'] or
                any(not math.isfinite(value) or value > (1e-9 if 'gap' in name else 1e-8)
                    for name,value in accepted['checks'].items())):
            raise ValueError('saved native scientific predicates do not pass unchanged criteria')
        with np.load(inputs/case/'raw-state.npz', allow_pickle=False) as saved:
            coordinates = saved['xyz_m'][:1105].copy()
            action = saved['load'][:6630]-saved['constraint_resisting'][:6630]
            state = saved['q'][:6630].copy()
            if not np.array_equal(state.reshape(1105, 6), saved['shell_poses']):
                raise ValueError('reference-linear nodal chart/state mismatch')
            residual = saved['Kq']+saved['constraint_resisting']-saved['load']
            if not np.array_equal(residual, saved['full_equilibrium']):
                raise ValueError('saved full equilibrium sign/inventory mismatch')
            applied = saved['load'][free]
            weighted_residual, weighted_applied = residual[free]*scales, applied*scales
            magnitude = max(float(np.max(abs(weighted_residual))), float(np.max(abs(weighted_applied))))
            if not magnitude > 0. or not np.all(np.isfinite(weighted_residual)):
                raise ValueError('unrepresentable native free equilibrium')
            active = applied != 0.
            ratio = max(float(np.linalg.norm(weighted_residual/magnitude)/np.linalg.norm(weighted_applied/magnitude)),
                        float(np.max(abs(residual[free][active]/applied[active]), initial=0.)))
            ground_max = max(abs(float(state[6*(node-1)+dof-1])) for node,dof in fixed)
            if not math.isfinite(ratio) or ratio > 1e-8 or ground_max > 1e-12:
                raise ValueError('native free equilibrium/ground state fails existing criterion')
            native_checks[case] = {'free_equilibrium_ratio':ratio, 'fixed_coordinate_max':ground_max,
                                   'saved_checks':accepted['checks']}
        if xyz is not None and not np.array_equal(xyz, coordinates):
            raise ValueError('case geometry differs')
        xyz = coordinates
        if (xyz.shape != (1105, 3) or action.shape != (6630,) or state.shape != (6630,)
                or not all(np.all(np.isfinite(v)) for v in (xyz, action, state))):
            raise ValueError('finite full six-channel shell action/state required')
        if not float(state@action) > 1e-12:
            raise ValueError('native work does not exceed frozen work floor')
        forces.append(action.reshape(1105, 6))
        native.append(state.reshape(1105, 6))
    if np.any(xyz[:, 2] != 0.) or not np.allclose(np.ptp(xyz, axis=0), (1., .2, 0.), rtol=0, atol=1e-15):
        raise ValueError('frozen flat 1x.2m reference required')
    root_ids = [node for node, dof in fixed if dof == 1]
    if root_ids != [node for node, p in zip(ids, xyz) if p[0] == 0.]:
        raise ValueError('frozen supports are not exact x=0 root')
    if fixed != sorted((node, dof) for node in root_ids for dof in range(1, 7)):
        raise ValueError('frozen shell root must restrain all six coordinates')
    locations = {tuple(p): node for node, p in zip(ids, xyz)}
    xs, ys = sorted(set(xyz[:, 0])), sorted(set(xyz[:, 1]))
    if len(xs) != 65 or len(ys) != 17 or len(locations) != 1105:
        raise ValueError('exact frozen 64x16 grid required')
    triangles = []
    for j in range(16):
        for i in range(64):
            a,b,c,d = (locations[(xs[ii], ys[jj], 0.)]
                       for ii,jj in ((i,j),(i+1,j),(i+1,j+1),(i,j+1)))
            triangles.extend(((a,b,c), (a,c,d)))
    lines = ['** Same native shell action, independent US3 response only',
        '*USER ELEMENT,TYPE=US3,NODES=3,INTEGRATION POINTS=3,MAXDOF=6',
        '*NODE,NSET=AllNodes']
    for node, p in zip(ids, xyz):
        lines.append(str(node)+','+','.join(format(float(v), '.17g') for v in p))
    lines.append('*ELEMENT,TYPE=US3,ELSET=Panel')
    lines.extend(str(i)+','+','.join(map(str, tri)) for i,tri in enumerate(triangles, 1))
    lines.extend(('*MATERIAL,NAME=Elastic', '*ELASTIC', '210.e9,.3',
        '*USER SECTION,ELSET=Panel,MATERIAL=Elastic,CONSTANTS=1', '.035', '*BOUNDARY'))
    lines.extend(f'{node},1,6,0.' for node in root_ids)
    deck_forces = []
    for case, action in zip(CASES, forces):
        lines.extend(('** '+case, '*STEP', '*STATIC', '1.,1.,1.e-6,1.', '*CLOAD,OP=NEW'))
        decoded = np.zeros_like(action)
        for index, (node, row) in enumerate(zip(ids, action)):
            for dof,value in enumerate(row, 1):
                if value != 0.:
                    token, number = cload_number(value)
                    lines.append(f'{node},{dof},{token}')
                    decoded[index,dof-1] = number
        deck_forces.append(decoded)
        lines.extend(('*NODE PRINT,NSET=AllNodes', 'U', '*END STEP'))
    output.mkdir(parents=True, exist_ok=False)
    deck = output/'same-action.inp'
    deck.write_bytes(('\n'.join(lines)+'\n').encode('ascii'))
    np.savez_compressed(output/'actions.npz', ids=ids, xyz=xyz, forces=forces, deck_forces=deck_forces,
        native=native, fixed=fixed, triangles=triangles)
    identity = {'classification': 'development same-action shell discriminator, not qualification',
        'inputs': str(inputs), 'inventory': str(inventory), 'inventory_sha256': sha(inventory),
        'protected_inputs_sha256': bound, 'deck_sha256': sha(deck),
        'actions_sha256': sha(output/'actions.npz'), 'cases': CASES,
        'shell_nodes':1105, 'US3_elements':2048, 'physical_rows':6630,
        'supports':len(fixed), 'E_Pa':210.e9, 'nu':.3, 'thickness_m':.035,
        'native_source':record['source_product_commit'], 'runner_sha256':sha(Path(__file__)),
        'native_checks':native_checks,
        'load_format':'explicit exponent; <=20 characters; decoded actions retained separately',
        'load_format_relative_error_max':max(float(np.max(abs((d-a)[a!=0.]/a[a!=0.])))
                                             for d,a in zip(deck_forces,forces)),
        'action_contract':'f_s=L_s-C_s.T lambda; all six reference-linear nodal covectors',
        'trace_contract':'plate-only; no beam, attachment, retained-coordinate or coupled equivalence claim'}
    (output/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    shutil.copy2(Path(__file__), output/'runner.py')
    return identity


def parse(dat, ids):
    blocks = list(HEADER.finditer(dat))
    if len(blocks) != 3:
        raise ValueError('exactly three complete six-component DAT displacement blocks required')
    displacements, uncertainties = [], []
    for i, block in enumerate(blocks):
        if float(block.group(1)) != i+1:
            raise ValueError('DAT total-time/case order mismatch')
        end = blocks[i+1].start() if i+1 < len(blocks) else len(dat)
        rows = {}
        for line in dat[block.end():end].splitlines():
            parts = line.split()
            if not parts: continue
            if (re.fullmatch(r'S\s+T\s+E\s+P\s+\d+', line.strip()) or
                    re.fullmatch(r'INCREMENT\s+\d+', line.strip())):
                continue
            if len(parts) != 7 or not parts[0].isdigit():
                raise ValueError('unexpected DAT row')
            node = int(parts[0])
            if node not in ids or node in rows:
                raise ValueError('unknown/duplicate DAT node')
            rows[node] = tuple(printed(token) for token in parts[1:])
        if set(rows) != set(ids):
            raise ValueError('incomplete six-component DAT inventory')
        displacements.append([[value for value, error in rows[node]] for node in ids])
        uncertainties.append([[error for value, error in rows[node]] for node in ids])
    return np.asarray(displacements), np.asarray(uncertainties)


def adjudicate(output):
    identity = json.loads((output/'identity.json').read_text())
    if (sha(output/'same-action.inp') != identity['deck_sha256'] or
            sha(output/'actions.npz') != identity['actions_sha256']):
        raise ValueError('prepared inputs changed')
    stdout = (output/'run/stdout.log').read_text()
    if (output/'run/stderr.log').read_text().strip():
        raise ValueError('nonempty external stderr')
    if ('Job finished' not in stdout or
            re.search(r'\*(?:WARNING|ERROR)|\bFATAL\b', stdout, re.I)):
        raise ValueError('external completion missing or warnings/errors present')
    cpu = re.findall(r'Using\s+(\d+)\s+cpu', stdout, re.I)
    if not cpu or any(int(v) != 1 for v in cpu):
        raise ValueError('external reported numerical CPU count differs')
    sta = [line.split() for line in (output/'same-action.sta').read_text().splitlines()
           if line.strip() and line.strip()[0].isdigit()]
    if (len(sta) != 3 or any(row[:4] != [str(i+1), '1', '1', '1'] or len(row) != 7 or
            tuple(float(v) for v in row[4:]) != (float(i+1),1.,1.) for i,row in enumerate(sta))):
        raise ValueError('exact three complete single-increment linear steps required')
    with np.load(output/'actions.npz', allow_pickle=False) as arrays:
        ids, xyz, forces, native = (arrays[name] for name in ('ids','xyz','forces','native'))
        deck_forces = arrays['deck_forces']
        fixed = arrays['fixed']
    u, uncertainty = parse((output/'same-action.dat').read_text(), ids.tolist())
    results = []
    for case, nominal, action, ref, native_u, error in zip(CASES, forces, deck_forces, u, native, uncertainty):
        component_work = np.asarray([math.fsum(float(f)*float(v) for f,v in zip(action[:,d], ref[:,d]))
                                     for d in range(6)])
        native_work = np.asarray([math.fsum(float(f)*float(v) for f,v in zip(nominal[:,d], native_u[:,d]))
                                  for d in range(6)])
        total, target = math.fsum(component_work), math.fsum(native_work)
        if not math.isfinite(total) or total <= 1e-12 or not math.isfinite(target):
            raise ValueError('reference work does not exceed frozen floor')
        rounding_terms = []
        for f,v,e in zip(action.flat, ref.flat, error.flat):
            term = abs(float(f))*float(e)
            rounding_terms.append(math.nextafter(term+math.ulp(term)+math.ulp(float(f)*float(v)), math.inf))
        rounding = math.nextafter(math.fsum(rounding_terms)+math.fsum(math.ulp(v) for v in component_work)+math.ulp(total), math.inf)
        if not math.isfinite(rounding):
            raise ValueError('nonfinite work uncertainty')
        force = np.sum(action[:,:3], axis=0)
        moment = np.sum(action[:,3:]+np.cross(xyz, action[:,:3]), axis=0)
        groups = {}
        for name, components in (('translation',(0,1,2)),('tangential_director',(3,4)),('normal_spin',(5,))):
            diff = float(np.linalg.norm((ref-native_u)[:,components]))
            denominator = max(float(np.linalg.norm(native_u[:,components])), float(np.linalg.norm(ref[:,components])),
                              np.finfo(float).tiny)
            groups[name] = {'native_norm':float(np.linalg.norm(native_u[:,components])),
                'reference_norm':float(np.linalg.norm(ref[:,components])),
                'difference_norm':diff, 'relative_difference':diff/denominator,
                'rounding_norm_estimate':float(np.linalg.norm(error[:,components]))}
        if not all(math.isfinite(v) for group in groups.values() for v in group.values()):
            raise ValueError('nonfinite derived response norms/ratios')
        if any(abs(ref[node-1,dof-1]) > error[node-1,dof-1] for node,dof in fixed):
            raise ValueError('supported reference coordinates not zero within printed uncertainty')
        results.append({'case':case, 'native_work_J':target, 'reference_work_J':total,
            'relative_work_change':(total-target)/target, 'work_rounding_bound_J':rounding,
            'load_serialization_work_change_J':math.fsum(float(f)*float(v) for f,v in zip((action-nominal).flat, ref.flat)),
            'load_serialization_pairing_abs_estimate_J':math.fsum(abs(float(f)*float(v))
                                                     for f,v in zip((action-nominal).flat, ref.flat)),
            'native_component_work_J':native_work.tolist(), 'reference_component_work_J':component_work.tolist(),
            'applied_force_N':force.tolist(), 'applied_moment_origin_Nm':moment.tolist(),
            'component_response':groups})
    np.savez_compressed(output/'reference-state.npz', u=u, uncertainty=uncertainty)
    result = {'classification':identity['classification'], 'cases':results, 'sta':sta,
        'reported_numerical_cpu_counts':list(map(int,cpu)), 'completed':True,
        'load_serialization_scope':'direct pairing estimates only; not a forward state/compliance error certificate',
        'claim_boundary':'same-action shell response only; no coupled accuracy, beam/connection causal allocation or F03 acceptance'}
    (output/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


def run(output, executable, supervisor):
    if sha(executable) != EXE_SHA or sha(supervisor) != SUPERVISOR_SHA:
        raise ValueError('executable or reused supervisor changed')
    shutil.copy2(supervisor, output/'supervisor.py')
    spec = importlib.util.spec_from_file_location('bounded_supervisor', output/'supervisor.py')
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
    identity = json.loads((output/'identity.json').read_text())
    identity.update(executable=str(executable), executable_sha256=EXE_SHA, supervisor_sha256=SUPERVISOR_SHA,
                    executed_runner_sha256=sha(Path(__file__)))
    shutil.copy2(Path(__file__), output/'executed-runner.py')
    (output/'execution-identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    result = service.supervised([str(executable), '-i', str(output/'same-action')], output/'run')
    parsed = adjudicate(output)
    print(json.dumps({'seconds':result['elapsed_seconds'], 'peak_bytes':result['sampled_peak_tree_bytes'],
        'cases':[{k:v for k,v in row.items() if k in ('case','native_work_J','reference_work_J','relative_work_change')}
                 for row in parsed['cases']]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare','run','parse'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--supervisor', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        if args.inputs is None or args.inventory is None: parser.error('inputs and inventory required')
        result = prepare(args.inputs, args.inventory, args.output)
        print(json.dumps({k:result[k] for k in ('deck_sha256','shell_nodes','US3_elements','physical_rows')}))
    elif args.mode == 'run':
        if args.executable is None or args.supervisor is None: parser.error('executable and supervisor required')
        run(args.output, args.executable, args.supervisor)
    else:
        print(json.dumps(adjudicate(args.output)))
