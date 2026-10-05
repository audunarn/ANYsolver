"""Bounded row-dependence audit for the already-loaded P0 aligned cases.

Rank detects algebraic loss only. These singular values are not an inf-sup
constant, a physical compliance norm, or a multiplier-space selection rule.
"""

import json

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)


def row_inventory(matrix):
    singular = linalg.svdvals(matrix, check_finite=True)
    cutoff = 1e-10*singular[0]
    return {"rows": matrix.shape[0],
            "rank_at_relative_1e_minus_10": int(np.count_nonzero(singular > cutoff)),
            "smallest_over_largest": float(singular[-1]/singular[0])}


def main():
    shell = FlatE4TrialPanel(make_shell(8, "Q4", n_y=8))
    beam = build(32)
    output = []
    for intervals in (8, 16):
        space = LineMultiplierSpace(
            "piecewise_constant", tuple(np.linspace(0., 1., intervals+1)))
        kkt = assemble_reference_kkt(
            shell, beam, space, shell_port="local_translation",
            shell_support_policy="full_left_edge")
        free = kkt.free_primal
        shell_size = 6*shell.panel.node_count
        rows = kkt.constraint_jacobian[:, free]
        # Fixed 1 m moment-to-force length and the existing frozen primal
        # coordinate scales are used only to expose numerical row dependence.
        channel = np.tile([1., 1., 1., 1., 1., 1.], intervals)
        scaled = channel[:, None]*rows*kkt.coordinate_scale[:len(free)][None, :]
        nshell = int(np.count_nonzero(free < shell_size))
        transverse = np.array([6*i+j for i in range(intervals)
                               for j in (2, 3, 4)])
        output.append({"topology": "Q4", "shell_x_hosts": 16,
                       "shell_y_hosts": 8, "native_half_cells": 32,
                       "p0_intervals": intervals,
                       "whole": row_inventory(scaled),
                       "shell_only": row_inventory(scaled[:, :nshell]),
                       "beam_only": row_inventory(scaled[:, nshell:]),
                       "transverse_whole": row_inventory(scaled[transverse]),
                       "transverse_shell_only": row_inventory(
                           scaled[transverse, :nshell]),
                       "transverse_beam_only": row_inventory(
                           scaled[transverse, nshell:])})
    print(json.dumps({"purpose": "UNREGISTERED_P0_ALIGNED_ROW_DEPENDENCE",
                      "not_inf_sup_or_selection": True, "cases": output},
                     sort_keys=True))


if __name__ == "__main__":
    main()
