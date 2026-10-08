"""Bounded native B3/E4 linear rigid-footprint comparator for G0 F04.

The four shell material nodes and the shared native B3 nodal pose match the
declared *connection geometry* of the external knot-footprint model. This
does not match its B31 section torsion law or qualify a nonlinear owner.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import (SECTION_DIAGONAL, Fixture,
                                                build)
from scripts._b3_e4_f03_native_spatial_port import NativeNodalSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_trace import make_shell


SAMPLES = ((.25, -.25), (.75, -.25), (.75, .25), (.25, .25))
BEAM_OFFSET_M = .1


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


@dataclass(frozen=True)
class FootprintReference:
    shell: FlatE4TrialPanel
    beam: Fixture
    port: NativeNodalSpatialPort
    shell_nodes: tuple[int, ...]
    sample_offsets: np.ndarray
    primal_tangent: np.ndarray
    constraint_jacobian: np.ndarray
    free_primal: np.ndarray
    scaled_system: np.ndarray
    coordinate_scale: np.ndarray
    energy_scale: float


def assemble(topology: str = "Q4", n_half_cells: int = 4) -> FootprintReference:
    """Linearize the physical rigid-region point constraints at virgin state."""
    if topology not in ("Q4", "S3-V2D"):
        raise ValueError("bounded Q4 or S3 footprint required")
    shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
    beam = build(n_half_cells, z_offset=BEAM_OFFSET_M)
    port = NativeNodalSpatialPort(beam.context, n_half_cells // 2)
    shell_reference = reference_nodes(shell.panel)
    bh, bl, frame = port.pose_pair(beam.context.initial.mechanical)
    center = bh + bl
    if (np.linalg.norm(center-(.5, 0., BEAM_OFFSET_M)) > 1e-14 or
            np.linalg.norm(frame-np.eye(3)) > 1e-14):
        raise ValueError("unexpected native footprint reference pose")
    nodes = []
    offsets = []
    for x, y in SAMPLES:
        found = np.flatnonzero(np.linalg.norm(
            shell_reference-np.array((x, y, 0.)), axis=1) < 1e-14)
        if len(found) != 1:
            raise ValueError("rigid footprint sample is not one shell node")
        node = int(found[0])
        nodes.append(node)
        offsets.append(shell_reference[node]-center)
    shell_size = 6*shell.panel.node_count
    count = shell_size+beam.context.count
    primal = np.zeros((count, count))
    primal[:shell_size, :shell_size] = shell.evaluate(
        np.zeros(shell_size), .5).tangent
    primal[shell_size:, shell_size:] = beam.tangent.toarray()
    constraint = np.zeros((12, count))
    beam_tangent = port.tangent(beam.context.initial.mechanical)
    for i, (node, offset) in enumerate(zip(nodes, offsets)):
        constraint[3*i:3*i+3, 6*node:6*node+3] = np.eye(3)
        constraint[3*i:3*i+3, shell_size:] = (
            np.column_stack((-np.eye(3), _skew(offset))) @ beam_tangent)
    # Match CalculiX PanelEnds,1,3 and BeamRoot,1,6 exactly in meaning.
    nx = 2*shell.panel.n_s
    fixed_shell = {6*(j*(nx+1)+i)+axis
                   for j in range(shell.panel.n_y+1)
                   for i in (0, nx) for axis in range(3)}
    fixed_beam = {shell_size+index for index in beam.context.fixed}
    free = np.array([i for i in range(count)
                     if i not in fixed_shell and i not in fixed_beam], dtype=int)
    rows = constraint[:, free]
    # Each row owns a distinct unconstrained shell translation column with
    # coefficient one. This proves algebraic row independence without using
    # a mixed-unit singular-value threshold as a stability claim.
    if (len(set(nodes)) != 4 or any(
            6*node+axis in fixed_shell for node in nodes for axis in range(3))):
        raise ValueError("rigid footprint sample is fixed or repeated")
    kkt = np.block([[primal[np.ix_(free, free)], rows.T],
                    [rows, np.zeros((12, 12))]])
    force_scale = 1e6
    displacement_scale = force_scale/(210e9*shell.panel.thickness)
    nodal_scale = np.tile(np.r_[np.full(3, displacement_scale),
                                np.full(3, displacement_scale)],
                          shell.panel.node_count+beam.context.nodal_count//6)
    resultants = np.r_[np.tile(SECTION_DIAGONAL[:3]*displacement_scale, 2),
                       np.tile(SECTION_DIAGONAL[3:]*displacement_scale, 4)]
    retained_scale = np.tile(np.r_[np.full(6, displacement_scale),
                                    resultants], beam.n_half_cells//2)
    full_scale = np.r_[nodal_scale, retained_scale]
    if len(full_scale) != count:
        raise ValueError("native retained footprint scale layout changed")
    coordinate_scale = np.r_[full_scale[free], np.full(12, force_scale)]
    energy_scale = force_scale*displacement_scale
    scaled = ((coordinate_scale[:, None]*kkt)*coordinate_scale[None, :]
              )/energy_scale
    return FootprintReference(shell, beam, port, tuple(nodes),
                              np.asarray(offsets), primal, constraint,
                              free, scaled, coordinate_scale, energy_scale)


def solve(reference: FootprintReference, *, mx_nm: float = 100.) -> dict:
    """Solve the bounded tip-torque case with the actual retained B3 block."""
    if not np.isfinite(mx_nm):
        raise ValueError("finite physical tip torque required")
    shell_size = 6*reference.shell.panel.node_count
    load = np.zeros(reference.primal_tangent.shape[0])
    load[shell_size+6*reference.beam.n_half_cells+3] = mx_nm
    free = reference.free_primal
    rhs = np.r_[load[free]*reference.coordinate_scale[:len(free)]/
                reference.energy_scale, np.zeros(12)]
    scaled_solution = linalg.solve(reference.scaled_system, rhs,
                                   assume_a="gen", check_finite=True)
    physical = reference.coordinate_scale*scaled_solution
    full = np.zeros(len(load))
    full[free] = physical[:len(free)]
    multipliers = physical[len(free):]
    residual = (reference.primal_tangent@full+
                reference.constraint_jacobian.T@multipliers-load)
    shell_nodes = reference_nodes(reference.shell.panel)
    shell_reaction = residual[:shell_size].reshape(-1, 6)
    shell_force = shell_reaction[:, :3].sum(axis=0)
    shell_moment = (shell_reaction[:, 3:]+np.cross(
        shell_nodes, shell_reaction[:, :3])).sum(axis=0)
    beam_reaction = residual[shell_size:shell_size+6]
    total_force = shell_force+beam_reaction[:3]
    total_moment = (shell_moment+beam_reaction[3:]+np.cross(
        np.array((0., 0., BEAM_OFFSET_M)), beam_reaction[:3]))
    shell_interface = (reference.constraint_jacobian[:, :shell_size].T@
                       multipliers).reshape(-1, 6)
    interface_moment = (shell_interface[:, 3:]+np.cross(
        shell_nodes, shell_interface[:, :3])).sum(axis=0)
    gap = reference.constraint_jacobian@full
    return {
        "topology": reference.shell.panel.topology,
        "native_half_cells": reference.beam.n_half_cells,
        "tip_rx_rad": float(full[shell_size+6*reference.beam.n_half_cells+3]),
        "shell_force_n": shell_force.tolist(),
        "shell_moment_origin_nm": shell_moment.tolist(),
        "beam_root_wrench": beam_reaction.tolist(),
        "total_force_n": total_force.tolist(),
        "total_moment_origin_nm": total_moment.tolist(),
        "shell_interface_moment_origin_nm": interface_moment.tolist(),
        "scaled_equation_residual": float(np.linalg.norm(
            reference.scaled_system@scaled_solution-rhs)),
        "weak_gap_norm_m": float(np.linalg.norm(gap)),
        "external_work_j": float(load@full),
        "quadratic_internal_work_j": float(full@reference.primal_tangent@full),
        "scope": "linear native rigid footprint; external B31 section unmatched",
    }
