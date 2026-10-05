"""Whole-model wrench recovery for the zero-director radial fixture.

This checks saved vectors, not equilibrium by solving again. Every node enters
once, including both ends of MPCs and prescribed-path actuators. Rotations must
be exactly zero: this helper does not turn finite-rotation generalized forces
into physical couples. The caller supplies the complete free displacement map
after structural constraints AND path controls, and physical contact wrench
from skin work before constraint reduction, already about the supplied origin.
"""
from __future__ import annotations

import numpy as np
from scipy import linalg


def guided_wrench_diagnostics(model, displacement, structural_internal,
                             contact_internal, external, free_map, *,
                             physical_contact_force, physical_contact_moment,
                             origin=(.6, .6, 0.), force_scale_n=.08,
                             moment_scale_nm=.08, bodies=None):
    size = model.mesh.dof_manager.total_dofs
    arrays = [np.asarray(v, dtype=float).reshape(-1) for v in
              (displacement, structural_internal, contact_internal, external)]
    if any(a.size != size or not np.isfinite(a).all() for a in arrays):
        raise ValueError("complete finite authoritative coordinate vectors required")
    u, structural, contact, load = arrays
    origin = np.asarray(origin, dtype=float)
    physical_force = np.asarray(physical_contact_force, dtype=float)
    physical_moment = np.asarray(physical_contact_moment, dtype=float)
    if (origin.shape != (3,) or physical_force.shape != (3,)
            or physical_moment.shape != (3,)
            or not np.isfinite(np.r_[origin, physical_force, physical_moment]).all()
            or not np.isfinite([force_scale_n, moment_scale_nm]).all()
            or min(force_scale_n, moment_scale_nm) <= 0):
        raise ValueError("finite wrench/origin and positive dimensional scales required")
    rows, positions = [], []
    for node_id, node in model.mesh.nodes.items():
        dofs = np.asarray(model.mesh.dof_manager.get_node_dofs(node_id))
        if (dofs.size != 6 or np.any(dofs < 0) or np.any(dofs >= size)
                or not np.issubdtype(dofs.dtype, np.integer)):
            raise ValueError("six valid authoritative nodal coordinate indices required")
        if np.any(u[dofs[3:]] != 0.):
            raise ValueError("six Cartesian coordinates with exactly zero rotations required")
        rows.append(dofs)
        positions.append(np.array((node.x, node.y, node.z))+u[dofs[:3]])
    rows = np.asarray(rows)
    if rows.size != size or np.unique(rows).size != size:
        raise ValueError("nodal coordinates must cover authoritative coordinates exactly once")
    lever = np.asarray(positions)-origin

    def wrench(vector, selection=None):
        nodal = vector[rows]
        arms = lever
        if selection is not None:
            nodal, arms = nodal[selection], arms[selection]
        return np.r_[np.sum(nodal[:, :3], axis=0),
                     np.sum(np.cross(arms, nodal[:, :3])+nodal[:, 3:], axis=0)]

    # b acts ON the model. Subtracting path multipliers here would omit their
    # physical action. Project onto the joint constraint/control row space.
    b = structural+contact-load
    free = np.asarray(free_map, dtype=float)
    if (free.ndim != 2 or free.shape[0] != size or free.shape[1] > size
            or not np.isfinite(free).all()):
        raise ValueError("complete finite joint free-coordinate map required")
    if np.any(free[rows[:, 3:].ravel()] != 0.):
        raise ValueError("guided free variations must have exactly zero rotation")
    if free.shape[1]:
        q, r = linalg.qr(free, mode="economic")
        if np.min(abs(np.diag(r))) <= 1e-12*np.linalg.norm(r, 2):
            raise ValueError("joint free-coordinate map must have full column rank")
        equilibrium_error = q @ (q.T @ b)
    else:
        equilibrium_error = np.zeros(size)
    reaction = b-equilibrium_error
    reaction_wrench = wrench(reaction)
    load_wrench = wrench(load)
    structural_wrench = wrench(structural)
    mapped_contact = -wrench(contact)
    physical_contact = np.r_[physical_force, physical_moment]
    balance = reaction_wrench+load_wrench+physical_contact
    conversion = mapped_contact-physical_contact
    scales = np.array([force_scale_n]*3+[moment_scale_nm]*3)
    result = dict(
        scope="zero-rotation guided Cartesian nodal work; all constraint/path actions",
        origin_m=origin.tolist(), force_scale_n=force_scale_n,
        moment_scale_nm=moment_scale_nm,
        total_reaction_wrench=reaction_wrench.tolist(),
        external_wrench=load_wrench.tolist(),
        physical_contact_wrench=physical_contact.tolist(),
        structural_internal_wrench=structural_wrench.tolist(),
        mapped_to_physical_contact_defect=conversion.tolist(),
        total_balance_defect=balance.tolist(),
        free_equilibrium_residual_n=float(np.linalg.norm(equilibrium_error)),
        constraint_reconstruction_relative_force=float(np.linalg.norm(equilibrium_error)/force_scale_n),
        balance_relative_force=float(np.linalg.norm(balance[:3])/force_scale_n),
        balance_relative_moment=float(np.linalg.norm(balance[3:])/moment_scale_nm),
        contact_conversion_max_scaled=float(np.max(abs(conversion)/scales)),
        structural_internal_max_scaled=float(np.max(abs(structural_wrench)/scales)))
    if bodies is not None:
        # Recover the joint constrained reaction ONCE, then partition nodal
        # work by body. Separate body checks prevent cancellation of errors.
        node_order = tuple(model.mesh.nodes)
        selected, body_results = set(), {}
        for name, body in bodies.items():
            ids = tuple(body['node_ids'])
            if (not isinstance(name, str) or not name or not ids
                    or len(set(ids)) != len(ids)
                    or not set(ids) <= set(node_order)
                    or selected & set(ids)):
                raise ValueError('bodies require distinct disjoint model node selections')
            selected.update(ids)
            selection = [i for i, node in enumerate(node_order) if node in set(ids)]
            physical = np.r_[np.asarray(body['physical_contact_force'], dtype=float),
                             np.asarray(body['physical_contact_moment'], dtype=float)]
            if physical.shape != (6,) or not np.isfinite(physical).all():
                raise ValueError('each body requires its finite physical wrench about origin')
            body_reaction, body_load = wrench(reaction, selection), wrench(load, selection)
            body_structural = wrench(structural, selection)
            body_conversion = -wrench(contact, selection)-physical
            body_balance = body_reaction+body_load+physical
            body_results[name] = dict(
                node_ids=list(ids), total_reaction_wrench=body_reaction.tolist(),
                external_wrench=body_load.tolist(), physical_contact_wrench=physical.tolist(),
                structural_internal_wrench=body_structural.tolist(),
                mapped_to_physical_contact_defect=body_conversion.tolist(),
                total_balance_defect=body_balance.tolist(),
                balance_relative_force=float(np.linalg.norm(body_balance[:3])/force_scale_n),
                balance_relative_moment=float(np.linalg.norm(body_balance[3:])/moment_scale_nm),
                contact_conversion_max_scaled=float(np.max(abs(body_conversion)/scales)),
                structural_internal_max_scaled=float(np.max(abs(body_structural)/scales)))
        if selected != set(node_order):
            raise ValueError('body selections must cover every model node exactly once')
        result['bodies'] = body_results
    return result
