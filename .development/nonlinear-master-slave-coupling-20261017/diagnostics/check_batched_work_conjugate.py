"""Compare unchanged scalar/batched stencils and run the independent FD oracle."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tests'))
import test_corotational_work_conjugate as fixtures
import anysolver.corotational as cr
import batched_work_conjugate_candidate as candidate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output')
    args = ap.parse_args()
    output = Path(args.output)
    if output.exists():
        ap.error('refusing to overwrite evidence')
    records = []
    for builder in (fixtures._make_beam_model, fixtures._make_q4_shell_model,
                    fixtures._make_s3_shell_model):
        model, elem_id, elem = builder()
        coords = np.asarray(elem.get_node_coordinates(model.mesh))
        ref = cr._corotational_cache(model)[elem_id]
        rng = np.random.default_rng(20261018)
        for angle in (0., 35., 100.):
            u = np.zeros((elem.num_nodes, 6))
            u[:, :3] = .006*rng.standard_normal((elem.num_nodes, 3))
            u[:, 3:] = .035*rng.standard_normal((elem.num_nodes, 3))
            u = fixtures._superimpose_se3_motion(coords, u.ravel(),
                    np.deg2rad(angle)*np.array([.6, -.5, .6244997998398398]),
                    np.array([.3, -.4, .2]))
            ud, R, deformed = cr._corotational_deformation_state(ref, elem, u)
            rotations = u.reshape(-1, 6)[:, 3:]
            D, U, G = cr._pullback_jacobian_factors(ref, elem, deformed, rotations, R)
            f, K, _ = elem.compute_nonlinear_response(model.mesh,
                    model.get_material(elem.material_name), ud, None, 5, True)
            a = (ref, elem, deformed, rotations, R, G, D+U@G, f, K)
            old_mat, old_geo = candidate.ORIGINAL(*a)
            new_mat, new_geo = candidate.tangent(*a)
            # Numerical equality is checked before measured timing. The public
            # test below supplies the independent dp/du oracle at unchanged1e-7.
            assert np.array_equal(old_mat, new_mat)
            total_error = np.linalg.norm(old_geo-new_geo)/max(np.linalg.norm(old_mat+old_geo), 1e-30)
            assert total_error < 1e-7, (builder.__name__, angle, total_error)
            geometric_error = np.linalg.norm(old_geo-new_geo)/max(np.linalg.norm(old_geo), 1e-30)
            timings = {}
            for name, kernel in (('scalar', candidate.ORIGINAL), ('batched', candidate.tangent)):
                start = time.perf_counter()
                for _ in range(5):
                    kernel(*a)
                timings[name] = (time.perf_counter()-start)/5
            records.append(dict(element=builder.__name__, angle=angle,
                                total_tangent_relative_difference=float(total_error),
                                geometric_tangent_relative_difference=float(geometric_error),
                                seconds_per_evaluation=timings))
    output.write_text(json.dumps(dict(comparisons=records), indent=2))
    original = cr._work_conjugate_corotational_tangent
    cr._work_conjugate_corotational_tangent = candidate.tangent
    try:
        status = pytest.main(['-x', '-vv', str(Path(fixtures.__file__))])
    finally:
        cr._work_conjugate_corotational_tangent = original
    record = dict(comparisons=records, independent_existing_tests_exit_code=int(status))
    output.write_text(json.dumps(record, indent=2))
    print(json.dumps(record), flush=True)
    raise SystemExit(status)


if __name__ == '__main__':
    main()
