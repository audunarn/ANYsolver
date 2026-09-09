"""Bounded two-macro retained-resultant research solve. No native state commit.

This deliberately does not pretend to be a production controller: supports
are a complete root, external work is a dead tip force, and sections must stay
elastic. The same coupled section and curved geometry enter the probe.
"""
from time import monotonic
import numpy as np
from scipy import sparse
from anysolver.assembly import build_constraint_transformation
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from docs.reference_cases.ge_beam3_full_resultant_legendre_probe import ElasticResultantProbe


def solve_two_macro_probe(model, tip_force, checkpoint=lambda record: None):
    start = monotonic()
    if tuple(model.mesh.nodes) != (1, 2, 3, 4, 5) or tuple(model.mesh.elements) != (1, 2):
        raise ValueError('exact two-macro diagnostic topology required')
    elements = [model.mesh.elements[i] for i in (1, 2)]
    if tuple(e.node_ids for e in elements) != ((1, 2, 3), (3, 4, 5)):
        raise ValueError('exact two-macro diagnostic connectivity required')
    if model.mesh.dof_manager.total_dofs != 30 or model.mesh.element_activity is not None or model.mesh.point_masses or model.constraint_equations:
        raise ValueError('plain standalone two-macro diagnostic required')
    _, _, transform, offset, actual_free, info = build_constraint_transformation(
        sparse.eye(30, format='csr'), np.zeros(30), model)
    if (list(actual_free) != list(range(6, 30)) or np.any(offset)
            or info['slave_dofs'] or transform.nnz != 24 or np.any(transform.data != 1.)):
        raise ValueError('complete root-only support required')
    for e in elements: e._check(model.mesh)
    if not np.array_equal(elements[0].core.reference.nodal_triads[-1], elements[1].core.reference.nodal_triads[0]):
        raise ValueError('common shared-node frame authority required')
    force = np.asarray(tip_force, dtype=float)
    if force.shape != (3,) or not np.isfinite(force).all(): raise ValueError('finite tip force required')
    probes = [ElasticResultantProbe(e) for e in elements]
    x = np.array([model.mesh.nodes[i].coords() for i in (1, 2, 3, 4, 5)])
    low = np.zeros_like(x)
    q = np.concatenate((elements[0].core.reference.nodal_triads,
                        elements[1].core.reference.nodal_triads[1:]))
    u = np.tile(np.eye(3), (2, 2, 1, 1)); p = np.zeros((2, 18))
    # q30 + two (cell-rotation6, resultant18) blocks. No internal condensation.
    slots = [list(e.get_dof_mapping(model.mesh))+list(range(30+24*i, 54+24*i))
             for i, e in enumerate(elements)]
    equilibrium = list(range(6, 30))+list(range(30, 36))+list(range(54, 60))
    compatibility = list(range(36, 54))+list(range(60, 78))
    free = list(range(6, 78)); length = max(e.core.length for e in elements)
    scales = np.ones(78)
    for node in range(5): scales[6*node+3:6*node+6] = length
    for first in (30, 54):
        scales[first:first+6] = length
        scales[first+6:first+12] = length
    def safe(record):
        if monotonic()-start > 120: raise RuntimeError('two-macro probe deadline')
        checkpoint(record)
    def assemble(state, parameter):
        r = np.zeros(78); h = np.zeros((78, 78))
        sx, sl, sq, su, sp = state
        for i, probe in enumerate(probes):
            ns = slice(2*i, 2*i+3)
            out = probe.evaluate(sx[ns], sl[ns], sq[ns], su[i], sp[i])
            r[slots[i]] += out.residual; h[np.ix_(slots[i], slots[i])] += out.hessian
        r[24:27] -= parameter*force
        scaled = r/scales
        metrics = (float(np.linalg.norm(scaled[equilibrium])),
                   float(np.linalg.norm(scaled[compatibility])))
        return r, h, metrics
    def update(state, step):
        sx, sl, sq, su, sp = [v.copy() for v in state]
        for node in range(5):
            for axis in range(3):
                sx[node, axis], sl[node, axis] = split_sum((float(sx[node, axis]),
                    float(sl[node, axis]), float(step[6*node+axis])))
            angular = step[6*node+3:6*node+6]
            if np.linalg.norm(angular) >= .9*np.pi: raise ValueError('probe nodal step requires cutback')
            sq[node] = rotation(angular)@sq[node]
        for i, first in enumerate((30, 54)):
            for cell in (0, 1):
                v = step[first+3*cell:first+3*cell+3]
                if np.linalg.norm(v) >= .9*np.pi: raise ValueError('probe step requires cutback')
                su[i, cell] = rotation(v)@su[i, cell]
            sp[i] += step[first+6:first+24]
        return sx, sl, sq, su, sp
    state = (x, low, q, u, p); records = []
    for parameter in (.5, 1.):
        for iteration in range(13):
            r, h, metrics = assemble(state, parameter)
            safe(dict(parameter=parameter, iteration=iteration,
                      equilibrium=metrics[0], compatibility=metrics[1]))
            if max(metrics) <= 1e-11:
                records.append(dict(parameter=parameter, iterations=iteration,
                    equilibrium=metrics[0], compatibility=metrics[1]))
                break
            if iteration == 12: raise RuntimeError('two-macro probe Newton limit')
            step = np.zeros(78)
            step[free] = np.linalg.solve(h[np.ix_(free, free)], -r[free])
            if not np.isfinite(step).all(): raise ValueError('finite probe step required')
            for cut in range(9):
                trial = update(state, step*(.5**cut))
                _, _, changed = assemble(trial, parameter)
                if max(changed) < max(metrics):
                    state = trial; break
            else: raise RuntimeError('two-macro probe line search limit')
        else: raise RuntimeError('two-macro probe incomplete target')
    return state, records
