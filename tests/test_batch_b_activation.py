from anysolver.jit_compiler import JIT_ENABLED
from anysolver.nonlinear_performance_bootstrap import nonlinear_performance_status
from anysolver.nonlinear_static import _ensure_nonlinear_acceleration


def test_batch_b_activation_policy():
    _ensure_nonlinear_acceleration()
    status = nonlinear_performance_status()
    assert status["installed"] is True
    assert status["batch_b"]["eligible"] is JIT_ENABLED
    assert status["batch_b"]["installed"] is JIT_ENABLED
