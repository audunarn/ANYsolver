"""Signed physical residual fields for the bounded classical F03 Qp model.

The shell field is piecewise polynomial and has interior traction jumps.
The beam distribution is transferred over the four finite pad areas. This
module combines both without interpreting a jump as a material load.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_primal_ritz import F0
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_nodal_recovery import assemble_area_nodal_load
from scripts._b3_e4_f03_qp_shell_recovery import PiecewiseQpShellRecovery


@dataclass(frozen=True)
class SignedSpatialWork:
    cell: float
    support: float
    free: float
    interior: float

    @property
    def total(self) -> float:
        """Beam/pad virtual work minus shell internal virtual work."""
        return self.cell+self.support+self.free+self.interior

    @property
    def reaction(self) -> float:
        """Shell internal minus beam/pad work on this virtual lifting."""
        return -self.total


class SpatialQpRecovery:
    """Expose cell, boundary, and jump fields with signed work channels."""

    def __init__(self, adjoint: FinitePadAreaAdjoint,
                 *, x_order: int | None = None,
                 comparison_order: int | None = None):
        if not isinstance(adjoint, FinitePadAreaAdjoint):
            raise TypeError("physical finite-pad adjoint required")
        x_order = adjoint.trace.p+5 if x_order is None else x_order
        comparison_order = x_order+2 if comparison_order is None else comparison_order
        if comparison_order <= x_order:
            raise ValueError("higher area comparison order required")
        load, wrench = assemble_area_nodal_load(adjoint, x_order=x_order)
        comparison, comparison_wrench = assemble_area_nodal_load(
            adjoint, x_order=comparison_order)
        scale = max(F0, float(np.max(np.abs(comparison))))
        wrench_scale = max(F0, float(np.max(np.abs(comparison_wrench))))
        self.area_order_error = max(
            float(np.max(np.abs(load-comparison)))/scale,
            float(np.max(np.abs(wrench-comparison_wrench)))/wrench_scale)
        if (not np.isfinite(self.area_order_error) or
                self.area_order_error > 2e-10):
            raise ValueError("finite-pad area quadrature has not settled")
        load = np.array(load, copy=True)
        load.setflags(write=False)
        self.adjoint = adjoint
        self.area_nodal_load = load
        self.area_wrench = np.array(wrench, copy=True)
        self.area_wrench.setflags(write=False)
        self.shell = PiecewiseQpShellRecovery(adjoint.trace)
        self.coefficients = self.shell.coefficients(adjoint.q)

    def cell(self, i: int, k: int, x: float, y: float) -> dict[str, np.ndarray]:
        """Physical displacement, T, div T, area load and r_K at a point."""
        displacement, strain, resultant, divergence = self.shell.state(
            self.coefficients, i, k, x, y)
        area_force = self.adjoint.area_force(x, y)
        return {
            "displacement": displacement,
            "strain": strain,
            "resultant": resultant,
            "divergence": divergence,
            "area_force": area_force,
            "residual": divergence+area_force,
        }

    def outer_traction(self, axis: str, side: int, cell: int,
                       coordinate: float) -> np.ndarray:
        """Outward supported or free shell-edge traction."""
        return self.shell.outer_traction(
            self.coefficients, axis, side, cell, coordinate)

    def interior_jump(self, axis: str, edge: int, cell: int,
                      coordinate: float) -> np.ndarray:
        """Sum of two opposing cell-outward tractions on one edge."""
        return self.shell.interior_jump(
            self.coefficients, axis, edge, cell, coordinate)

    def work(self, virtual: np.ndarray) -> SignedSpatialWork:
        """Integrate checked area residual, outer tractions and jumps."""
        z = np.asarray(virtual, dtype=float)
        if (z.shape != self.area_nodal_load.shape or
                not np.isfinite(z).all()):
            raise ValueError("invalid bounded virtual shell field")
        shell = self.shell.integration_by_parts(self.adjoint.q, z)
        return SignedSpatialWork(
            cell=float(self.area_nodal_load@z-shell.volume),
            support=-shell.support,
            free=-shell.free,
            interior=-shell.interior,
        )
