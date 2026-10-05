"""Small real-kernel control for opt-in development compilation cache reuse."""
import os

import numpy as np
import pytest


def test_real_compiled_kernel_matches_reference():
    from anysolver.jit_compiler import JIT_ENABLED
    from anysolver.vectorized_stiffness import _cross3

    if not JIT_ENABLED:
        pytest.skip("compiled-cache control requires the Numba backend")
    a = np.array([2.0, -3.0, 5.0])
    b = np.array([-7.0, 11.0, 13.0])
    np.testing.assert_array_equal(_cross3(a, b), np.cross(a, b))
    if os.environ.get("NUMBA_DISABLE_JIT") == "0":
        assert _cross3.signatures, "requested compiled route must actually execute"
        if os.environ.get("ANYSOLVER_EXPECT_DEVELOPMENT_CACHE_HIT") == "1":
            assert sum(_cross3._cache_hits.values()) > 0, "fresh process did not reuse the compiled cache"
