"""Small experimental two-Q4/two-B3 point-connected panel.

Run with an installed development build of ANYsolver. This exercises a
reference-linear integration slice; it is not a qualified stiffened-shell
example or a nonlinear response prediction.
"""

import json

import numpy as np

import anysolver
from anysolver import b3_ge
from anysolver.stiffened_shell import (
    B3_GE_E4_PL_STIFFENED_SHELL_V1, FixedCoordinate, LinearDefinition,
    NodalAction, PointConnection, ShellPanel,
)


def make_definition():
    young = 210e9
    shear = young/(2*(1+.3))
    section = b3_ge.EllipsoidalGeneralizedSection(
        np.diag((young*.01, shear*.008, shear*.008,
                 shear*1.6666666666666667e-5,
                 young*8.333333333333333e-6,
                 young*8.333333333333333e-6)),
        np.eye(6), 1e20, 1e9)
    beam_nodes = tuple((x, -.5, .1) for x in (0., .5, 1., 1.5, 2.))
    beams = tuple(b3_ge.define_beam(
        "b3-ge", index+1,
        (101+2*index, 102+2*index, 103+2*index),
        np.asarray(beam_nodes[2*index:2*index+3]),
        np.tile(np.eye(3), (3, 1, 1)), section, np.eye(6))
        for index in range(2))
    shell = ShellPanel(
        (1, 2, 3, 4, 5, 6),
        ((0., -.5, 0.), (1., -.5, 0.), (2., -.5, 0.),
         (0., .5, 0.), (1., .5, 0.), (2., .5, 0.)),
        ((1, 2, 5, 4), (2, 3, 6, 5)),
        .07, young, .3, 7850.)
    return LinearDefinition(
        B3_GE_E4_PL_STIFFENED_SHELL_V1, shell, beams,
        (PointConnection(1, 101), PointConnection(2, 103),
         PointConnection(3, 105)),
        tuple(FixedCoordinate("shell", node, component)
              for node in (1, 4) for component in range(6)))


def run():
    definition = make_definition()
    analysis = anysolver.stiffened_shell.create_analysis(definition=definition)
    first = analysis.solve_linear((NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),))
    saved = analysis.checkpoint()
    continued = b3_ge.create_stiffened_shell_analysis(
        formulation="b3-ge", definition=definition)
    continued.restore(saved)
    second = continued.solve_linear((NodalAction(
        "beam", 105, (0., 0., 200., 0., 0., 0.)),))
    return {
        "capabilities": analysis.capabilities,
        "preflight": analysis.preflight(),
        "first_tip_z_m": float(first.beam_coordinates[6*4+2]),
        "continued_tip_z_m": float(second.beam_coordinates[6*4+2]),
        "support_z_n": float(np.sum(first.reactions[:6*6].reshape(-1, 6)[:, 2])),
        "first_equilibrium_ratio": first.free_equilibrium_ratio,
        "first_constraint_max": first.constraint_max,
        "checkpoint_bytes": len(saved),
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, allow_nan=False))
