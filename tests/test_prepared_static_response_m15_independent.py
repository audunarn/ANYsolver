"""Independent exact controls for relation sufficiency, not native execution."""
from fractions import Fraction as F
import math

from prepared_static_response_m15_relation_limit import admitted, counterexample


def relation_holds(T, x, b):
    # Re-derive the asserted contract without calling the author's checker.
    n = len(x)
    u, mu = F(1, 2**53), F(1, 2**1074)
    k = 2*n + 2
    gamma = k*u/(1-k*u)
    for i in range(n):
        r = abs(sum(T[i][j]*x[j] for j in range(n))-b[i])
        magnitude = sum(abs(T[i][j]*x[j]) for j in range(n))+abs(b[i])
        if r > gamma*magnitude + k*mu*(1+abs(T[i][i]))/(1-k*u):
            return False
    return True


def test_exact_admission_and_output_error_independently():
    m, e = F(2**20), F(1, 2**31)
    T, b, x = [[F(1), m], [F(0), F(1)]], [F(0), F(1)], [-m+e, F(1)]
    assert all(F(float(v)) == v for v in x)
    assert relation_holds(T, x, b)
    assert x[0]+m*x[1] == e > F(float(1e-12))
    assert counterexample()['output_error'] == float(e)


def test_relation_can_admit_reversal_of_distinct_governors():
    m, e = F(2**20), F(1, 2**31)
    T = [[F(1), m], [F(0), F(1)]]
    # True outputs: case 0 = 0, case 1 = e/2. Both RHS are represented.
    loads = [[F(0), F(1)], [e/2, F(1)]]
    candidates = [[-m+e, F(1)], [-m+e/2, F(1)]]
    assert all(relation_holds(T, x, b) for x, b in zip(candidates, loads))
    assert all(F(float(v)) == v for x in candidates for v in x)
    exact_outputs = [b[0] for b in loads]
    allowed_outputs = [x[0]+m*x[1] for x in candidates]
    assert max(range(2), key=exact_outputs.__getitem__) == 1
    assert max(range(2), key=allowed_outputs.__getitem__) == 0


def test_relation_is_not_unconditional_and_has_represented_boundary():
    m = F(2**20)
    T, b = [[F(1), m], [F(0), F(1)]], [F(0), F(1)]
    for e, expected in [(F(1, 2**31), True), (F(1, 2**27), False)]:
        x = [-m+e, F(1)]
        assert F(float(x[0])) == x[0]
        assert relation_holds(T, x, b) is expected
        assert admitted(T, x, b)[0] is expected


def test_rounding_limit_is_binary64_and_underflow_term_is_not_zero():
    assert F(math.ulp(1.0)/2) == F(1, 2**53)
    mu = F.from_float(math.nextafter(0.0, 1.0))
    assert mu == F(1, 2**1074)
    T, x, b = [[F(float(1e308))]], [F(0)], [F(float(1e-20))]
    assert relation_holds(T, x, b)
    assert b[0] > 4*mu
