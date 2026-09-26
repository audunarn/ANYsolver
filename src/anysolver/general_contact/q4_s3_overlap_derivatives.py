"""Smooth-branch derivatives for a physical Q4 source and S3 target.

The Q4 remains one bilinear Q1 face.  At an affine pose, the seven-point rule
integrates value and first/second variations exactly.  Warped poses use the
same adaptive quadrature semantics as the existing Q4 source kernel, with
derivatives of the accepted smooth quadrature branch.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver._ge_beam3_mixed_ad import Jet2, sqrt

from .moving import _TRIANGLE_RULE


class UnsupportedQ4S3Branch(ValueError):
    """The requested pose is outside an admitted smooth Q4/S3 branch."""


@dataclass(frozen=True)
class Q4S3OverlapDerivatives:
    """P1/Q1 node integrals and 21-coordinate derivatives.

    ``derivative_quadrature_differences`` sums leafwise coarse/refined
    differences in support gradient, support Hessian, gap gradient and gap
    Hessian order.  It is a resolution indicator, not a certified error bound.
    """

    reference_support: np.ndarray
    reference_weighted_gap: np.ndarray
    support_gradient: np.ndarray
    support_hessian: np.ndarray
    weighted_gap_gradient: np.ndarray
    weighted_gap_hessian: np.ndarray
    overlap_area: float
    reference_overlap_area: float
    branch_signature: tuple[int, ...]
    integration_triangles: int
    derivative_quadrature_differences: np.ndarray


_SIZE = 21


def _zero() -> Jet2:
    return Jet2.constant(0.0, _SIZE)


def _sum(items) -> Jet2:
    return sum(items, start=_zero())


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _dot(a, b):
    return _sum(x*y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0]]


def _cross2(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _normalize(a):
    length = sqrt(_dot(a, a))
    return [x/length for x in a]


def _signed_area(poly):
    return _sum(_cross2(p, poly[(i+1) % len(poly)])
                for i, p in enumerate(poly))/2


def _clip(subject, target, threshold):
    polygon = subject
    signature = []
    for edge_index in range(3):
        if not polygon:
            raise UnsupportedQ4S3Branch("zero projected overlap")
        start = target[edge_index]
        edge = _sub(target[(edge_index+1) % 3], start)
        old = polygon[-1]
        old_distance = _cross2(edge, _sub(old, start))
        out = []
        signature.append(len(polygon))
        for point in polygon:
            distance = _cross2(edge, _sub(point, start))
            if min(abs(old_distance.value), abs(distance.value)) <= threshold:
                raise UnsupportedQ4S3Branch("vertex lies on a clipping boundary")
            old_inside = old_distance.value > 0
            inside = distance.value > 0
            signature.append(int(inside))
            if old_inside != inside:
                denominator = old_distance-distance
                if abs(denominator.value) <= threshold:
                    raise UnsupportedQ4S3Branch("degenerate clipping intersection")
                alpha = old_distance/denominator
                out.append([a+alpha*(b-a) for a, b in zip(old, point)])
            if inside:
                out.append(point)
            old, old_distance = point, distance
        polygon = out
    signature.append(len(polygon))
    return polygon, tuple(signature)


def _q1(r, s):
    one = Jet2.constant(1.0, _SIZE)
    shape = [(one-r)*(one-s)/4, (one+r)*(one-s)/4,
             (one+r)*(one+s)/4, (one-r)*(one+s)/4]
    dr = [-(one-s)/4, (one-s)/4, (one+s)/4, -(one+s)/4]
    ds = [-(one-r)/4, -(one+r)/4, (one+r)/4, (one-r)/4]
    return shape, dr, ds


def _map_xy(shape, corners):
    return [_sum(shape[i]*corners[i][k] for i in range(4)) for k in range(2)]


def _natural(point, corners):
    # At an affine base pose, this value solve is exact.  Jet Newton iterations
    # then solve the first and second variations of the bilinear inverse.
    a = np.array([corners[1][k].value-corners[0][k].value for k in range(2)])
    b = np.array([corners[3][k].value-corners[0][k].value for k in range(2)])
    rhs = np.array([point[k].value-corners[0][k].value for k in range(2)])
    u, v = np.linalg.solve(np.column_stack((a, b)), rhs)
    r = Jet2.constant(2*u-1, _SIZE)
    s = Jet2.constant(2*v-1, _SIZE)
    for _ in range(3):
        shape, dr, ds = _q1(r, s)
        mapped = _map_xy(shape, corners)
        first = _map_xy(dr, corners)
        second = _map_xy(ds, corners)
        determinant = _cross2(first, second)
        residual = _sub(mapped, point)
        delta_r = _cross2(residual, second)/determinant
        delta_s = _cross2(first, residual)/determinant
        r, s = r-delta_r, s-delta_s
    shape, dr, ds = _q1(r, s)
    residual = _sub(_map_xy(shape, corners), point)
    if any(abs(x.value) > 1e-11 or np.max(np.abs(x.gradient)) > 1e-9
           or np.max(np.abs(x.hessian)) > 1e-7 for x in residual):
        raise UnsupportedQ4S3Branch("Q1 projected inversion did not converge")
    return shape, dr, ds


def _target_shape(point, corners):
    a = _sub(corners[1], corners[0])
    b = _sub(corners[2], corners[0])
    p = _sub(point, corners[0])
    denominator = _cross2(a, b)
    u = _cross2(p, b)/denominator
    v = _cross2(a, p)/denominator
    return [1-u-v, u, v]


def _parts(jets):
    return (np.array([x.value for x in jets]),
            np.stack([x.gradient for x in jets]),
            np.stack([x.hessian for x in jets]))


def _validate(source_reference, source_current, target_current,
              relative_branch_tolerance, enforce_affine):
    reference = np.asarray(source_reference, dtype=float)
    source = np.asarray(source_current, dtype=float)
    target = np.asarray(target_current, dtype=float)
    if (reference.shape != (4, 3) or source.shape != (4, 3)
            or target.shape != (3, 3)
            or not all(np.all(np.isfinite(x)) for x in (reference, source, target))):
        raise ValueError("Q4/S3 overlap needs finite (4,3), (4,3), (3,3) positions")
    if not np.isfinite(relative_branch_tolerance) or relative_branch_tolerance <= 0:
        raise ValueError("relative_branch_tolerance must be finite and positive")
    for name, quad in (("reference", reference), ("current", source)):
        span = max(np.linalg.norm(quad[i]-quad[0]) for i in (1, 2, 3))
        if span <= 0:
            raise UnsupportedQ4S3Branch(f"{name} Q4 is degenerate")
        cross = np.cross(quad[1]-quad[0], quad[3]-quad[0])
        if np.linalg.norm(cross) <= 1e-12*span*span:
            raise UnsupportedQ4S3Branch(f"{name} Q4 is degenerate")
        if ((name == "reference" or enforce_affine) and
                np.linalg.norm(quad[0]-quad[1]+quad[2]-quad[3])
                > relative_branch_tolerance*span):
            raise UnsupportedQ4S3Branch(f"{name} Q4 is warped or non-affine")
    target_span = max(np.linalg.norm(target[i]-target[0]) for i in (1, 2))
    if (target_span <= 0 or np.linalg.norm(np.cross(target[1]-target[0],
                                                    target[2]-target[0]))
            <= 1e-12*target_span*target_span):
        raise UnsupportedQ4S3Branch("S3 target is degenerate")
    return reference, source, target


def _evaluate(reference_source, current_source, current_target, *,
              area_tolerance, weighted_gap_tolerance, maximum_triangles,
              relative_branch_tolerance, enforce_affine,
              derivative_tolerances=None):
    reference, source, target = _validate(
        reference_source, current_source, current_target,
        relative_branch_tolerance, enforce_affine,
    )
    if (not np.isfinite(area_tolerance) or area_tolerance <= 0
            or not np.isfinite(weighted_gap_tolerance)
            or weighted_gap_tolerance <= 0
            or type(maximum_triangles) is not int or maximum_triangles < 1):
        raise ValueError("integration tolerances and triangle budget must be positive")
    if not enforce_affine and derivative_tolerances is None:
        raise ValueError("warped Q4 needs explicit gradient and Hessian tolerances")
    values = np.concatenate((source, target)).reshape(-1)
    points = [[Jet2.variable(values[3*i+k], 3*i+k, _SIZE) for k in range(3)]
              for i in range(7)]
    q, t = points[:4], points[4:]
    e1 = _sub(q[1], q[0])
    e3 = _sub(q[3], q[0])
    normal = _normalize(_cross(e1, e3))
    for i in range(4):
        first = _sub(q[(i+1) % 4], q[i])
        second = _sub(q[(i-1) % 4], q[i])
        if _dot(_cross(first, second), normal).value <= 0:
            raise UnsupportedQ4S3Branch("Q4 is folded or has inverted bilinear geometry")
    ref_cross = np.cross(reference[1]-reference[0],
                         reference[3]-reference[0])
    if np.dot(ref_cross, np.array([x.value for x in normal])) <= 0:
        raise UnsupportedQ4S3Branch("Q4 polarity differs from reference")
    target_cross = _cross(_sub(t[1], t[0]), _sub(t[2], t[0]))
    if _dot(target_cross, normal).value <= 0:
        raise UnsupportedQ4S3Branch("S3 target faces away")
    tangent = _normalize(e1)
    binormal = _cross(normal, tangent)

    def projected(point):
        delta = _sub(point, q[0])
        return [_dot(delta, tangent), _dot(delta, binormal)]

    quad_xy = [projected(x) for x in q]
    triangle_xy = [projected(x) for x in t]
    scale = max(np.hypot(x[0].value, x[1].value)
                for x in (*quad_xy, *triangle_xy))
    threshold = relative_branch_tolerance*scale*scale
    if _signed_area(quad_xy).value <= threshold:
        raise UnsupportedQ4S3Branch("Q4 projection is degenerate or inverted")
    for i in range(4):
        edge1 = _sub(quad_xy[(i+1) % 4], quad_xy[i])
        edge2 = _sub(quad_xy[(i+2) % 4], quad_xy[(i+1) % 4])
        if _cross2(edge1, edge2).value <= threshold:
            raise UnsupportedQ4S3Branch("Q4 projection is folded or degenerate")
    if _signed_area(triangle_xy).value <= threshold:
        raise UnsupportedQ4S3Branch("S3 projection is degenerate or inverted")
    polygon, clipping_signature = _clip(quad_xy, triangle_xy, threshold)
    if len(polygon) < 3:
        raise UnsupportedQ4S3Branch("zero projected overlap")
    overlap_area = _signed_area(polygon)
    if overlap_area.value <= threshold:
        raise UnsupportedQ4S3Branch("zero projected overlap")

    ref_area_jacobian = np.linalg.norm(ref_cross)/4
    def rule(vertices):
        area = _cross2(_sub(vertices[1], vertices[0]),
                       _sub(vertices[2], vertices[0]))/2
        if area.value <= threshold:
            raise UnsupportedQ4S3Branch("degenerate integration triangle")
        total = [_zero() for _ in range(24)]
        for bary, relative_weight in _TRIANGLE_RULE:
            xy = [_sum(bary[j]*vertices[j][k] for j in range(3))
                  for k in range(2)]
            shape, dr, ds = _natural(xy, quad_xy)
            jr = [_sum(dr[i]*q[i][k] for i in range(4)) for k in range(3)]
            js = [_sum(ds[i]*q[i][k] for i in range(4)) for k in range(3)]
            cross = _cross(jr, js)
            projected_jacobian = _dot(cross, normal)
            if projected_jacobian.value <= threshold/4:
                raise UnsupportedQ4S3Branch("Q4 projected Jacobian is near singular")
            physical_normal = _normalize(cross)
            source_point = [_sum(shape[i]*q[i][k] for i in range(4))
                            for k in range(3)]
            target_shape = _target_shape(xy, triangle_xy)
            target_point = [_sum(target_shape[i]*t[i][k] for i in range(3))
                            for k in range(3)]
            gap = _dot(physical_normal, _sub(source_point, target_point))
            weight = area*relative_weight*ref_area_jacobian/projected_jacobian
            integrand = ([weight*x for x in shape]
                         + [weight*x*gap for x in shape]
                         + [weight*x*y for x in shape for y in shape])
            total = [a+b for a, b in zip(total, integrand)]
        return total

    total = [_zero() for _ in range(24)]
    integration_triangles = 0
    visited_triangles = 0
    quadrature_signature: list[int] = []
    derivative_differences = np.zeros(4)
    roots = len(polygon)-2
    def integrate(vertices, area_budget, gap_budget, derivative_budgets):
        nonlocal integration_triangles, visited_triangles
        visited_triangles += 1
        if visited_triangles > maximum_triangles:
            raise UnsupportedQ4S3Branch("adaptive integration exceeds triangle budget")
        a, b, c = vertices
        coarse = rule(vertices)
        ab = [(x+y)/2 for x, y in zip(a, b)]
        bc = [(x+y)/2 for x, y in zip(b, c)]
        ca = [(x+y)/2 for x, y in zip(c, a)]
        children = ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))
        refined = [_zero() for _ in range(24)]
        for child in children:
            refined = [x+y for x, y in zip(refined, rule(child))]
        area_error = max(abs(refined[i].value-coarse[i].value)
                         for i in (*range(4), *range(8, 24)))
        gap_error = max(abs(refined[i].value-coarse[i].value)
                        for i in range(4, 8))
        derivative_errors = (
            max(np.max(np.abs(refined[i].gradient-coarse[i].gradient))
                for i in range(4)),
            max(np.max(np.abs(refined[i].hessian-coarse[i].hessian))
                for i in range(4)),
            max(np.max(np.abs(refined[i].gradient-coarse[i].gradient))
                for i in range(4, 8)),
            max(np.max(np.abs(refined[i].hessian-coarse[i].hessian))
                for i in range(4, 8)),
        )
        if (abs(area_error-area_budget) <= 1e-8*area_budget
                or abs(gap_error-gap_budget) <= 1e-8*gap_budget):
            raise UnsupportedQ4S3Branch("adaptive integration decision is ambiguous")
        if (derivative_budgets is not None and any(
            abs(error-budget) <= 1e-8*budget
            for error, budget in zip(derivative_errors, derivative_budgets)
        )):
            raise UnsupportedQ4S3Branch("derivative integration decision is ambiguous")
        derivative_resolved = (derivative_budgets is None or all(
            error <= budget for error, budget in
            zip(derivative_errors, derivative_budgets)
        ))
        if (area_error <= area_budget and gap_error <= gap_budget
                and derivative_resolved):
            quadrature_signature.append(0)
            if enforce_affine:
                derivative_error = max(derivative_errors)
                derivative_scale = max(
                    1.0, *(max(np.max(np.abs(x.gradient)),
                                np.max(np.abs(x.hessian))) for x in refined[:8])
                )
                if derivative_error > 1e-10*derivative_scale:
                    raise UnsupportedQ4S3Branch(
                        "quadrature does not resolve the support/gap derivatives"
                    )
            integration_triangles += 4
            if integration_triangles > maximum_triangles:
                raise UnsupportedQ4S3Branch("adaptive integration exceeds triangle budget")
            derivative_differences[:] += derivative_errors
            return refined
        quadrature_signature.append(1)
        if integration_triangles+4 > maximum_triangles:
            raise UnsupportedQ4S3Branch("adaptive integration exceeds triangle budget")
        integrated = [_zero() for _ in range(24)]
        for child in children:
            integrated = [x+y for x, y in zip(
                integrated, integrate(
                    child, area_budget/4, gap_budget/4,
                    None if derivative_budgets is None else
                    tuple(budget/4 for budget in derivative_budgets),
                )
            )]
        return integrated

    for index in range(1, len(polygon)-1):
        vertices = (polygon[0], polygon[index], polygon[index+1])
        total = [x+y for x, y in zip(total, integrate(
            vertices, area_tolerance/roots, weighted_gap_tolerance/roots,
            None if derivative_tolerances is None else
            tuple(tolerance/roots for tolerance in derivative_tolerances),
        ))]
    support, support_gradient, support_hessian = _parts(total[:4])
    gap, gap_gradient, gap_hessian = _parts(total[4:8])
    if (np.min(support) <= 0 or not all(np.all(np.isfinite(x)) for x in
            (support, support_gradient, support_hessian,
             gap, gap_gradient, gap_hessian))):
        raise UnsupportedQ4S3Branch("nonpositive support or nonfinite derivative")
    return Q4S3OverlapDerivatives(
        support, gap, support_gradient, support_hessian,
        gap_gradient, gap_hessian, overlap_area.value,
        float(np.sum(support)), clipping_signature+tuple(quadrature_signature),
        integration_triangles, derivative_differences,
    )


def q4_s3_overlap_derivatives(
    reference_source: np.ndarray, current_source: np.ndarray,
    current_target: np.ndarray, *, area_tolerance: float = 1e-10,
    weighted_gap_tolerance: float = 1e-10, maximum_triangles: int = 32,
    relative_branch_tolerance: float = 1e-10,
    allow_warped_source: bool = False,
    support_gradient_tolerance: float | None = None,
    support_hessian_tolerance: float | None = None,
    weighted_gap_gradient_tolerance: float | None = None,
    weighted_gap_hessian_tolerance: float | None = None,
) -> Q4S3OverlapDerivatives:
    """Differentiate source Q1 reference support/gap in 4+3 xyz node order.

    The reference Q4 must be affine.  The derivative is of the smooth physical
    Q1 and accepted quadrature branch.  Warped current poses require explicit
    opt-in and four positive derivative-resolution tolerances; their integral
    and derivative accuracy depends on those controls and the triangle budget.
    Clipping and quadrature decision ties
    are unsupported.  Polygon fans create no physical faces.
    """
    if type(allow_warped_source) is not bool:
        raise ValueError("allow_warped_source must be boolean")
    derivative_tolerances = None
    if allow_warped_source:
        derivative_tolerances = (
            support_gradient_tolerance, support_hessian_tolerance,
            weighted_gap_gradient_tolerance, weighted_gap_hessian_tolerance,
        )
        if any(item is None or not np.isfinite(item) or item <= 0
               for item in derivative_tolerances):
            raise ValueError("warped Q4 needs four positive derivative tolerances")
    return _evaluate(
        reference_source, current_source, current_target,
        area_tolerance=area_tolerance,
        weighted_gap_tolerance=weighted_gap_tolerance,
        maximum_triangles=maximum_triangles,
        relative_branch_tolerance=relative_branch_tolerance,
        enforce_affine=not allow_warped_source,
        derivative_tolerances=derivative_tolerances,
    )
