"""Independent-review correction: full rigid-footprint support rank."""

from __future__ import annotations

import json

import numpy as np


def skew(v: np.ndarray) -> np.ndarray:
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def examine(points: np.ndarray, origin: np.ndarray) -> dict:
    jac = np.vstack([np.column_stack((np.eye(3), -skew(x - origin))) for x in points])
    singular = np.linalg.svd(jac, compute_uv=False)
    rank = int(np.sum(singular > 1e-10 * singular[0]))
    _, _, vh = np.linalg.svd(jac, full_matrices=True)
    null_error = float(np.linalg.norm(jac @ vh[-1])) if rank < 6 else None
    rotational = np.vstack([-skew(x - origin) for x in points])
    rotational_rank = int(np.linalg.matrix_rank(rotational, tol=1e-10 *
                                                np.linalg.svd(rotational, compute_uv=False)[0]))
    return {"rank": rank, "rotation_block_rank": rotational_rank,
            "null_error": null_error, "singular_values": singular.tolist()}


def main() -> int:
    origin = np.array([0., 0., .2])
    cases = {
        "square": np.array([[-.5, -.5, 0.], [.5, -.5, 0.], [.5, .5, 0.], [-.5, .5, 0.]]),
        "offset_line": np.array([[-.5, .2, .3], [0., .2, .3], [.5, .2, .3]]),
        "coincident": np.tile(np.array([.2, .1, .3]), (3, 1)),
        "curved_arc": np.array([[-.5, .25, 0.], [0., 0., 0.], [.5, .25, 0.]]),
    }
    result = {name: examine(points, origin) for name, points in cases.items()}
    passed = ([result[name]["rank"] for name in cases] == [6, 5, 3, 6]
              and result["offset_line"]["rotation_block_rank"] == 3
              and all(result[name]["null_error"] <= 1e-10 for name in ("offset_line", "coincident")))
    print(json.dumps({"case": "G0_F04_RIGID_FULL_RANK_V2",
                      "status": "diagnostic_pass" if passed else "failed", "supports": result}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
