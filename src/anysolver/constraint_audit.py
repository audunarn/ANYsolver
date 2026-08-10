"""Auditable fixed-DOF and linear MPC constraint contracts.

ANYsolver deliberately supports a restricted affine constraint form::

    u_slave = sum(a_i * u_master_i) + value

Together with prescribed support values this form has a structural rank that
can be determined without a dense rank-revealing factorization: every valid
equation owns one distinct dependent DOF.  This module validates that contract,
preserves equation provenance, and provides a common post-solve residual check.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Real
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from .fe_core import FEModel


COEFFICIENT_ATOL = 1.0e-14
RESIDUAL_RTOL = 1.0e-10


@dataclass(frozen=True)
class ConstraintAuditIssue:
    """One stable, machine-readable constraint diagnostic."""

    code: str
    severity: str
    message: str
    origin: str = ""
    dof: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstraintEquation:
    """One normalized equation ``sum(coefficient * u[dof]) = value``."""

    dependent_dof: int
    coefficients: Tuple[Tuple[int, float], ...]
    value: float
    origin: str
    kind: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dependent_dof": int(self.dependent_dof),
            "coefficients": [
                {"dof": int(dof), "coefficient": float(coefficient)}
                for dof, coefficient in self.coefficients
            ],
            "value": float(self.value),
            "origin": self.origin,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class ConstraintAuditReport:
    """Integrity and structural-rank report for the active constraint system."""

    status: str
    total_dofs: int
    equation_count: int
    structural_rank: int
    redundant_equations: int
    independent_dofs: int
    fixed_dofs: int
    mpc_slave_dofs: int
    homogeneous: bool
    feasible: bool
    max_dependency_depth: int
    origin_counts: Dict[str, int]
    equations: Tuple[ConstraintEquation, ...]
    issues: Tuple[ConstraintAuditIssue, ...]

    @property
    def errors(self) -> Tuple[ConstraintAuditIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> Tuple[ConstraintAuditIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["equations"] = [equation.to_dict() for equation in self.equations]
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        payload["error_count"] = len(self.errors)
        payload["warning_count"] = len(self.warnings)
        return payload


@dataclass(frozen=True)
class _Equation:
    dependent: int
    coefficients: Dict[int, float]
    value: float
    origin: str
    kind: str


def _finite_number(value: Any) -> Optional[float]:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if np.isfinite(result) else None


def _dof_index(value: Any) -> Optional[int]:
    if isinstance(value, (bool, np.bool_)):
        return None
    try:
        integer = int(value)
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return integer if np.isfinite(numeric) and numeric == integer else None


def _collect_equations(model: "FEModel") -> Tuple[List[_Equation], List[ConstraintAuditIssue]]:
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    equations: List[_Equation] = []
    issues: List[ConstraintAuditIssue] = []

    for bc_index, bc in enumerate(model.boundary_conditions):
        name = str(getattr(bc, "name", f"boundary_{bc_index}"))
        origin = f"support:{name}"
        try:
            constrained = bc.get_constrained_dofs(model.mesh.dof_manager)
        except Exception as exc:
            issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"Cannot enumerate support constraints: {exc}", origin))
            continue
        for dof_raw, value_raw in constrained:
            dof = _dof_index(dof_raw)
            if dof is None:
                issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"Support has invalid DOF {dof_raw!r}.", origin))
                continue
            value = _finite_number(value_raw)
            if not 0 <= dof < total_dofs:
                issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"Support DOF {dof} is outside [0, {total_dofs}).", origin, dof))
                continue
            if value is None:
                issues.append(ConstraintAuditIssue("CONSTRAINT004", "error", f"Support DOF {dof} has a non-finite prescribed value.", origin, dof))
                continue
            equations.append(_Equation(dof, {}, value, origin, "support"))

    for element_id, element in model.mesh.elements.items():
        getter = getattr(element, "get_mpc_constraints", None)
        if getter is None:
            continue
        try:
            constraints = getter(model.mesh) or ()
        except Exception as exc:
            origin = f"mpc:element:{int(element_id)}"
            issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"Cannot enumerate MPC constraints: {exc}", origin))
            continue
        for index, raw in enumerate(constraints):
            label = str(raw.get("label", f"constraint_{index}"))
            origin = f"mpc:{int(element_id)}:{label}"
            dependent = _dof_index(raw.get("slave"))
            if dependent is None:
                issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", "MPC has an invalid slave DOF.", origin))
                continue
            if not 0 <= dependent < total_dofs:
                issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"MPC slave DOF {dependent} is outside [0, {total_dofs}).", origin, dependent))
                continue
            value = _finite_number(raw.get("value", 0.0))
            if value is None:
                issues.append(ConstraintAuditIssue("CONSTRAINT004", "error", f"MPC slave DOF {dependent} has a non-finite affine value.", origin, dependent))
                continue
            masters: Dict[int, float] = {}
            valid = True
            raw_masters = raw.get("masters", {})
            if not isinstance(raw_masters, Mapping):
                issues.append(ConstraintAuditIssue("CONSTRAINT004", "error", "MPC masters must be a mapping.", origin, dependent))
                continue
            for master_raw, coefficient_raw in raw_masters.items():
                master = _dof_index(master_raw)
                if master is None:
                    issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"MPC has invalid master DOF {master_raw!r}.", origin, dependent))
                    valid = False
                    continue
                coefficient = _finite_number(coefficient_raw)
                if not 0 <= master < total_dofs:
                    issues.append(ConstraintAuditIssue("CONSTRAINT001", "error", f"MPC master DOF {master} is outside [0, {total_dofs}).", origin, master))
                    valid = False
                elif coefficient is None:
                    issues.append(ConstraintAuditIssue("CONSTRAINT004", "error", f"MPC coefficient for master DOF {master} is non-finite.", origin, master))
                    valid = False
                elif abs(coefficient) > COEFFICIENT_ATOL:
                    masters[master] = masters.get(master, 0.0) + coefficient
            masters = {dof: coefficient for dof, coefficient in masters.items() if abs(coefficient) > COEFFICIENT_ATOL}
            if dependent in masters:
                issues.append(ConstraintAuditIssue("CONSTRAINT003", "error", f"MPC slave DOF {dependent} references itself.", origin, dependent))
                valid = False
            if valid:
                equations.append(_Equation(dependent, masters, value, origin, "mpc"))

    return equations, issues


def audit_constraints(model: "FEModel") -> ConstraintAuditReport:
    """Audit fixed supports and affine MPCs without assembling FE matrices."""
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    equations, issues = _collect_equations(model)
    owners: Dict[int, _Equation] = {}
    redundant = 0

    for equation in equations:
        previous = owners.get(equation.dependent)
        if previous is None:
            owners[equation.dependent] = equation
            continue
        if previous.kind == equation.kind == "support" and np.isclose(previous.value, equation.value):
            redundant += 1
            issues.append(ConstraintAuditIssue("CONSTRAINT002", "warning", f"DOF {equation.dependent} has a duplicate prescribed constraint.", equation.origin, equation.dependent))
        else:
            issues.append(ConstraintAuditIssue("CONSTRAINT002", "error", f"DOF {equation.dependent} has multiple dependent definitions ({previous.origin}, {equation.origin}).", equation.origin, equation.dependent))

    mpc_by_slave = {dof: equation for dof, equation in owners.items() if equation.kind == "mpc"}
    visiting: Dict[int, int] = {}
    depths: Dict[int, int] = {}

    def visit(dof: int, path: Tuple[int, ...] = ()) -> int:
        state = visiting.get(dof, 0)
        if state == 1:
            cycle = path[path.index(dof):] + (dof,) if dof in path else path + (dof,)
            equation = mpc_by_slave[dof]
            issues.append(ConstraintAuditIssue("CONSTRAINT003", "error", f"Circular MPC dependency detected: {' -> '.join(map(str, cycle))}.", equation.origin, dof))
            return 0
        if state == 2:
            return depths[dof]
        visiting[dof] = 1
        equation = mpc_by_slave[dof]
        child_depths = [visit(master, path + (dof,)) for master in equation.coefficients if master in mpc_by_slave]
        depth = 1 + max(child_depths, default=0)
        depths[dof] = depth
        visiting[dof] = 2
        return depth

    for slave in mpc_by_slave:
        if visiting.get(slave, 0) == 0:
            visit(slave)

    error_count = sum(issue.severity == "error" for issue in issues)
    dependent_count = len(owners)
    fixed_count = sum(equation.kind == "support" for equation in owners.values())
    mpc_count = sum(equation.kind == "mpc" for equation in owners.values())
    homogeneous = all(abs(equation.value) <= COEFFICIENT_ATOL for equation in equations)
    origin_counts: Dict[str, int] = {}
    for equation in equations:
        origin_counts[equation.kind] = origin_counts.get(equation.kind, 0) + 1
    status = "invalid" if error_count else ("warning" if issues else "ok")
    normalized_equations = tuple(
        ConstraintEquation(
            dependent_dof=equation.dependent,
            coefficients=((equation.dependent, 1.0),)
            + tuple(sorted((master, -coefficient) for master, coefficient in equation.coefficients.items())),
            value=equation.value,
            origin=equation.origin,
            kind=equation.kind,
        )
        for equation in equations
    )
    return ConstraintAuditReport(
        status=status,
        total_dofs=total_dofs,
        equation_count=len(equations),
        structural_rank=dependent_count if not error_count else max(0, dependent_count),
        redundant_equations=redundant,
        independent_dofs=max(total_dofs - dependent_count, 0),
        fixed_dofs=fixed_count,
        mpc_slave_dofs=mpc_count,
        homogeneous=homogeneous,
        feasible=not bool(error_count),
        max_dependency_depth=max(depths.values(), default=0),
        origin_counts=origin_counts,
        equations=normalized_equations,
        issues=tuple(issues),
    )


def constraint_residual_summary(
    model: "FEModel",
    displacements: np.ndarray,
    *,
    homogeneous_variation: bool = False,
) -> Dict[str, Any]:
    """Return normalized support/MPC residuals for one vector or mode matrix."""
    values = np.asarray(displacements, dtype=float)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.ndim != 2:
        raise ValueError("constraint residual input must be a vector or 2D matrix")
    equations, collection_issues = _collect_equations(model)
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    if values.shape[0] != total_dofs:
        raise ValueError(f"constraint residual input has {values.shape[0]} rows; expected {total_dofs}")

    max_absolute = 0.0
    max_relative = 0.0
    worst_origin = ""
    residual_l2 = 0.0
    for equation in equations:
        prescribed = 0.0 if homogeneous_variation else equation.value
        residual = values[equation.dependent, :] - prescribed
        scale = np.maximum(np.abs(values[equation.dependent, :]), abs(prescribed))
        for master, coefficient in equation.coefficients.items():
            residual = residual - coefficient * values[master, :]
            scale = scale + abs(coefficient) * np.abs(values[master, :])
        absolute = float(np.max(np.abs(residual), initial=0.0))
        relative = float(np.max(np.abs(residual) / np.maximum(scale, 1.0), initial=0.0))
        residual_l2 += float(np.dot(residual, residual))
        if relative >= max_relative:
            max_relative = relative
            max_absolute = absolute
            worst_origin = equation.origin
    passed = not collection_issues and max_relative <= RESIDUAL_RTOL
    return {
        "status": "passed" if passed else "failed",
        "equation_count": len(equations),
        "vector_count": int(values.shape[1]),
        "max_absolute_residual": max_absolute,
        "max_relative_residual": max_relative,
        "residual_l2_norm": float(np.sqrt(residual_l2)),
        "relative_tolerance": RESIDUAL_RTOL,
        "worst_origin": worst_origin,
        "collection_issue_count": len(collection_issues),
        "homogeneous_variation": bool(homogeneous_variation),
        "issue_code": None if passed else "CONSTRAINT006",
    }


def require_valid_constraints(model: "FEModel") -> ConstraintAuditReport:
    """Return the audit or raise before matrix reduction for an invalid model."""
    report = audit_constraints(model)
    if report.errors:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in report.errors)
        raise ValueError(f"Invalid constraint system: {details}")
    return report
