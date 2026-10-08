"""Prospective pressure assessment experiment. NOT imported by product code.

Executing this file explicitly overrides the finite module in this process only.
No resulting solve is accepted evidence under the current frozen assessment.
"""
import json
from pathlib import Path
import sys

import numpy as np


def proposed_ratio(residual, applied, scale, *, free, shell_count):
    from anysolver._stiffened_shell_ge_finite_experimental import _trial_work_ratio
    result = _trial_work_ratio(residual, applied, scale)
    # Only groups actually carrying pressure are active. Native beam/internal
    # rows have no external pressure; their equilibrium remains in global norm.
    for group in np.unique(free[free < shell_count]//3):
        selected = free//3 == group
        r, f = residual[selected]*scale[selected], applied[selected]*scale[selected]
        magnitude = max(np.max(np.abs(r), initial=0.), np.max(np.abs(f), initial=0.))
        if np.any(f):
            result = max(result, float(np.linalg.norm(r/magnitude)/np.linalg.norm(f/magnitude)))
    return result


def controls():
    from scipy.spatial.transform import Rotation
    free = np.arange(12)
    f = np.array((1., 2., 3., .4, -.2, .3, 1e-12, 0., 0., 0., 0., 0.))
    r = 1e-10*f
    def ratio(r, f, scale=None, selected=free):
        return proposed_ratio(r, f, np.ones(len(r)) if scale is None else scale,
                              free=selected, shell_count=12)
    base = ratio(r, f)
    transform = np.kron(np.eye(4), Rotation.from_rotvec((.3, -.4, .2)).as_matrix())
    assert np.isclose(ratio(transform@r, transform@f), base, rtol=1e-12)
    missed = r.copy(); missed[6] = f[6]
    assert ratio(missed, f) >= 1.
    for units in (1e-6, 1e6):
        assert np.isclose(ratio(units*r, units*f), base, rtol=1e-12)
    unsupported = r.copy(); unsupported[11] = 1.
    assert ratio(unsupported, f) > 1e-8
    for index in (3, 9):
        wrong = r.copy(); wrong[index] = 1.
        assert ratio(wrong, f) > 1e-8
    assert proposed_ratio(np.r_[r, 1.], np.r_[f, 0.], np.ones(13),
                          free=np.arange(13), shell_count=12) > 1e-8
    # Explicit changed guarantee: an orthogonal tiny contribution at the same
    # node can be missed. Preserve this counterexample rather than hide it.
    shared = np.zeros(12); shared[:3] = (1e-10, 0., 1.)
    missing = np.zeros(12); missing[0] = 1e-10
    assert ratio(missing, shared) < 1e-8
    cancelled = np.zeros(12); cancelled[6] = 1.
    assert ratio(missing, cancelled) < 1e-8  # zero group has global coverage only
    for quiet in (-1e-20, 0., 1e-20):
        crossed = shared.copy(); crossed[0] = quiet
        assert ratio(missing, crossed) < 1e-8
    selected = np.array((1, 2, 4, 5, 6, 7, 8, 9, 10, 11))
    assert np.isclose(ratio(r[selected], f[selected], selected=selected), base, rtol=1e-12)


def main():
    root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root/'tests'))
    from anysolver import stiffened_shell as ss
    from anysolver import _stiffened_shell_ge_finite_experimental as finite
    from anysolver.control import CancellationToken, SolveCancelled
    from test_stiffened_shell_ge_pressure_owner import definition, load, balance
    from test_stiffened_shell_ge_director_pressure import director_load
    controls()
    original = finite._linear_equilibrium
    reports = []
    try:
        for kind, mode in (('mixed', 'director'), ('s3', 'director'), ('mixed', 'current_surface')):
            a, b = (ss.create_analysis(definition=definition(kind)) for _ in range(2))
            finite._linear_equilibrium = lambda r, f, s: proposed_ratio(r, f, s,
                free=a._free, shell_count=a._shell_count)
            token = CancellationToken()
            action = director_load(a) if mode == 'director' else load(a, mode)
            try:
                try:
                    a.solve(action, (.1, .2), on_accepted=lambda _: token.cancel('prefix'), cancellation_token=token)
                except SolveCancelled:
                    pass
                assert a.recover().accepted_factors == (.1,)
                b.restore(a.checkpoint())
                direct = a.solve(action, (.2,))
                resumed = b.solve(action, (.2,))
                np.testing.assert_array_equal(direct.beam_positions, resumed.beam_positions)
                balance(a, direct)
                a.rebase_rotations(direct.generation)
                b.close()
                b = ss.create_analysis(definition=definition(kind))
                b.restore(a.checkpoint())
                last, restored = a.solve(action, (.3,)), b.solve(action, (.3,))
                np.testing.assert_array_equal(last.beam_positions, restored.beam_positions)
                balance(a, last)
                reports.append(dict(kind=kind, mode=mode, status='completed_under_proposal',
                    generation=last.generation, factors=list(last.accepted_factors)))
            except Exception as error:
                reports.append(dict(kind=kind, mode=mode, status='failed_under_proposal',
                    error=repr(error), generation=a._generation))
            finally:
                a.close(); b.close()
    finally:
        finite._linear_equilibrium = original
    print(json.dumps(dict(qualification=False, product_assessment_unchanged=True,
                         controls='passed', reports=reports), indent=2))


if __name__ == '__main__':
    main()
