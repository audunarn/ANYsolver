"""Installed private signed modes: correctness/replay, not qualification.

The rational discrete reference below is copied from the preserved same-author
standard-library reconstruction. It is not an independent review.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import permutations


def characteristic(slenderness, axial):
    if type(slenderness) is not int or slenderness < 1:
        raise ValueError('positive integral diagnostic slenderness required')
    n = F(str(axial)); ea = F(3*slenderness**2); shear = 25*ea/78
    stretch = 1+n/ea
    if stretch <= 0: raise ValueError('positive accepted axial stretch required')
    # x=(v_mid,v_tip,c1,c2,theta_mid,theta_tip), v0=theta0=0.
    k = [[F(0) for _ in range(6)] for _ in range(6)]
    for dv, c, jl, jr in (
        ([1,0,0,0,0,0], [0,0,1,0,0,0], [0,0,1,0,0,0], [0,0,-1,0,1,0]),
        ([-1,1,0,0,0,0], [0,0,0,1,0,0], [0,0,0,1,-1,0], [0,0,0,-1,0,1]),
    ):
        for i in range(6):
            for j in range(6):
                k[i][j] += (shear*dv[i]*dv[j]+(n-shear*stretch)*(dv[i]*c[j]+c[i]*dv[j])
                    +(shear*stretch**2-n*stretch)*c[i]*c[j]
                    +4*(jl[i]*jl[j]+jr[i]*jr[j])-2*(jl[i]*jr[j]+jr[i]*jl[j]))
    determinant = k[4][4]*k[5][5]-k[4][5]*k[5][4]
    inverse = [[k[5][5]/determinant, -k[4][5]/determinant],
               [-k[5][4]/determinant, k[4][4]/determinant]]
    reduced = [[k[i][j]-sum(k[i][4+a]*inverse[a][b]*k[4+b][j]
        for a in range(2) for b in range(2)) for j in range(4)] for i in range(4)]
    mass = [[F(2,3), F(1,6), F(0), F(0)], [F(1,6), F(1,3), F(0), F(0)],
        [F(0), F(0), 1/ea, F(0)], [F(0), F(0), F(0), 1/ea]]
    coefficients = [F(0)]*5
    for order in permutations(range(4)):
        sign = (-1)**sum(order[i] > order[j] for i in range(4) for j in range(i+1, 4))
        polynomial = [F(sign)]
        for i, j in enumerate(order):
            updated = [F(0)]*(len(polynomial)+1)
            for power, value in enumerate(polynomial):
                updated[power] += value*reduced[i][j]
                updated[power+1] -= value*mass[i][j]
            polynomial = updated
        coefficients = [a+b for a,b in zip(coefficients, polynomial)]
    return tuple(coefficients)


def bending_roots(slenderness, axial):
    """80-digit polynomial bisection in two separately frozen sign brackets.

    No interval certification or automatic root search. Exact polynomial
    coefficients avoid normal-equation cancellation in the comparison model.
    """
    coefficients = characteristic(slenderness, axial)
    with localcontext() as ctx:
        ctx.prec = 80
        decimal = [Decimal(x.numerator)/Decimal(x.denominator) for x in coefficients]
        def evaluate(value):
            result = decimal[-1]
            for coefficient in reversed(decimal[:-1]): result = result*value+coefficient
            return result
        roots = []
        for lower, upper in ((-10, 5), (5, 100)):
            lo, hi = Decimal(lower), Decimal(upper); left = evaluate(lo)
            if left*evaluate(hi) >= 0: raise ValueError('frozen discrete reference bracket failed')
            for _ in range(100):
                middle = (lo+hi)/2; value = evaluate(middle)
                if value == 0:
                    lo = hi = middle
                    break
                if left*value > 0: lo, left = middle, value
                else: hi = middle
            roots.append(float((lo+hi)/2))
        return tuple(roots)


def pairs(rows):
    result = {}
    for key, value in rows:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def reject(_): raise ValueError('nonfinite JSON value')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or sys.prefix == sys.base_prefix:
        raise RuntimeError('fresh isolated virtual environment required')
    if any(str(Path(p).resolve()).lower().startswith('c:\\github') for p in sys.path if p):
        raise RuntimeError('repository search path present')
    source_raw = args.source_map.read_bytes()
    source_map = json.loads(source_raw, object_pairs_hook=pairs, parse_constant=reject)
    if ((json.dumps(source_map, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode() != source_raw
            or set(source_map) != {'schema', 'candidate_commit', 'candidate_tree',
                'output_text_normalization', 'outputs', 'production_qualified'}
            or source_map['schema'] != 'GE_BEAM3_SIGNED_MODES_INSTALLED_SOURCE_MAP_V1'
            or source_map['candidate_commit'] != '2b0ee70beda6f12e81bb57aa95195c424364a23d'
            or source_map['candidate_tree'] != 'f8a21473610c6e05abe92847f796c0ea80ff88b2'
            or source_map['output_text_normalization'] != 'UTF8_LF'
            or source_map['production_qualified'] is not False
            or len(source_map['outputs']) != 67):
        raise RuntimeError('wrong installed source-map authority')
    class NoResearch:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'docs', 'tests'}: raise ImportError('research import forbidden')
            return None
    sys.meta_path.insert(0, NoResearch())
    import numpy as np
    import scipy
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_p5_loads import NativeP5BeamElement, DirectedHardeningSection
    from anysolver._ge_beam3_p5_loads.core import canonical
    from anysolver._ge_beam3_load_program import ForceProgram, solve_force_program
    from anysolver._ge_beam3_signed_loaded_modes import solve_signed_loaded_modes
    from anysolver._ge_beam3_loaded_modal import solve_elastic_modes

    root = Path(anysolver.__file__).resolve().parent
    if not root.is_relative_to(Path(sys.prefix).resolve()): raise RuntimeError('source import escaped target')
    files = {}
    for name, expected in source_map['outputs'].items():
        relative = Path(name).relative_to('src/anysolver'); path = (root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file(): raise RuntimeError('source path escape')
        raw = path.read_bytes(); normalized = raw.decode('utf-8').replace('\r\n', '\n').encode()
        if dict(bytes=len(normalized), sha256=hashlib.sha256(normalized).hexdigest()) != expected:
            raise RuntimeError('installed source mismatch: '+name)
        files[relative.as_posix()] = dict(canonical_sha256=expected['sha256'],
            installed_bytes=len(raw), installed_sha256=hashlib.sha256(raw).hexdigest())
    print('signed installed: 67 source bindings complete', flush=True)

    def straight():
        made = FEModel('installed-signed-slender'); h = 2/1000000.; ea = 12/h**2
        points = np.array([[0.,0.,0.], [1.,0.,0.], [2.,0.,0.]])
        for i, point in enumerate(points, 1): made.add_node(i, *point)
        section = DirectedHardeningSection(np.diag([ea, (5/6)*ea/2.6, (5/6)*ea/2.6, 2., 1., 1.]),
            np.array([1.,0.,0.,0.,0.,0.]), 1e6, 1.)
        e = NativeP5BeamElement(1, (1,2,3), Reference(points, np.tile(np.eye(3),(3,1,1))), section,
            line_force=np.zeros(3))
        made.add_element(1,e); made.materials[e.material_name] = e.core.section
        made.add_boundary_condition(BoundaryCondition('root',[1],
            {name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
        return made, {1:np.diag([1.,1.,1.,h*h/6,h*h/12,h*h/12])}

    def curved(count=1, plastic=False, free=False):
        made = FEModel('installed-signed-curved')
        parameters = np.linspace(-1.,1.,2*count+1); ids = (7,23,55,81,103)[:2*count+1]
        points = np.array([[x,.5*(1-x*x),.25*(1-x*x)] for x in parameters]); frames=[]
        for x in parameters:
            first=np.array([1.,-x,-.5*x]); first/=np.linalg.norm(first)
            second=np.array([0.,0.,1.]); second-=first*(first@second); second/=np.linalg.norm(second)
            frames.append(np.column_stack((first,second,np.cross(first,second))))
        for i,point in zip(ids,points): made.add_node(i,*point)
        factor=np.array([[2.,.1,0.,.2,-.1,0.],[0.,3.,.2,0.,.3,.1],[0.,0.,4.,.1,0.,.2],
            [0.,0.,0.,1.,.1,.2],[0.,0.,0.,0.,1.5,.1],[0.,0.,0.,0.,0.,2.]])
        inertia=np.diag([2.,2.,2.,.2,.1,.15])
        coupling=np.array([[0.,-.02,.01],[.02,0.,-.03],[-.01,.03,0.]])
        inertia[:3,3:]=coupling; inertia[3:,:3]=coupling.T; inertia[3,4]=inertia[4,3]=.005
        for c in range(count):
            section=DirectedHardeningSection(factor.T@factor,np.array([1.,.2,-.1,.3,-.4,.5]),
                .02 if plastic else 1000.,.4)
            e=NativeP5BeamElement(c+1,ids[2*c:2*c+3],Reference(points[2*c:2*c+3],
                np.array(frames[2*c:2*c+3])),section,line_force=np.array([.03,-.02,.01]))
            made.add_element(c+1,e); made.materials[e.material_name]=e.core.section
        if not free:
            made.add_boundary_condition(BoundaryCondition('root',[7],
                {name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
        return made,{i:inertia.copy() for i in made.mesh.elements}

    rows=[]; diagnostics={}
    for case in ('straight_compression','straight_tension','curved_pair','plastic_unloading','free_curved'):
        print('signed installed: '+case+' initialized',flush=True)
        axial=-1. if case=='straight_compression' else .5
        if case.startswith('straight'):
            factory=straight; program=ForceProgram((.5,1.),((3,axial,0.,0.),)); count=4; bounds=(-10.,100.)
        elif case=='curved_pair':
            factory=lambda:curved(2); program=ForceProgram((.5,1.)); count=6; bounds=(-10000.,1000000.)
        elif case=='plastic_unloading':
            factory=lambda:curved(plastic=True); program=ForceProgram((.5,1.,0.)); count=6; bounds=(-10000.,1000000.)
        else:
            factory=lambda:curved(free=True); program=None; count=7; bounds=(-10000.,1000000.)
        made,inertias=factory()
        if program is not None:
            result=solve_force_program(made,program)
            if result.status!='completed': raise RuntimeError(str(result.failure))
            states={r['element_id']:r['state'] for r in json.loads(result.checkpoint)['element_states']}
            total=result.displacements; parameter=result.parameter; checkpoint=result.checkpoint
        else:
            states={i:e.init_model_bound_nonlinear_state(made.mesh,e.core.section,1)
                for i,e in made.mesh.elements.items()}
            total=np.zeros(18); parameter=0.; checkpoint=canonical({i:e.serialize_native_material_state(
                made.mesh,states[i]) for i,e in made.mesh.elements.items()})
        force=np.zeros(len(total))
        if case.startswith('straight'): force[12]=parameter*axial
        before=canonical(states)
        packet,modes=solve_signed_loaded_modes(made,states,total,inertias,force,
            load_parameter=parameter,bounds=bounds,num_modes=count)
        if canonical(states)!=before: raise RuntimeError('installed modes changed state')
        if modes.spectral_residual>1e-11 or modes.full_backward_residual>1e-11:
            raise RuntimeError('installed mode residual failed')
        if np.linalg.norm(modes.full_modes.T@packet.mass@modes.full_modes-np.eye(count))>1e-11:
            raise RuntimeError('installed physical mass normalization failed')
        if modes.production_qualified or modes.buckling_factor_authorized or modes.certified_intervals:
            raise RuntimeError('installed private scope upgraded')
        if case.startswith('straight'):
            expected=np.repeat(bending_roots(1000000,axial),2)
            if np.max(np.abs(modes.eigenvalues-expected))>1e-9:
                raise RuntimeError('installed finite-shear reference disagreement')
            if not np.all(np.sign(modes.eigenvalues)==np.sign(expected)):
                raise RuntimeError('installed negative mode lost')
        elif case=='free_curved':
            if np.max(np.abs(modes.eigenvalues[:6]))>1e-11 or modes.eigenvalues[6]<=1e-6:
                raise RuntimeError('installed free rigid-mode count failed')
        else:
            _,dense=solve_elastic_modes(made,states,total,inertias,force,load_parameter=parameter,num_modes=count)
            if np.max(np.abs(modes.eigenvalues-dense.eigenvalues))>1e-9:
                raise RuntimeError('installed moderate dense spectrum disagreement')
            if case=='plastic_unloading':
                decoded=made.mesh.elements[1].validate_model_bound_nonlinear_state(made.mesh,
                    made.mesh.elements[1].core.section,states[1],1)
                if not any(h.accumulated>0. for h in decoded['material_state']['histories']):
                    raise RuntimeError('installed plastic history missing')
        clone,clone_inertias=factory()
        if program is not None:
            again=solve_force_program(clone,program,checkpoint=checkpoint)
            if again.status!='completed' or again.checkpoint!=checkpoint: raise RuntimeError('installed restart differs')
            replay_states={r['element_id']:r['state'] for r in json.loads(again.checkpoint)['element_states']}
            replay_total=again.displacements
        else:
            replay_states={int(i):state for i,state in json.loads(checkpoint).items()}
            replay_total=total
        replay=solve_signed_loaded_modes(clone,replay_states,replay_total,clone_inertias,force,
            load_parameter=parameter,bounds=bounds,num_modes=count)
        if canonical((packet,modes))!=canonical(replay): raise RuntimeError('installed modes changed on replay')
        try:
            solve_signed_loaded_modes(made,states,total,inertias,force,
                load_parameter=parameter+.125,bounds=bounds,num_modes=count)
        except ValueError: pass
        else: raise RuntimeError('installed load-parameter mismatch accepted')
        for name,raw in ((case+'-state.json',checkpoint),(case+'-modes.json',canonical((packet,modes)))):
            with (args.output.parent/name).open('xb') as stream: stream.write(raw)
            diagnostics[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        rows.append(dict(case=case,retained_coordinates=len(packet.mass),mode_count=count,
            negative_count=int(np.count_nonzero(modes.eigenvalues < -1e-11)),state_preserved=True,
            replay_exact=True,parameter_mismatch_rejected=True,checks_passed=True))
        print('signed installed: '+case+' replay/evidence complete',flush=True)
    for name,module in tuple(sys.modules.items()):
        if name=='anysolver' or name.startswith('anysolver.'):
            origin=getattr(module,'__file__',None)
            if origin is not None and not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver import escaped installed target')
    if any(hasattr(anysolver,name) for name in ('solve_signed_loaded_modes','SignedLoadedModes',
            'solve_signed_factor_modes','SignedFactorModes','NativeP5BeamElement')):
        raise RuntimeError('private path publicly exported')
    result=dict(schema='GE_BEAM3_SIGNED_MODES_INSTALLED_CHECK_V1',production_qualified=False,
        release_authorized=False,imports_isolated=True,research_imports_forbidden=True,
        signed_cases_passed=True,state_replay_exact=True,cases=rows,diagnostics=diagnostics,
        runtime=dict(python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__),
        source_files=files,source_map_sha256=hashlib.sha256(source_raw).hexdigest())
    with args.output.open('xb') as stream: stream.write(canonical(result))
    print('signed installed: evidence complete',flush=True)


if __name__=='__main__': main()
