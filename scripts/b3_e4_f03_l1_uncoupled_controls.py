"""Matched shell-only Fy and native-beam-only torque refinement controls.

The Q4 and B3 reference geometry, material and root supports match the
three-level coupled L1 development screen. Removing the attachment is an
attribution diagnostic, not a substitute for a same-law coupled reference or
an external physical comparison. The native resultant block remains in its
actual stationary formulation until exact reduction.
"""

from __future__ import annotations

import json

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent


def evaluate(segments: int) -> dict:
    if type(segments) is not int or segments not in (2, 4, 8):
        raise ValueError("bounded whole-panel 2/4/8-edge controls required")
    xs = np.linspace(0., 1., 2*segments+1)
    ys = np.linspace(-.1, .1, segments+1)
    shell, shell_physical = raw_e4_tangent(xs, ys, thickness=.035)
    shell_count = shell.shape[0]
    beam = build(2*segments, z_offset=.0675)
    beam_count = beam.context.count
    if 8*(shell_count**2+beam_count**2) > 8*1024**3:
        raise ValueError("bounded control matrix resource ceiling exceeded")

    shell_free = np.array([
        j for j in range(shell_count) if (j//6) % len(xs) != 0], dtype=int)
    shell_load = np.zeros(shell_count)
    shell_tip_y = 6*((len(ys)//2)*len(xs)+len(xs)-1)+1
    shell_load[shell_tip_y] = 1000.
    shell_factor = linalg.cho_factor(
        shell[np.ix_(shell_free, shell_free)], lower=True,
        check_finite=True)
    shell_q = np.zeros(shell_count)
    shell_q[shell_free] = linalg.cho_solve(shell_factor,
                                            shell_load[shell_free])
    shell_residual = shell@shell_q-shell_load
    shell_error = float(np.linalg.norm(shell_residual[shell_free], ord=np.inf)/
                        max(1., np.linalg.norm(shell_load, ord=np.inf)))
    physical_work = float(shell_q@shell_physical@shell_q)
    completion_work = float(shell_q@(shell-shell_physical)@shell_q)
    shell_work = float(shell_load@shell_q)
    if abs(physical_work+completion_work-shell_work) > (
            1e-8*max(abs(shell_work), 1e-12)):
        raise AssertionError("shell-only physical/completion work does not sum")

    native = beam.tangent.toarray()
    native_free = np.asarray(beam.context.free, dtype=int)
    p = np.concatenate([
        beam.context.nodal_count+24*element+np.arange(6, 24)
        for element in range(len(beam.context.elements))])
    p_set = set(p)
    x = np.array([j for j in native_free if j not in p_set], dtype=int)
    if len(x)+len(p) != len(native_free):
        raise AssertionError("native physical/resultant partition differs")
    hxx = native[np.ix_(x, x)]
    hxp = native[np.ix_(x, p)]
    hpp = native[np.ix_(p, p)]
    negative_pp = linalg.cho_factor(-hpp, lower=True, check_finite=True)
    stationary = linalg.cho_solve(negative_pp, -hxp.T)
    kphysical = hxx-hxp@stationary
    physical_factor = linalg.cho_factor(kphysical, lower=True,
                                        check_finite=True)
    beam_load = np.zeros(beam_count)
    beam_tip_mx = 6*(2*segments)+3
    beam_load[beam_tip_mx] = 100.
    beam_q = np.zeros(beam_count)
    beam_q[x] = linalg.cho_solve(physical_factor, beam_load[x])
    beam_q[p] = -stationary@beam_q[x]
    beam_residual = native@beam_q-beam_load
    beam_error = float(np.linalg.norm(beam_residual[native_free], ord=np.inf)/
                       max(1., np.linalg.norm(beam_load, ord=np.inf)))
    beam_work = float(beam_load@beam_q)
    if abs(float(beam_q@native@beam_q)-beam_work) > (
            1e-8*max(abs(beam_work), 1e-12)):
        raise AssertionError("native retained quadratic work does not sum")

    return {
        "segments_on_half_line": segments,
        "shell_grid_x_m": xs.tolist(), "shell_grid_y_m": ys.tolist(),
        "shell_nodes": len(xs)*len(ys),
        "native_half_cells": 2*segments,
        "shell_only_fy_tip_m": float(shell_q[shell_tip_y]),
        "shell_only_fy_load_displacement_work_Nm": shell_work,
        "shell_only_physical_work_Nm": physical_work,
        "shell_only_completion_work_Nm": completion_work,
        "native_only_torque_tip_twist_rad": float(beam_q[beam_tip_mx]),
        "native_only_torque_load_displacement_work_Nm": beam_work,
        "native_uniform_torsion_oracle_rad": float(100./SECTION_DIAGONAL[3]),
        "shell_free_equilibrium_relative": shell_error,
        "native_free_equilibrium_relative": beam_error,
        "scope": "uncoupled same-geometry attribution controls only",
    }


if __name__ == "__main__":
    print(json.dumps([evaluate(n) for n in (2, 4, 8)], indent=2))
