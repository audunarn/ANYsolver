"""One flat Q4 and physical B2 member joined by the existing F10 point law.

This is a bounded reference-linear experiment.  The six constraint rows are
compiled by F10/F11; this module only owns sparse assembly, affine reduction,
the solve, and physical equilibrium output.  It makes no line or footprint,
dynamic, stability, nonlinear or qualification claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite

import numpy as np
from scipy import sparse

from ._b2_f10_f11_point_attachment import LAW_ID, compile_reference_point
from ._b2_physical_linear_definition import (
    PROFILE_ID, CompiledPhysicalB2Member, PhysicalB2Member,
)
from .e4_pl_element import QualifiedE4PLShellElement
from .fe_core import FEModel
from .linalg import MatrixClass, factorize_cached


class ExperimentalB2Q4PointError(RuntimeError):
    """The bounded point-coupled reference-linear problem cannot be used."""


class _NumericalFailure(RuntimeError):
    """A sparse solve or checked mixed equilibrium failed."""


@dataclass(frozen=True)
class ExperimentalB2Q4PointCapabilities:
    profile_id: str = PROFILE_ID
    point_law_id: str = LAW_ID
    status: str = "experimental"
    production_qualified: bool = False
    shell_domain: str = "one flat elastic Q4"
    beam_domain: str = "one physical B2 member"
    attachment: str = "one F10 reference point"
    operations: tuple[str, ...] = ("solve_linear", "close")


@dataclass(frozen=True)
class ExperimentalB2Q4PointResult:
    status: str
    displacements: tuple[float, ...] = ()
    multiplier: tuple[float, ...] = ()
    affine_reactions: tuple[float, ...] = ()
    point_gap: tuple[float, ...] = ()
    beam_resultants_local: tuple[tuple[float, ...], ...] = ()
    internal_strain_energy: float | None = None
    factorization_count: int | None = None
    solve_count: int | None = None
    failure_reason: str | None = None
    production_qualified: bool = False


class ExperimentalB2Q4PointAnalysis:
    """Compiled 36-coordinate Q4/B2 point system with six algebraic rows.

    The coordinate order is four shell vertices followed by two B2 member
    nodes, with six global translations/rotations per node.  Callers supply
    an audited affine plan ``u=T q+u0`` in that exact order. Returned affine
    reactions include all forces in the null space of ``T.T``; they are support
    reactions only for a pure fixed-coordinate plan.
    """

    def __init__(self, member: PhysicalB2Member | CompiledPhysicalB2Member,
                 shell_vertices_m, *, shell_E: float, shell_nu: float,
                 shell_thickness_m: float, station: float,
                 transformation: sparse.spmatrix, prescribed_offset,
                 offset_local_m=(0., 0., 0.), reference_normal=(0., 0., 1.)):
        if isinstance(member, CompiledPhysicalB2Member):
            compiled = member
            definition = member.definition
        elif isinstance(member, PhysicalB2Member):
            definition = member
            compiled = member.compile_local()
        else:
            raise ValueError("physical B2 member required")
        vertices = np.array(shell_vertices_m, dtype=float, copy=True)
        if vertices.shape != (4, 3) or not np.isfinite(vertices).all():
            raise ValueError("four finite Q4 shell vertices required")
        model = FEModel("experimental-B2-Q4-point")
        model.add_material("shell", shell_E, shell_nu)
        for index, point in enumerate(vertices, 1):
            model.add_node(index, *point)
        shell = QualifiedE4PLShellElement(
            1, (1, 2, 3, 4), "shell", thickness=shell_thickness_m,
            reference_normal=np.asarray(reference_normal, dtype=float))
        model.add_element(1, shell)
        shell_k = shell.compute_stiffness_matrix(
            model.mesh, model.get_material("shell"))
        if shell_k.shape != (24, 24) or not np.isfinite(shell_k).all():
            raise ExperimentalB2Q4PointError("finite physical Q4 stiffness required")
        frame = compiled.local_dof_map()
        beam_k = frame.T @ compiled.operator.evaluate(np.zeros(12)).tangent @ frame
        if beam_k.shape != (12, 12) or not np.isfinite(beam_k).all():
            raise ExperimentalB2Q4PointError("finite physical B2 stiffness required")
        law = compile_reference_point(
            definition, vertices, station=station,
            offset_local_m=offset_local_m)
        try:
            T = transformation.tocsr(copy=True)
            u0 = np.array(prescribed_offset, dtype=float, copy=True)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("finite sparse Q4/B2 affine plan required") from exc
        if (T.shape[0] != 36 or T.shape[1] <= 6 or
                u0.shape != (36,) or not np.isfinite(T.data).all() or
                not np.isfinite(u0).all()):
            raise ValueError("finite sparse Q4/B2 affine plan required")
        K = sparse.block_diag((shell_k, beam_k), format="csr")
        C = sparse.csr_matrix(law.constraint)
        reduced_k = (T.T @ K @ T).tocsc()
        reduced_c = (C @ T).tocsc()
        if np.linalg.matrix_rank(reduced_c.toarray()) != 6:
            raise ValueError("six independent supported point rows required")
        kkt = sparse.bmat(
            ((reduced_k, reduced_c.T), (reduced_c, None)),
            format="csc")
        handle = factorize_cached(kkt, MatrixClass.SYMMETRIC_INDEFINITE)
        if handle.status != "ok":
            raise ExperimentalB2Q4PointError(
                "Q4/B2 point factorization failed: " + str(handle.failure_reason))
        self._member = compiled
        self._law = law
        self._K = K
        self._C = C
        self._T = T
        self._u0 = u0
        self._ku0 = np.asarray(K @ u0).reshape(-1)
        self._cu0 = np.asarray(C @ u0).reshape(-1)
        self._handle = handle
        self._closed = False

    @property
    def capabilities(self) -> ExperimentalB2Q4PointCapabilities:
        return ExperimentalB2Q4PointCapabilities()

    def solve_linear(self, load) -> ExperimentalB2Q4PointResult:
        if self._closed:
            raise ExperimentalB2Q4PointError("experimental Q4/B2 point analysis is closed")
        try:
            applied = np.array(load, dtype=float, copy=True)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("finite 36-coordinate Q4/B2 load required") from exc
        if applied.shape != (36,) or not np.isfinite(applied).all():
            raise ValueError("finite 36-coordinate Q4/B2 load required")
        rhs = np.r_[np.asarray(self._T.T @ (applied-self._ku0)).reshape(-1),
                    -self._cu0]
        try:
            answer = np.asarray(self._handle.solve(rhs), dtype=float)
        except RuntimeError as exc:
            return ExperimentalB2Q4PointResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        try:
            if answer.shape != rhs.shape or not np.isfinite(answer).all():
                raise _NumericalFailure("finite Q4/B2 point solution required")
            q, lam = answer[:-6], answer[-6:]
            displacement = np.asarray(self._T @ q).reshape(-1) + self._u0
            gap = np.asarray(self._C @ displacement).reshape(-1)
            reaction = np.asarray(self._K @ displacement +
                                  self._C.T @ lam - applied).reshape(-1)
            if (not np.isfinite(displacement).all() or
                    not np.isfinite(gap).all() or not np.isfinite(reaction).all()):
                raise _NumericalFailure("finite Q4/B2 point recovery required")
            # Preserve numerical non-success; a finite solve alone is not an
            # equilibrium or constraint pass.
            internal_force = np.asarray(self._K @ displacement).reshape(-1)
            reduced_reaction = np.asarray(self._T.T @ reaction).reshape(-1)
            force_scale = max(1., hypot(*applied), hypot(*internal_force))
            motion_scale = max(1., hypot(*displacement))
            if (not isfinite(force_scale) or not isfinite(motion_scale) or
                    not np.isfinite(reduced_reaction).all() or
                    hypot(*gap) > 1e-9*motion_scale or
                    hypot(*reduced_reaction) > 1e-9*force_scale):
                raise _NumericalFailure("Q4/B2 point equilibrium or gap failed")
        except _NumericalFailure as exc:
            return ExperimentalB2Q4PointResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count, failure_reason=str(exc))
        local = self._member.local_dof_map() @ displacement[24:]
        if not np.isfinite(local).all():
            return ExperimentalB2Q4PointResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count,
                failure_reason="finite Q4/B2 local recovery coordinates required")
        recovered = self._member.operator.recover_sections(
            local, stations=(0., .5, 1.))
        energy = .5*float(displacement @ (self._K @ displacement))
        if (not isfinite(energy) or
                not np.isfinite(recovered.resultants).all() or
                not np.isfinite(recovered.strains).all()):
            return ExperimentalB2Q4PointResult(
                "failed", factorization_count=self._handle.factorization_count,
                solve_count=self._handle.solve_count,
                failure_reason="finite Q4/B2 physical recovery required")
        return ExperimentalB2Q4PointResult(
            "completed", tuple(map(float, displacement)), tuple(map(float, lam)),
            tuple(map(float, reaction)), tuple(map(float, gap)),
            tuple(tuple(map(float, row)) for row in recovered.resultants),
            energy, self._handle.factorization_count, self._handle.solve_count)

    def close(self) -> None:
        self._closed = True
        self._handle = None


def create_experimental_b2_q4_point_analysis(*args, **kwargs):
    return ExperimentalB2Q4PointAnalysis(*args, **kwargs)
