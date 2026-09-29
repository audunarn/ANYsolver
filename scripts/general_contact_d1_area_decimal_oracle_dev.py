"""Independent high-precision projected polygon areas for captured Q4/S3 pairs.

Uses only Python Decimal arithmetic on the captured physical coordinates.
No production clipping, projection or differentiation function is imported.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path


def vector(values):
    return tuple(Decimal.from_float(float(value)) for value in values)


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(x*factor for x in a)


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Decimal(0))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def cross2(a, b):
    return a[0]*b[1]-a[1]*b[0]


def unit(a):
    return scale(a, Decimal(1)/dot(a, a).sqrt())


def projected_area(source_values, target_values):
    source = tuple(vector(point) for point in source_values)
    target = tuple(vector(point) for point in target_values)
    normal = unit(cross(sub(source[1], source[0]),
                        sub(source[3], source[0])))
    tangent = unit(sub(source[1], source[0]))
    binormal = cross(normal, tangent)

    def project(point):
        delta = sub(point, source[0])
        return (dot(delta, tangent), dot(delta, binormal))

    polygon = [project(point) for point in source]
    clip = [project(point) for point in target]
    for index, first in enumerate(clip):
        if not polygon:
            return Decimal(0), 0
        edge = sub(clip[(index+1) % len(clip)], first)
        previous = polygon[-1]
        previous_distance = cross2(edge, sub(previous, first))
        output = []
        for current in polygon:
            distance = cross2(edge, sub(current, first))
            previous_inside = previous_distance >= 0
            current_inside = distance >= 0
            if previous_inside != current_inside:
                fraction = previous_distance/(previous_distance-distance)
                output.append(add(previous,
                                  scale(sub(current, previous), fraction)))
            if current_inside:
                output.append(current)
            previous, previous_distance = current, distance
        polygon = output
    if len(polygon) < 3:
        return Decimal(0), len(polygon)
    origin = polygon[0]
    doubled = sum((cross2(sub(polygon[i], origin),
                            sub(polygon[i+1], origin))
                   for i in range(1, len(polygon)-1)), Decimal(0))
    return abs(doubled)/2, len(polygon)


def main(capture_path: Path, output_path: Path):
    if output_path.exists():
        raise FileExistsError(output_path)
    raw = capture_path.read_bytes()
    captured = json.loads(raw)
    with localcontext() as context:
        context.prec = 80
        results = []
        for index, entry in enumerate(captured["captures"]):
            area, vertices = projected_area(entry["source_q4_m"],
                                            entry["target_s3_m"])
            float_area = Decimal.from_float(entry["float_overlap_area_m2"])
            jet_area = Decimal.from_float(entry["jet2_overlap_area_m2"])
            results.append({
                "capture_index": index,
                "decimal_projected_area_m2": str(area),
                "polygon_vertices": vertices,
                "float_area_absolute_error_m2": str(abs(float_area-area)),
                "jet2_area_absolute_error_m2": str(abs(jet_area-area)),
                "float_area_relative_error": str(abs(float_area-area)/area),
                "jet2_area_relative_error": str(abs(jet_area-area)/area),
                "propagated_area_resolution_m2":
                    entry["jet2_area_resolution_m2"],
            })
    payload = {"capture_sha256": hashlib.sha256(raw).hexdigest(),
               "decimal_precision": 80, "results": results}
    output_path.write_text(json.dumps(payload, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"capture_count": len(results),
                      "capture_sha256": payload["capture_sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    main(arguments.capture, arguments.output)
