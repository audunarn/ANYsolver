"""One prescribed state, no equilibrium solves; draft pending root execution adoption.

Native energy/force consistency is separate from finite-mesh/continuum error.
No parameter search: nx16, e=.002, phi=30deg, lambda=1-zbar*k.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from scipy import sparse

TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "diagnostics"))
import arc_reference as ar
import anysolver.corotational as co
from anysolver.elements import BeamElement
from anysolver.matrix_assembly import assemble_load_vector

START = time.perf_counter()


def deadline():
    if time.perf_counter() - START > 24.0:
        raise TimeoutError("fixed internal24s audit deadline; no retry")


def sinc(x):
    return math.sin(x) / x if x else 1.0


def circle(x, lam, k):
    return np.array([lam * math.sin(k*x)/k, 0., lam*(math.cos(k*x)-1.)/k])


def manufactured(model, lam, k, policy):
    """Independent planar state; actual descriptor inverse checks its admission."""
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    h = 1./16
    for node in model.mesh.nodes.values():
        X = node.coords(); x = float(X[0]); e = float(X[2])
        if int(node.id) < 10000:
            p = circle(x, lam, k)
        else:
            if policy == "director_integrated":
                host = circle(x, lam, k)
            else:
                ix = min(int(math.floor(x/h)), 15); xi = x/h-ix
                host = (1-xi)*circle(ix*h, lam, k) + xi*circle((ix+1)*h, lam, k)
            p = host + np.array([e*math.sin(k*x), 0., e*math.cos(k*x)])
        # Keep the physical y coordinate; only plane-section x/z move.
        p[1] = X[1]
        u[node.dofs[:3]] = p-X
        u[node.dofs[4]] = k*x
    return u


def independent_energy(model, u, lam, k, ref):
    """Closed form for actual chord axial strain and planar Timoshenko shear."""
    h, l, E = 1./16, 1./24, ar.E
    membrane = .5*E*ref['As']*(sinc(k*h/2)*lam-1.)**2
    bending = .5*E*(ref['Is']+ref['Ib'])*k*k
    axial = shear = 0.
    S = (E/2)*ref['Ab']*(5./6.)
    Seff = 1./(1./S+l*l/(12*E*ref['Ib']))
    for ib in range(24):
        nodes = [model.mesh.get_node(10000+ib+j) for j in (0,1)]
        p = [n.coords()+u[n.dofs[:3]] for n in nodes]
        d = p[1]-p[0]
        axial += .5*E*ref['Ab']*l*(np.linalg.norm(d)/l-1.)**2
        beta = math.atan2(-d[2], d[0])
        gamma = k*(ib+.5)*l-beta
        shear += .5*l*Seff*gamma*gamma
    return dict(shell_membrane=membrane, bending=bending, beam_axial=axial, beam_shear=shear)


def native(model, u, force=False):
    deadline()
    cache = co._corotational_cache(model)
    pieces = dict(shell_membrane=0., shell_bending=0., shell_shear=0., shell_drilling=0.,
                  beam_axial=0., beam_other=0.)
    f = np.zeros_like(u)
    max_shell_gradient = 0.
    for eid, reference in cache.items():
        if reference.category not in ('shell', 'beam'):
            continue
        element = model.mesh.elements[eid]
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=int)
        ud, _, _ = co._corotational_deformation_state(reference, element, u[dofs])
        material = model.get_material(element.material_name)
        if force:
            fe, _, _ = co.corotational_work_conjugate_response(
                model, eid, element, u[dofs], tangent=False, committed_state=None)
            f[dofs] += fe
        if reference.category == 'beam':
            # Populate the same native cache without global RHS/factorization.
            if getattr(element, '_nl_cache', None) is None:
                element.compute_nonlinear_response(model.mesh, material, ud, tangent=False)
            c = element._nl_cache; v = c['T']@ud; L = c['L']
            eps = (v[6]-v[0])/L + ((v[7]-v[1])**2+(v[8]-v[2])**2)/(2*L*L)
            pieces['beam_axial'] += .5*c['EA']*L*eps*eps
            pieces['beam_other'] += .5*v@c['K_noax']@v
        else:
            c = element._nonlinear_geometry(model.mesh); v = c['T0']@ud; t = element.thickness
            C = ar.E*np.diag([1., 1., .5])  # declared nu=0 benchmark
            for gp in c['gp']:
                grad = gp['Gw']@v
                max_shell_gradient = max(max_shell_gradient, float(np.max(np.abs(grad))))
            for Bm, Bb, Bd, Gw, dw in zip(c['B_m_all'], c['B_b_all'], c['B_d_all'], c['Gw_all'], c['detw_all']):
                g = Gw@v; m = Bm@v + [.5*g[0]**2, .5*g[1]**2, g[0]*g[1]]; b = Bb@v
                pieces['shell_membrane'] += .5*t*(m@C@m)*dw
                pieces['shell_bending'] += .5*t**3/12*(b@C@b)*dw
                pieces['shell_drilling'] += .5*(ar.E/2)*t*getattr(element, 'drilling_stabilization', 1.e-3)*float((Bd@v)[0])**2*dw
            for Bs, dw in zip(c['B_s_all'], c['detw_shear_all']):
                s = Bs@v
                pieces['shell_shear'] += .5*(ar.E/2)*(5./6.)*t*(s@s)*dw
    return float(sum(pieces.values())), pieces, f, max_shell_gradient


def audit(policy, ref):
    model, load, _, _, _ = ar.build_model(16, 'nonmatching', ref)
    if policy != 'linear':
        for el in model.mesh.elements.values():
            if hasattr(el, 'shell_node_ids'):
                el.connection_trace = policy  # task-owned model only
    nodes_before = {n: model.mesh.get_node(n).coords().copy() for n in model.mesh.nodes}
    material_before = copy.deepcopy(vars(model.get_material('elastic')))
    k, lam = ref['phi'], 1-ref['neutral_axis_z']*ref['phi']
    u = manufactured(model, lam, k, policy); u_before = u.copy()
    mapping = co.build_nonlinear_rotating_mpc_map(model, sparse.eye(len(u), format='csr'))
    linear = mapping.to_linear_displacement(u)
    constraint_error = 0.
    for el in model.mesh.elements.values():
        get = getattr(el, 'get_mpc_constraints', None)
        if get is not None:
            for row in get(model.mesh):
                residual = linear[row['slave']]-sum(value*linear[d] for d,value in row['masters'].items())-row.get('value',0.)
                constraint_error = max(constraint_error, abs(residual))
    E0, parts, f, grad = native(model, u, force=True)
    analytic = independent_energy(model, u, lam, k, ref)
    external, _ = assemble_load_vector(model, load)
    rows = {}
    for index, name in enumerate(('lambda','k')):
        value = (lam,k)[index]; h = np.finfo(float).eps**.2*max(1.,abs(value))
        work = []
        for step in (h,h/2):
            energies = {}; states = {}; analytic_values = {}
            for s in (-2,-1,1,2):
                args = [lam,k]; args[index] += s*step
                states[s] = manufactured(model,*args,policy)
                energies[s] = native(model,states[s])[0]
                analytic_values[s] = sum(independent_energy(model,states[s],*args,ref).values())
            du = (-states[2]+8*states[1]-8*states[-1]+states[-2])/(12*step)
            dU = (-energies[2]+8*energies[1]-8*energies[-1]+energies[-2])/(12*step)
            dA = (-analytic_values[2]+8*analytic_values[1]-8*analytic_values[-1]+analytic_values[-2])/(12*step)
            work.append(dict(energy_derivative=float(dU),independent_derivative=float(dA),
                             native_force_work=float(f@du),external_work=float(external@du),step=step))
        # Fixed stencil comparison, no retries/step fitting. Local roundoff estimate.
        uncertainty = abs(work[1]['energy_derivative']-work[0]['energy_derivative'])/15
        uncertainty += 64*np.finfo(float).eps*max(abs(E0),1.)/(h/2)
        threshold = 1e-7*max(abs(work[1]['native_force_work']),1.)
        error = abs(work[1]['energy_derivative']-work[1]['native_force_work'])
        classification = ('unresolved_uncertainty' if uncertainty > threshold else
                          'resolved_mismatch' if error > threshold+uncertainty else
                          'consistent_with_original_derivative_bound' if error+uncertainty <= threshold else
                          'unresolved_margin')
        rows[name] = dict(stencils=work,uncertainty_local=uncertainty,threshold=threshold,
                          consistency_resolved=uncertainty<=threshold,
                          energy_force_error=error,classification=classification)
    b = sinc(k/48); a = sinc(k/32)
    circular = .5*ar.E*(ref['As']*(a*lam-1)**2+ref['Ab']*(b*(lam+.002*k)-1)**2+(ref['Is']+ref['Ib'])*k*k)
    immutable = np.array_equal(u,u_before) and all(np.array_equal(model.mesh.get_node(n).coords(),p) for n,p in nodes_before.items())
    # This elastic benchmark material has scalar/immutable public attributes.
    immutable = immutable and repr(vars(model.get_material('elastic'))) == repr(material_before)
    return dict(policy=policy,native_energy=E0,native_parts=parts,independent_default_chord_parts=analytic,
                independent_energy_error=E0-sum(analytic.values()),director_circular_energy=circular,
                continuum_energy=.5*ar.E*(ref['As']*(lam-1)**2+ref['Ab']*(lam+.002*k-1)**2+(ref['Is']+ref['Ib'])*k*k),
                constraint_error=constraint_error,coupled_work_admitted=constraint_error<=1e-10,
                constraint_admission_tolerance=1e-10,
                interpretation='Native energy/force consistency is required before any defect inference; independent-energy mismatch may be an omitted component. Coupled-work interpretation requires inverse MPC admission.',
                max_shell_transverse_gradient=grad,inputs_unchanged=immutable,
                work=rows,expected_external_lambda_work=0.,expected_external_k_work=ref['rigidity_Nm2']*k,
                global_rhs_solves=0)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    out=dict(kind='prescribed_native_energy_work_audit',status='incomplete',global_rhs_solves=0,policies=[])
    try:
        ref=ar.oracle(.002,30.)
        for policy in ('linear','director_integrated'):
            out['policies'].append(audit(policy,ref))
        out['status']='completed_audit_not_scientific_gate'
    except Exception as exc:
        out['error'] = dict(type=type(exc).__name__, message=str(exc))
        raise
    finally:
        out['elapsed_seconds']=time.perf_counter()-START
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__=='__main__': main()
