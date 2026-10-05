"""Independent high-precision value oracle for one captured Q4/S3 wedge.

This development oracle clips projected polygons and integrates physical Q4
work in Decimal arithmetic. It does not call the production contact kernels.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path

import numpy as np


ZERO = Decimal(0)
ONE = Decimal(1)
TWO = Decimal(2)


def d(value):
    return Decimal.from_float(float(value))


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(x*factor for x in a)


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), ZERO)


def cross(a, b):
    if len(a) == 2:
        return a[0]*b[1]-a[1]*b[0]
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def norm(a):
    return dot(a, a).sqrt()


def normalize(a):
    return scale(a, ONE/norm(a))


def shape(u, v):
    values = ((ONE-u)*(ONE-v), u*(ONE-v), u*v, (ONE-u)*v)
    du = (v-ONE, ONE-v, v, -v)
    dv = (u-ONE, -u, u, ONE-u)
    return values, du, dv


def combination(weights, points):
    total = (ZERO,)*len(points[0])
    for weight, point in zip(weights, points, strict=True):
        total = add(total, scale(point, weight))
    return total


def clip(subject, triangle):
    polygon = list(subject)
    signature = []
    for a, b in zip(triangle, triangle[1:]+triangle[:1]):
        edge = sub(b, a)
        out = []
        intersections = 0
        for previous, current in zip(polygon[-1:]+polygon[:-1], polygon):
            dp = cross(edge, sub(previous, a))
            dc = cross(edge, sub(current, a))
            inside_previous = dp >= 0
            inside_current = dc >= 0
            if inside_previous != inside_current:
                fraction = dp/(dp-dc)
                out.append(add(previous,
                               scale(sub(current, previous), fraction)))
                intersections += 1
            if inside_current:
                out.append(current)
        polygon = out
        signature.append((len(polygon), intersections))
        if not polygon:
            break
    return polygon, signature


def natural(point, corners):
    u = point[0]/corners[1][0]
    v = point[1]/corners[3][1]
    for _ in range(12):
        values, du, dv = shape(u, v)
        residual = sub(combination(values, corners), point)
        if max(abs(x) for x in residual) < Decimal("1e-65"):
            return u, v, values, du, dv
        tangent_u = combination(du, corners)
        tangent_v = combination(dv, corners)
        determinant = cross(tangent_u, tangent_v)
        u -= cross(residual, tangent_v)/determinant
        v -= cross(tangent_u, residual)/determinant
    raise ArithmeticError("Q4 inverse did not converge")


def gauss_rule(order):
    x, weights = np.polynomial.legendre.leggauss(order)
    return [((d(a)+ONE)/TWO, d(w)/TWO)
            for a, w in zip(x, weights, strict=True)]


def work(reference, source, target, pressure, order):
    origin = source[0]
    e1 = sub(source[1], origin)
    e3 = sub(source[3], origin)
    normal = normalize(cross(e1, e3))
    tangent = normalize(e1)
    binormal = cross(normal, tangent)

    def project(point):
        delta = sub(point, origin)
        return dot(delta, tangent), dot(delta, binormal)

    corners = [project(point) for point in source]
    triangle = [project(point) for point in target]
    polygon, signature = clip(corners, triangle)
    if len(polygon) < 3:
        raise ArithmeticError("captured wedge lost projected overlap")
    target_det = cross(sub(triangle[1], triangle[0]),
                       sub(triangle[2], triangle[0]))
    rule = gauss_rule(order)

    def integrand(xy):
        u, v, values, du, dv = natural(xy, corners)
        if not (Decimal("-1e-8") <= u <= ONE+Decimal("1e-8")
                and Decimal("-1e-8") <= v <= ONE+Decimal("1e-8")):
            raise ArithmeticError("quadrature point outside source Q4")
        source_u = combination(du, source)
        source_v = combination(dv, source)
        physical_cross = cross(source_u, source_v)
        physical_normal = normalize(physical_cross)
        projected_jacobian = dot(physical_cross, normal)
        reference_jacobian = norm(cross(
            combination(du, reference), combination(dv, reference),
        ))
        relative = sub(xy, triangle[0])
        bary1 = cross(relative, sub(triangle[2], triangle[0]))/target_det
        bary2 = cross(sub(triangle[1], triangle[0]), relative)/target_det
        bary0 = ONE-bary1-bary2
        gap = dot(physical_normal, sub(
            combination(values, source),
            combination((bary0, bary1, bary2), target),
        ))
        return (reference_jacobian/projected_jacobian
                * dot(values, pressure)*gap)

    total = ZERO
    for b, c in zip(polygon[1:-1], polygon[2:]):
        a = polygon[0]
        ab = sub(b, a)
        ac = sub(c, a)
        determinant = cross(ab, ac)
        if determinant <= 0:
            raise ArithmeticError("clipped polygon triangle is not positive")
        for s, ws in rule:
            for t, wt in rule:
                xy = add(a, add(scale(ab, s), scale(ac, (ONE-s)*t)))
                total += ws*wt*determinant*(ONE-s)*integrand(xy)
    area = sum((cross(polygon[i], polygon[(i+1) % len(polygon)])
                for i in range(len(polygon))), ZERO)/TWO
    return total, area, signature


def main(capture_path: Path, output_path: Path):
    if output_path.exists():
        raise FileExistsError(output_path)
    if capture_path.suffix.lower() == ".json":
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        reference_float = capture["source_reference"]
        source_float = capture["local_source"]
        target_float = capture["local_target"]
        pressure_float = capture["local_pressure_pa"]
        direction_float = capture["direction_per_m"]
    else:
        with np.load(capture_path) as capture:
            reference_float = capture["source_reference"].copy()
            source_float = capture["local_source"].copy()
            target_float = capture["local_target"].copy()
            pressure_float = capture["pressure"][capture["source_nodes"]].copy()
        direction_float = [(1.0, 0.0, 0.2)]*4+[(0.0, 0.0, 0.0)]*3
    with localcontext() as context:
        context.prec = 80
        reference = [tuple(map(d, row)) for row in reference_float]
        source = [tuple(map(d, row)) for row in source_float]
        target = [tuple(map(d, row)) for row in target_float]
        pressure = tuple(map(d, pressure_float))
        direction = [tuple(map(d, row)) for row in direction_float]
        rows = []
        for order in (4, 8, 12):
            baseline, base_area, base_signature = work(
                reference, source, target, pressure, order,
            )
            for h in ("4e-10", "2e-10", "1e-10", "5e-11", "2.5e-11"):
                step = Decimal(h)
                plus_source = [add(point, scale(rate, step))
                               for point, rate in zip(source, direction[:4])]
                minus_source = [sub(point, scale(rate, step))
                                for point, rate in zip(source, direction[:4])]
                plus_target = [add(point, scale(rate, step))
                               for point, rate in zip(target, direction[4:])]
                minus_target = [sub(point, scale(rate, step))
                                for point, rate in zip(target, direction[4:])]
                plus, plus_area, plus_signature = work(
                    reference, plus_source, plus_target, pressure, order,
                )
                minus, minus_area, minus_signature = work(
                    reference, minus_source, minus_target, pressure, order,
                )
                rows.append({
                    "quadrature_order": order,
                    "step_m": h,
                    "same_clip_signature": (
                        plus_signature == base_signature == minus_signature
                    ),
                    "base_area_m2": str(base_area),
                    "plus_area_m2": str(plus_area),
                    "minus_area_m2": str(minus_area),
                    "gradient_j_per_m": str((plus-minus)/(TWO*step)),
                    "hessian_j_per_m2": str(
                        (plus-TWO*baseline+minus)/(step*step)
                    ),
                })
    record = {"capture": str(capture_path), "precision_digits": 80,
              "input_conversion": "exact binary64 to Decimal",
              "rows": rows}
    output_path.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    for row in rows:
        print(row["quadrature_order"], row["step_m"],
              row["same_clip_signature"],
              f"{float(row['hessian_j_per_m2']):.12g}",
              f"{float(row['gradient_j_per_m']):.12g}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.capture, args.output)
