"""Parity + timing of the batched prototype against the production Q4/S3 Jet2 kernel.
Run from an ANYsolver checkout at be5ea482 (or with its src/ on PYTHONPATH):
    python bench_q4_s3_kernel.py
"""
import time, numpy as np
from anysolver.general_contact.q4_s3_overlap_derivatives import q4_s3_overlap_derivatives as base
from q4_s3_batched_jet_prototype import q4_s3_overlap_derivatives as proto

KW = dict(area_tolerance=1e-9, weighted_gap_tolerance=1e-10, maximum_triangles=300,
          allow_warped_source=True, support_gradient_tolerance=1e-5, support_hessian_tolerance=1e-5,
          weighted_gap_gradient_tolerance=1e-5, weighted_gap_hessian_tolerance=1e-5)   # D1 script settings

def pose(warp=2e-7):
    """One 4x8-mesh source Q4 straddling the rim of the fixed S3 target (model coordinates)."""
    x0, y0, hx, hy = 0.6, 0.9, 0.25, 0.125
    ref = np.array([[x0, y0, .04004], [x0+hx, y0, .04004], [x0+hx, y0+hy, .04004], [x0, y0+hy, .04004]])
    cur = ref.copy(); cur[:, 2] += np.array([-3e-5, -3.4e-5+warp, -3.6e-5, -3.1e-5])
    tgt = np.array([[0.0, 0.1, 0.0], [1.3, 1.0, 0.0], [0.0, 1.0, 0.0]])
    return ref, cur, tgt

FIELDS = ('reference_support', 'reference_weighted_gap', 'support_gradient', 'support_hessian',
          'weighted_gap_gradient', 'weighted_gap_hessian')
if __name__ == "__main__":
    rng = np.random.default_rng(1); worst = 0.0; n = 0
    for _ in range(12):
        ref, cur, tgt = pose(rng.uniform(-5e-7, 5e-7))
        cur = cur + rng.uniform(-2e-3, 2e-3, cur.shape)*np.array([1, 1, 0.01])
        a = base(ref, cur, tgt, **KW); b = proto(ref, cur, tgt, **KW)
        assert a.branch_signature == b.branch_signature and a.integration_triangles == b.integration_triangles
        for f in FIELDS:
            x, y = getattr(a, f), getattr(b, f)
            worst = max(worst, np.max(np.abs(x-y))/np.max(np.abs(x)))
        n += 1
    print("parity over %d poses: worst relative max-abs difference %.2e" % (n, worst))
    ref, cur, tgt = pose()
    for fn, name in ((base, "production Jet2"), (proto, "batched prototype")):
        fn(ref, cur, tgt, **KW); t = time.perf_counter()
        for _ in range(5): fn(ref, cur, tgt, **KW)
        print("%-18s %.4f s/pair" % (name, (time.perf_counter()-t)/5))
