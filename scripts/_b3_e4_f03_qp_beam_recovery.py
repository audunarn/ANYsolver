"""Bounded classical F03 Qp beam-side interface recovery.

The output is the distribution acting on the mapped physical pose. It has
an ordinary line density and two endpoint atoms; shell-side equilibrium and
spatial residuals are outside this module. The represented finite-pad J is
owned by the supplied trace, including its rigid-yaw gain.
"""

from __future__ import annotations

import math

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0, SECTION


def _side(station: float, requested: str) -> str:
    if requested not in ("left", "right"):
        raise ValueError("one-sided derivative choice required")
    # The beam has only an interior limit at either endpoint.
    return "right" if station == 0. else "left" if station == 1. else requested


def recover_interface(
    trace: FinitePadQpTrace,
    q: np.ndarray,
    eta: np.ndarray,
    stations: np.ndarray,
    *,
    sides: str | tuple[str, ...] = "right",
) -> dict[str, np.ndarray]:
    """Recover (N', Q'+load, M'+Q), root/tip atoms and root reaction.

    ``q`` contains both full shared-node fields (supported values may be
    zero); ``eta`` is the unscaled physical root multiplier. Interior
    crossing stations may select either one-sided density with ``sides``.
    The first pose derivative and section resultants are continuous there,
    so crossing stations carry no additional atom.
    """
    if not isinstance(trace, FinitePadQpTrace):
        raise TypeError("a finite-pad Qp trace is required")
    if (2*trace.n > 6014 or len(trace.free_columns) > 5890 or
            len(trace.station_intervals()) > 128):
        raise ValueError("outside bounded Qp reference recovery")
    q = np.asarray(q, dtype=float)
    eta = np.asarray(eta, dtype=float)
    stations = np.asarray(stations, dtype=float)
    if (q.shape != (2*trace.n,) or eta.shape != (3,) or
            stations.ndim != 1 or not np.isfinite(q).all() or
            not np.isfinite(eta).all() or not np.isfinite(stations).all() or
            np.any(stations < 0.) or np.any(stations > 1.)):
        raise ValueError("invalid physical Qp recovery state")
    selected = (tuple(sides for _ in stations) if isinstance(sides, str)
                else tuple(sides))
    if len(selected) != len(stations):
        raise ValueError("one side is required for each station")
    if any(side not in ("left", "right") for side in selected):
        raise ValueError("one-sided derivative choice required")

    ea, ei, ga = np.diag(SECTION)

    def section(station: float, side: str) -> tuple[np.ndarray, np.ndarray]:
        pose, first, second = (matrix@q for matrix in
            trace.matrices(station, side=_side(station, side)))
        nqm = np.array((ea*first[0], ga*(first[1]-pose[2]),
                        ei*first[2]))
        density = np.array((ea*second[0],
                            ga*(second[1]-first[2]) +
                                F0*(1.+.25*math.cos(2.*math.pi*station)),
                            ei*second[2]+nqm[1]))
        return nqm, density

    root, _ = section(0., "right")
    tip, _ = section(1., "left")
    density = np.array([section(float(station), side)[1]
                        for station, side in zip(stations, selected)],
                       dtype=float).reshape((-1, 3))
    return {
        "density": density,
        "root_atom": root-eta,
        "tip_atom": -tip,
        "root_reaction": -eta.copy(),
        "root_section_resultant": root.copy(),
        "tip_section_resultant": tip.copy(),
    }
