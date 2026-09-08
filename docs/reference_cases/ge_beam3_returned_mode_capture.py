"""Development-only observation of failed mode validation; no accepted modes.

Trace the unchanged kernel's final validation exception, then compare exact
dyadic congruences before and after physical-vector expansion. This is an
arithmetic diagnostic, not an independent mechanical qualification oracle.
"""
import sys
import numpy as np
from anysolver._native_relative_factor_chain_modes import solve_relative_factor_chain_modes
from anysolver._dyadic_bilinear import _capture, _multiply, _transpose, _add, _rounded

FAILURES = ('physical modal mass normalization',
            'original signed bilinear Ritz identity failed')
ARRAYS = ('left', 'right', 'g', 'b', 'mapping', 'h', 'mass', 'intervals',
          'widths', 'c', 'values', 'modes', 'speed')


def capture_failure(operation):
    if sys.gettrace() is not None:
        raise ValueError('diagnostic requires exclusive thread trace ownership')
    captured = {}
    target = solve_relative_factor_chain_modes.__code__
    def trace(frame, event, arg):
        if frame.f_code is not target:
            return None
        if event == 'exception' and type(arg[1]) is ValueError and str(arg[1]) in FAILURES:
            if captured:
                raise ValueError('duplicate final validation capture')
            captured.update({key: np.array(frame.f_locals[key], copy=True) for key in ARRAYS})
            captured['failure'] = str(arg[1])
        return trace
    sys.settrace(trace)
    try:
        operation()
    except ValueError as exc:
        if not captured or captured['failure'] != str(exc):
            raise
    else:
        raise ValueError('expected preserved validation failure did not occur')
    finally:
        sys.settrace(None)
    return captured


def analyze(data, checkpoint=lambda: None):
    """Separate complete-map rounding, extraction and physical expansion.

    All matrix products below use exact integer/dyadic arithmetic until the
    final comparison matrix is rounded once. No post-hoc normalization.
    """
    d = {key: _capture(data[key], checkpoint) for key in
         ('left', 'right', 'g', 'b', 'mapping', 'h', 'mass', 'c', 'modes')}
    def mul(a, b):
        return _multiply(a, b, checkpoint)
    def congruence(a, v):
        return mul(_transpose(v), mul(a, v))
    def original(v):
        strain = mul(d['left'], mul(d['right'], v))
        speed = mul(d['b'], v)
        return (_rounded(_add(mul(_transpose(strain), strain), congruence(d['g'], v))),
                _rounded(mul(_transpose(speed), speed)))
    nested = mul(d['mapping'], d['c'])
    reduced_h = _rounded(congruence(d['h'], d['c']))
    reduced_m = _rounded(congruence(d['mass'], d['c']))
    nested_h, nested_m = original(nested)
    physical_h, physical_m = original(d['modes'])
    values = data['values']
    scale = np.maximum(1., np.sqrt(abs(values))[:, None]*np.sqrt(abs(values))[None, :])
    rows = {}
    for name, h, m in (('reduced', reduced_h, reduced_m),
                       ('unrounded_expansion', nested_h, nested_m),
                       ('physical_binary64', physical_h, physical_m)):
        error = abs(h-m*values[None, :])/scale
        rows[name] = dict(energy=h, kinetic_gram=m,
            mass_error=float(np.linalg.norm(m-np.eye(len(values)))),
            signed_ritz_error=float(np.max(error)),
            worst_entry=list(map(int, np.unravel_index(np.argmax(error), error.shape))))
    rows['rounding_effect'] = dict(
        reduced_to_nested_energy=float(np.max(abs(nested_h-reduced_h)/scale)),
        nested_to_physical_energy=float(np.max(abs(physical_h-nested_h)/scale)),
        reduced_to_nested_mass=float(np.linalg.norm(nested_m-reduced_m)),
        nested_to_physical_mass=float(np.linalg.norm(physical_m-nested_m)))
    return rows
