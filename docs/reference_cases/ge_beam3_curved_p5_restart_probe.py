"""Strict research-only nonlinear checkpoint codec; no production restart API.

Expected geometry/section/order come from the caller, never executable payload
metadata. Only a fully verified new model is returned. Digests provide integrity
and identity checks, not authenticity or proof of the complete loading history.
"""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import (
    NonlinearCantileverHistoryProbe, NonlinearPathState, NonlinearPathTrial, digest,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import BeamStationTrial, NonlinearCondensedResponse
from docs.reference_cases.ge_beam3_curved_p5_section_probe import SectionHistory, SectionResponse, _history


SCHEMA = 'GE_BEAM3_P5_RESEARCH_HISTORY_RESTART_V1'
MAX_BYTES = 1048576


class RestartError(ValueError):
    """Checkpoint rejected before exposing a restored mutable model."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                       ensure_ascii=True, default=lambda value: value.tolist())+'\n').encode('ascii')


def _sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _identity(model):
    names = ['anysolver.ge_beam3_curved_reference', 'anysolver._ge_beam3_mixed_ad']
    names += ['docs.reference_cases.ge_beam3_curved_p5_'+suffix for suffix in (
        'algebra_probe', 'finite_probe', 'section_probe', 'nonlinear_mixed_probe', 'history_path_probe', 'restart_probe')]
    sources = {name: hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest() for name in names}
    law = model._section
    points, _ = np.polynomial.legendre.leggauss(model._order)
    return {'candidate': 'CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1',
        'production_qualified': False, 'scope': 'ONE_MACRO_CLAMPED_ELASTIC_DIRECTED_HARDENING_RESEARCH',
        'reference': {'coordinates': model._reference.coordinates.tolist(), 'frames': model._reference.nodal_triads.tolist()},
        'section': {'elastic': law._elastic.tolist(), 'direction': law._direction.tolist(),
                    'yield_force': law._yield, 'hardening': law._hardening},
        'order': model._order,
        'stations': [[c, i, float(c-1+(p+1)/2)] for c in (0, 1) for i, p in enumerate(points)],
        'update': 'SPATIAL_MULTIPLICATIVE_MATRICES_NO_ACCUMULATED_VECTOR',
        'runtime': {'python': platform.python_version(), 'numpy': np.__version__,
                    'platform': sys.platform, 'machine': platform.machine()},
        'implementation_sources': sources}


def dumps(model):
    if type(model) is not NonlinearCantileverHistoryProbe or model._pending is not None:
        raise RestartError('exact research model with no pending trial required')
    state, accepted = model._checkpoint
    if accepted is not None:
        model.replay()
    body = {'schema': SCHEMA, 'identity': _identity(model), 'state': asdict(state),
            'accepted': None if accepted is None else asdict(accepted)}
    payload = canonical({**body, 'payload_sha256': _sha(body)})
    if len(payload) > MAX_BYTES:
        raise RestartError('checkpoint exceeds byte limit')
    # The same validation is used for export and import; malformed private
    # state cannot be published simply because its checksum was recomputed.
    loads(payload, model._reference, model._section, order=model._order)
    return payload


def _keys(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise RestartError('exact checkpoint schema required')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RestartError('duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise RestartError('nonfinite JSON constant')


def _parse(payload):
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_BYTES:
        raise RestartError('bounded checkpoint bytes required')
    quoted = escaped = False
    depth = 0
    for byte in payload:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 32:
                raise RestartError('checkpoint nesting limit exceeded')
        elif byte in (93, 125):
            depth -= 1
    record = json.loads(payload.decode('ascii'), object_pairs_hook=_pairs, parse_constant=_constant)
    if canonical(record) != payload:
        raise RestartError('strict canonical JSON required')
    _keys(record, ('schema', 'identity', 'state', 'accepted', 'payload_sha256'))
    body = {key: value for key, value in record.items() if key != 'payload_sha256'}
    if record['schema'] != SCHEMA or record['payload_sha256'] != _sha(body):
        raise RestartError('schema or payload hash mismatch')
    return record


def _decode(value, schema):
    if schema is float:
        if type(value) is not float or not math.isfinite(value):
            raise RestartError('finite JSON float required; no coercion')
        return value
    if schema is bool:
        if type(value) is not bool:
            raise RestartError('JSON boolean required')
        return value
    kind, specification = schema
    if kind == 'integer':
        if type(value) is not int or not 0 <= value <= specification:
            raise RestartError('bounded JSON integer required')
        return value
    if kind == 'array':
        shape = specification
        def nested(item, dimensions):
            if not dimensions:
                return _decode(item, float)
            if type(item) is not list or len(item) != dimensions[0]:
                raise RestartError('exact array shape required')
            return [nested(part, dimensions[1:]) for part in item]
        made = np.array(nested(value, shape), dtype=float)
        made.setflags(write=False)
        return made
    if kind == 'sequence':
        count, item_schema = specification
        if type(value) is not list or len(value) != count:
            raise RestartError('exact station/history count required')
        return tuple(_decode(item, item_schema) for item in value)
    cls, fields = kind, specification
    _keys(value, fields)
    decoded = cls(**{key: _decode(value[key], item) for key, item in fields.items()})
    return _history(decoded) if cls is SectionHistory else decoded


def _schemas(order):
    array = lambda *shape: ('array', shape)
    integer = lambda maximum: ('integer', maximum)
    history = (SectionHistory, {'plastic_coordinate': float, 'accumulated': float})
    histories = ('sequence', (2*order, history))
    point = (SectionResponse, {'origin': history, 'history': history, 'strain': array(6),
        'resultants': array(6), 'tangent': array(6, 6), 'incremental_potential': float,
        'stored_energy': float, 'dissipation_increment': float, 'plastic_active': bool})
    station = (BeamStationTrial, {'cell': integer(1), 'index': integer(order-1),
        'reference_coordinate': float, 'response': point})
    response = (NonlinearCondensedResponse, {'potential': float, 'residual': array(18), 'tangent': array(18, 18),
        'local_rotations': array(2, 3, 3), 'moments': array(2, 2, 3),
        'stations': ('sequence', (2*order, station)), 'local_residual_norm': float,
        'iterations': integer(25), 'evaluations': integer(64)})
    state = (NonlinearPathState, {'epoch': integer(2147483647), 'positions': array(3, 3),
        'frames': array(3, 3, 3), 'forces': array(3, 3), 'histories': histories})
    trial = (NonlinearPathTrial, {'origin_epoch': integer(2147483646), 'positions': array(3, 3),
        'frames': array(3, 3, 3), 'forces': array(3, 3), 'origins': histories, 'response': response,
        'residual_norm': float, 'iterations': integer(16), 'mixed_evaluations': integer(256)})
    return state, trial


def loads(payload, reference, section, *, order=24):
    """Validate into a fresh model; no caller-owned state is modified on failure."""
    try:
        record = _parse(payload)
        staged = NonlinearCantileverHistoryProbe(reference, section, order=order)
        if canonical(record['identity']) != canonical(_identity(staged)):
            raise RestartError('expected geometry/section/implementation/runtime identity mismatch')
        state_schema, trial_schema = _schemas(order)
        state = _decode(record['state'], state_schema)
        if state.epoch == 0:
            if record['accepted'] is not None or digest(state) != digest(staged.committed):
                raise RestartError('initial checkpoint must be the exact stress-free state')
            return staged
        accepted = _decode(record['accepted'], trial_schema)
        if state.epoch != accepted.origin_epoch+1:
            raise RestartError('accepted epoch linkage mismatch')
        for name in ('positions', 'frames', 'forces'):
            if not np.array_equal(getattr(state, name), getattr(accepted, name)):
                raise RestartError('committed/accepted geometry or load mismatch')
        reconstructed = staged._reconstruct(accepted)
        if digest(reconstructed) != digest(accepted.response):
            raise RestartError('accepted-origin mechanics replay mismatch')
        expected_histories = tuple(s.response.history for s in reconstructed.stations)
        if state.histories != expected_histories:
            raise RestartError('committed station history mismatch')
        external = np.column_stack((state.forces, np.zeros((3, 3)))).ravel()
        norm = staged._norm(reconstructed.residual-external, state.forces)
        if (norm > 1e-11 or norm != accepted.residual_norm or reconstructed.local_residual_norm > 1e-11
                or not np.array_equal(state.positions[0], staged._reference.coordinates[0])
                or not np.array_equal(state.frames[0], staged._reference.nodal_triads[0])):
            raise RestartError('checkpoint equilibrium or clamp mismatch')
        staged._checkpoint = (deepcopy(state), deepcopy(accepted))
        return staged
    except RestartError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError,
            UnicodeError, np.linalg.LinAlgError) as exc:
        raise RestartError('invalid research restart') from exc


def write_exclusive(path, model):
    """Publish a complete same-directory staged file without overwriting.

    Atomic hard-link publication is required; unsupported filesystems fail
    closed. This is not a claim of power-loss durability of directory metadata.
    """
    payload = dumps(model)
    target = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.ge-b3-restart-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        os.unlink(temporary)
    return hashlib.sha256(payload).hexdigest()
