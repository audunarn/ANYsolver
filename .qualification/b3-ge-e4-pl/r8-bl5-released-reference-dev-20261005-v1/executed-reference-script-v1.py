"""New elastic reference-linear zero-width director hinge; never launches CCX.

Material face pairs define independent directors. Five collocated equations per
station tie top position and two perpendicular director components, with normal
spin free. This is neither a finite-width weld nor native finite BL5 acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from scripts.r8_e02_distributing_solid_area import _REFERENCE, _shape, _brick
from scripts.r8_e02_double_output import read_double_output
from scripts.r8_e02_rigid_tip_reference import CCX_SHA256, ReferenceParseError

IDENTITY = 'R8_BL5_RELEASED_MATERIAL_DIRECTOR_REFERENCE_LINEAR_V1_DEV'
MANUAL = 'https://www.dhondt.de/ccx_2.23.pdf'
E, NU = 210e9, .3
HS, HB, LENGTH, WIDTH, BAR_WIDTH = .02, .06, 1., .2, .04
MAX_NODES = 200


def _hash(value):
    value = json.loads(json.dumps(value,allow_nan=False))
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('ascii')).hexdigest()


def _field(values, nodes):
    if set(values) != set(nodes):
        raise ReferenceParseError('exact complete physical node field required')
    result = {n: np.array(values[n], dtype=float, copy=True) for n in nodes}
    if any(v.shape != (3,) or not np.isfinite(v).all() for v in result.values()):
        raise ReferenceParseError('finite three-component physical field required')
    return result


def _mesh(origin, spans, first_node, first_element):
    """Fixed 2x2x1 conforming Cartesian C3D20 mesh, authoritative node IDs."""
    nodes, elements, ids = {}, {}, {}
    for ix, iy in itertools.product(range(2), range(2)):
        cell = []
        for r in _REFERENCE:
            key = tuple((2*ix, 2*iy, 0)[j]+r[j]+1 for j in range(3))
            if key not in ids:
                node = first_node+len(nodes); ids[key] = node
                nodes[node] = tuple(origin[j]+spans[j]*key[j]/(4 if j < 2 else 2) for j in range(3))
            cell.append(ids[key])
        elements[first_element+len(elements)] = tuple(cell)
    return nodes, elements, ids


def _add(row, node, axis, value):
    key = (node, axis)
    row[key] = row.get(key, 0.)+value


def physical_rows(station):
    """Physical gaps: ub(bottom)-us(top), db(x,y)-ds(x,y)."""
    rows = []
    for axis in range(3):
        rows.append({(station['beam_bottom'], axis): 1., (station['shell_top'], axis): -1.})
    for axis in range(2):
        row = {}
        for node, coefficient in ((station['beam_top'], 1/HB), (station['beam_bottom'], -1/HB),
                                  (station['shell_top'], -1/HS), (station['shell_bottom'], 1/HS)):
            _add(row, node, axis, coefficient)
        rows.append(row)
    return rows


def deck_rows(station):
    """Equivalent rows with unique dependent DOFs and no dependent RHS terms.

    Director numerators substitute the preceding position equality. This changes
    the multiplier basis; recovery ALWAYS uses physical_rows, not deck multipliers.
    """
    rows = physical_rows(station)[:3]
    for axis in range(2):
        rows.append({(station['beam_top'], axis): 1.,
                     (station['shell_top'], axis): -(1+HB/HS),
                     (station['shell_bottom'], axis): HB/HS})
    return rows


def gap(station, displacements):
    return np.array([math.fsum(coefficient*float(displacements[node][axis])
                              for (node, axis), coefficient in row.items())
                     for row in physical_rows(station)])


def transpose_action(station, multiplier):
    lam = np.array(multiplier, dtype=float)
    if lam.shape != (5,) or not np.isfinite(lam).all():
        raise ValueError('finite physical force/director multiplier required')
    action = {}
    for row, value in zip(physical_rows(station), lam):
        for (node, axis), coefficient in row.items():
            action.setdefault(node, np.zeros(3))[axis] += coefficient*value
    return action


def wrench(nodes, action, origin=(0., 0., 0.)):
    origin = np.array(origin, dtype=float)
    if origin.shape != (3,) or not np.isfinite(origin).all():
        raise ValueError('finite common moment origin required')
    forces = list(action.values())
    moments = [np.cross(np.array(nodes[n])-origin, f) for n, f in action.items()]
    return np.array([math.fsum(float(f[j]) for f in forces) for j in range(3)] +
                    [math.fsum(float(m[j]) for m in moments) for j in range(3)])


def build_reference():
    """One explicit small specimen and one transverse +Fz=1 N case."""
    shell, shell_elements, shell_ids = _mesh((0., -WIDTH/2, -HS/2), (LENGTH, WIDTH, HS), 1, 1)
    beam, beam_elements, beam_ids = _mesh((0., -BAR_WIDTH/2, HS/2), (LENGTH, BAR_WIDTH, HB),
                                         1+len(shell), 1+len(shell_elements))
    nodes, elements = shell | beam, shell_elements | beam_elements
    stations = []
    for ix in range(5):
        station = dict(x=LENGTH*ix/4, shell_bottom=shell_ids[ix, 2, 0],
                       shell_top=shell_ids[ix, 2, 2], beam_bottom=beam_ids[ix, 2, 0],
                       beam_top=beam_ids[ix, 2, 2])
        if nodes[station['shell_top']] != nodes[station['beam_bottom']]:
            raise ValueError('reference physical attachment points must match')
        stations.append(station)
    root = sorted(n for n, point in shell.items() if point[0] == 0.)
    tip = beam_ids[4, 2, 1]
    dependent, rows = [], []
    for station in stations:
        for row in deck_rows(station):
            dependent.append(next(iter(row))); rows.append(row)
    if len(set(dependent)) != 25 or any(n in root for n, _ in dependent):
        raise ValueError('unique non-SPC dependent terms required')
    if any(term in dependent for row in rows for term in list(row)[1:]):
        raise ValueError('no dependent terms on equation RHS permitted')
    metadata = dict(identity=IDENTITY, ccx_version='2.23', ccx_executable_sha256=CCX_SHA256,
        element_type='C3D20', physical_nodes=nodes, elements=elements, root_nodes=root,
        shell_nodes=sorted(shell), beam_nodes=sorted(beam), shell_elements=sorted(shell_elements),
        beam_elements=sorted(beam_elements), stations=stations, load_node=tip,
        load_N=(0., 0., 1.), material=dict(E_Pa=E, nu=NU),
        geometry_m=dict(length=LENGTH, shell_width=WIDTH, shell_thickness=HS,
                        bar_width=BAR_WIDTH, bar_height=HB, centroid_z=(HS+HB)/2),
        section=dict(area_m2=BAR_WIDTH*HB, Iy_m4=BAR_WIDTH*HB**3/12,
                     Iz_m4=HB*BAR_WIDTH**3/12, G_Pa=E/(2*(1+NU)),
                     torsion='resolved isotropic continuum; no assumed J or shear area'),
        connection='five strong collocated stations, zero-width; reference-linear director hinge',
        row_units=['m','m','m','dimensionless','dimensionless'],
        reference_director=(0.,0.,1.), reference_frame=np.eye(3).tolist(),
        reference_centroid_arm=(0.,0.,-HB/2), shell_top_arm=(0.,0.,HS/2),
        model_assessment='not executed; no physical accuracy/qualification claim', manual=MANUAL)
    metadata['model_sha256'] = _hash(metadata)
    lines = ['*HEADING', IDENTITY+'; new development reference, not qualification', '*NODE']
    lines += [str(n)+','+','.join(format(v,'.17g') for v in point) for n, point in nodes.items()]
    lines += ['*ELEMENT,TYPE=C3D20,ELSET=BODY']
    for element, ids in elements.items():
        lines += [str(element)+','+','.join(map(str,ids[:15])), ','.join(map(str,ids[15:]))]
    for name, ids in (('ALL', sorted(nodes)), ('ROOT', root)):
        lines += ['*NSET,NSET='+name]
        lines += [','.join(map(str,ids[i:i+16])) for i in range(0,len(ids),16)]
    lines += ['*MATERIAL,NAME=ELASTIC','*ELASTIC',f'{E:.17g},{NU:.17g}',
              '*SOLID SECTION,ELSET=BODY,MATERIAL=ELASTIC','*BOUNDARY','ROOT,1,3,0.']
    for row in rows:
        terms = [f'{n},{axis+1},{value:.17g}' for (n,axis),value in row.items()]
        lines += ['*EQUATION',str(len(terms)),','.join(terms)]
    lines += ['*STEP','*STATIC','1.,1.','*CLOAD',f'{tip},3,1.',
              '*NODE OUTPUT,DOUBLE,NSET=ALL','U','*NODE OUTPUT,DOUBLE,NSET=ROOT','RF',
              '*NODE PRINT,NSET=ALL','U','*NODE PRINT,NSET=ROOT','RF','*END STEP']
    deck = '\n'.join(lines)+'\n'
    metadata['deck_sha256'] = hashlib.sha256(deck.encode('ascii')).hexdigest()
    return deck, metadata


def require_metadata(metadata):
    """Accept only the exact prepared specimen; reject missing/changed identities."""
    _, expected = build_reference()
    # JSON roundtrip normalizes dictionary integer keys/tuples only.
    if _hash(metadata) != _hash(expected):
        raise ReferenceParseError('metadata differs from the explicit prepared model')
    return expected


def _elastic_matrix():
    lam, mu = E*NU/((1+NU)*(1-2*NU)), E/(2*(1+NU))
    matrix = np.zeros((6,6)); matrix[:3,:3] = lam
    matrix[np.arange(3),np.arange(3)] += 2*mu
    matrix[3:,3:] = np.eye(3)*mu
    return matrix


def internal_covectors(metadata, displacements):
    """Independent linear isotropic C3D20 3x3x3 integration; no solve.

    Return each element's internal nodal covectors. The submitted Cartesian node
    geometry and canonical ordering are validated by the existing solid map.
    Engineering strains use xx,yy,zz,xy,yz,zx; stresses are work-conjugate.
    """
    model = require_metadata(metadata); nodes = model['physical_nodes']
    u = _field(displacements,nodes); constitutive = _elastic_matrix()
    points, weights = np.polynomial.legendre.leggauss(3)
    result = {}
    for element, ids in model['elements'].items():
        brick = _brick(ids,nodes)
        xyz = np.array([nodes[n] for n in ids]); displacement = np.array([u[n] for n in ids]).reshape(60)
        internal = np.zeros(60)
        for indices in itertools.product(range(3),repeat=3):
            _, grad = _shape(tuple(points[i] for i in indices))
            jacobian = xyz.T@grad
            determinant = np.linalg.det(jacobian)
            if not determinant > 0: raise ReferenceParseError('positive reference Jacobian required')
            gradient = grad@np.linalg.inv(jacobian)
            b = np.zeros((6,60))
            for j,(gx,gy,gz) in enumerate(gradient):
                b[:,3*j:3*j+3] = ((gx,0,0),(0,gy,0),(0,0,gz),(gy,gx,0),(0,gz,gy),(gz,0,gx))
            stress = constitutive@(b@displacement)
            internal += b.T@stress*determinant*math.prod(weights[i] for i in indices)
        result[element] = {n: internal.reshape(20,3)[j].copy() for j,n in enumerate(ids)}
    return result


def recover_response(metadata, displacements, reactions):
    """Expose unscaled equations/work/cuts before any physical-response scoring.

    Raw root RF is a cross-check only. Interface forces are recovered from the
    actual physical constraint transpose and independent internal covectors.
    No acceptance tolerance or success claim is inferred from parsed fields.
    """
    model = require_metadata(metadata); nodes = model['physical_nodes']; order = sorted(nodes)
    u = _field(displacements,nodes)
    rf = _field(reactions,{n:nodes[n] for n in model['root_nodes']})
    elements = internal_covectors(model,u)
    g = {n:np.zeros(3) for n in nodes}
    for forces in elements.values():
        for n,value in forces.items(): g[n] += value
    loads = {n:np.zeros(3) for n in nodes}; loads[model['load_node']] = np.array(model['load_N'])
    rows = [row for station in model['stations'] for row in physical_rows(station)]
    index = {n:3*i for i,n in enumerate(order)}
    c = np.zeros((25,3*len(nodes)))
    for i,row in enumerate(rows):
        for (n,axis),value in row.items(): c[i,index[n]+axis] = value
    free = [index[n]+j for n in order if n not in model['root_nodes'] for j in range(3)]
    residual = np.concatenate([g[n]-loads[n] for n in order])
    lam,_,rank,_ = np.linalg.lstsq(c[:,free].T,-residual[free],rcond=None)
    if rank != 25: raise ReferenceParseError('full independent physical row rank required for action recovery')
    connection_vector = -c.T@lam
    interface = {n:connection_vector[index[n]:index[n]+3].copy() for n in order}
    support = {n:g[n]-loads[n]-interface[n] for n in model['root_nodes']}
    unexplained = residual-connection_vector
    root_error = max(float(np.max(np.abs(support[n]-rf[n]))) for n in support)
    work = lambda action: math.fsum(float(value@u[n]) for n,value in action.items())
    fields = {}
    for station in model['stations']:
        sb,st,bb,bt = (station[k] for k in ('shell_bottom','shell_top','beam_bottom','beam_top'))
        point = np.array((station['x'],0.,0.))
        # Fixed one-sided host: positive x/y side, except final x uses left.
        hosts = []
        for element in model['shell_elements']:
            ids,low,high,center,span = _brick(model['elements'][element],nodes)
            if (low[0] <= point[0] <= high[0] and low[1] == 0.
                    and (point[0] < high[0] or point[0] == LENGTH)):
                hosts.append((ids,np.array(center),np.array(span)))
        if len(hosts)!=1: raise ReferenceParseError('one declared one-sided shell host required')
        ids,center,span=hosts[0]
        _,derivative=_shape(2*(point-center)/span)
        slope=(derivative*(2/span))[:,:2].T@np.array([u[n][2] for n in ids])
        director=(u[st]-u[sb])[:2]/HS
        fields[str(station['x'])] = dict(shell_mid_displacement=(u[st]+u[sb])/2,
            shell_director_change=(u[st]-u[sb])[:2]/HS,
            beam_director_change=(u[bt]-u[bb])[:2]/HB, shell_transverse_slope=slope,
            independent_director_transverse_shear=slope+director,
            geometric_normal_change=-slope, gap=gap(station,u))
    cuts = {}
    for name in ('shell','beam'):
        ids = model[name+'_nodes']
        cuts[name] = dict(internal_wrench=wrench(nodes,{n:g[n] for n in ids}),
                         applied_wrench=wrench(nodes,{n:loads[n] for n in ids}),
                         interface_wrench=wrench(nodes,{n:interface[n] for n in ids}),
                         support_wrench=wrench(nodes,{n:support[n] for n in ids if n in support}))
    return dict(status='PARSED_REFERENCE_NOT_ASSESSED', physical_multipliers=lam,
        interface_exerted_loads=interface, support_exerted_loads=support, domain_cuts=cuts,
        full_constraint_gap=c@np.concatenate([u[n] for n in order]),
        free_equilibrium_unexplained_max=float(np.max(np.abs(unexplained[free]))),
        support_RF_difference_max=root_error, support_wrench=wrench(nodes,support),
        total_external_wrench=wrench(nodes,loads)+wrench(nodes,support)+wrench(nodes,interface),
        applied_pairing_J=work(loads), interface_pairing_J=work(interface),
        support_pairing_J=work(support), internal_pairing_J=work(g), station_fields=fields,
        displacement=displacements, element_internal_covectors=elements,
        interpretation='preserve raw residuals; no physical accuracy, equilibrium or qualification acceptance')


def parse_output(frd, stdout, sta, metadata, *, deck_bytes, execution_binding=None,
                 executable_path=None, working_directory=None, stderr=''):
    """Strict saved-result route bound to actual input/output/executable bytes.

    A manifest is preserved execution evidence, not proof or authorization of a
    campaign. Missing evidence cannot produce physical recovered comparisons.
    """
    model = require_metadata(metadata)
    digest=lambda value:hashlib.sha256(value).hexdigest()
    if not isinstance(deck_bytes,bytes) or digest(deck_bytes)!=model['deck_sha256']:
        raise ReferenceParseError('actual executed deck bytes differ from prepared input')
    if execution_binding is None or executable_path is None or working_directory is None:
        return dict(status='UNVERIFIED_EXECUTION',physical_comparison_permitted=False,
                    reason='saved command/executable/input/output binding required')
    executable=Path(executable_path).resolve(); directory=Path(working_directory).resolve()
    if not executable.is_file() or executable.stat().st_size>100*1024**2:
        raise ReferenceParseError('bounded actual executable file required')
    expected=dict(schema='R8_BL5_RELEASED_REFERENCE_EXECUTION_V1',status='completed',exit_code=0,
        command=[str(executable),'-i','released'],working_directory=str(directory),
        executable_sha256=digest(executable.read_bytes()),model_sha256=model['model_sha256'],
        files={'released.inp':digest(deck_bytes),'released.frd':digest(frd),
               'stdout.log':digest(stdout.encode('utf-8')),'stderr.log':digest(stderr.encode('utf-8')),
               'released.sta':digest(sta.encode('utf-8'))})
    if expected['executable_sha256']!=CCX_SHA256 or execution_binding!=expected:
        raise ReferenceParseError('saved execution identity or actual file bytes do not match')
    if stderr.strip(): raise ReferenceParseError('nonempty external stderr preserved; adjudication required')
    if 'Job finished' not in stdout or any(token in stdout.lower() for token in ('*error','fatal','singular')):
        raise ReferenceParseError('missing completion or diagnosed external failure')
    # This one linear static step must reach time 1; no prefix/fallback accepted.
    lines = [line.split() for line in sta.splitlines() if line.strip()]
    numeric = [line for line in lines if len(line) >= 7 and line[0].isdigit()]
    if len(numeric) != 1 or numeric[0][0:2] != ['1','1'] or float(numeric[0][-2]) != 1.:
        raise ReferenceParseError('exact one completed static increment required')
    u,rf = read_double_output(frd,model)
    result=recover_response(model,u,rf)
    result['execution_binding']=expected
    result['physical_comparison_permitted']=False
    return result


def _json(value):
    return json.dumps(value,indent=2,allow_nan=False,default=lambda v:v.tolist())+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation',required=True)
    prepare = sub.add_parser('prepare'); prepare.add_argument('--output',type=Path,required=True)
    read = sub.add_parser('parse'); read.add_argument('--directory',type=Path,required=True)
    read.add_argument('--executable',type=Path,required=True)
    args = parser.parse_args()
    if args.operation == 'prepare':
        args.output.mkdir(parents=True,exist_ok=False)
        deck,model = build_reference()
        (args.output/'released.inp').write_text(deck,encoding='ascii')
        (args.output/'model.json').write_text(_json(model),encoding='ascii')
    else:
        directory=args.directory
        result = parse_output((directory/'released.frd').read_bytes(),
            (directory/'stdout.log').read_bytes().decode('utf-8'),(directory/'released.sta').read_bytes().decode('utf-8'),
            json.loads((directory/'model.json').read_text()),deck_bytes=(directory/'released.inp').read_bytes(),
            execution_binding=(json.loads((directory/'execution-binding.json').read_text())
                               if (directory/'execution-binding.json').is_file() else None),
            executable_path=args.executable,working_directory=directory,
            stderr=(directory/'stderr.log').read_bytes().decode('utf-8'))
        with (directory/'parsed.json').open('x',encoding='ascii') as stream: stream.write(_json(result))


if __name__ == '__main__': main()
