"""Explicit connected-model research restart; no production serialization API.

Caller-supplied model authority is never inferred from payload metadata. Loading
stages a fresh model and checks every accepted-origin element before returning.
Hashes bind integrity, not authenticity or the complete preceding load history.
"""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

import numpy as np

from docs.reference_cases import ge_beam3_curved_p5_restart_probe as single
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyState, AssemblyTrial, AssemblyResponse,
    AssemblyTransactionError,
)
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _frames
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe


SCHEMA = 'GE_BEAM3_P5_RESEARCH_ASSEMBLY_RESTART_V1'
MAX_BYTES = 16*1024*1024
RestartError = single.RestartError
canonical = single.canonical


def _sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _identity(model):
    if (type(model) is not NonlinearAssemblyHistoryProbe
            or any(type(s) is not DirectedHardeningSectionProbe for s in model._sections)):
        raise RestartError('exact research assembly and directed-hardening sections required')
    names = ['anysolver.ge_beam3_curved_reference', 'anysolver._ge_beam3_mixed_ad']
    names += ['docs.reference_cases.ge_beam3_curved_p5_'+suffix for suffix in (
        'algebra_probe', 'finite_probe', 'section_probe', 'nonlinear_mixed_probe',
        'history_path_probe', 'restart_probe', 'assembly_history_probe', 'assembly_restart_probe')]
    sources = {name: hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest() for name in names}
    points, _ = np.polynomial.legendre.leggauss(model._order)
    return {'candidate': 'CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1',
        'production_qualified': False, 'scope': 'CONNECTED_CLAMPED_DIRECTED_HARDENING_RESEARCH',
        'connectivity': [r.tolist() for r in model._maps], 'fixed_nodes': model._fixed.tolist(),
        'references': [{'coordinates': r.coordinates.tolist(), 'frames': r.nodal_triads.tolist()}
                       for r in model._references],
        'sections': [{'elastic': s._elastic.tolist(), 'direction': s._direction.tolist(),
                      'yield_force': s._yield, 'hardening': s._hardening} for s in model._sections],
        'extent': model._extent, 'order': model._order,
        'stations': [[c, i, float(c-1+(p+1)/2)] for c in (0, 1) for i, p in enumerate(points)],
        'update': 'SHARED_SPATIAL_U_ELEMENT_Q_EQUALS_U_R0',
        'runtime': {'python': platform.python_version(), 'numpy': np.__version__,
                    'platform': sys.platform, 'machine': platform.machine()},
        'implementation_sources': sources}


def _parse(payload):
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_BYTES:
        raise RestartError('bounded checkpoint bytes required')
    depth = 0
    quoted = escaped = False
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
    record = json.loads(payload.decode('ascii'), object_pairs_hook=single._pairs,
                        parse_constant=single._constant)
    if canonical(record) != payload:
        raise RestartError('strict canonical JSON required')
    single._keys(record, ('schema', 'identity', 'state', 'accepted', 'payload_sha256'))
    body = {k: v for k, v in record.items() if k != 'payload_sha256'}
    if record['schema'] != SCHEMA or record['payload_sha256'] != _sha(body):
        raise RestartError('assembly schema or payload hash mismatch')
    return record


def _schemas(model):
    # Share only the frozen scalar/history/element wire schemas. The former
    # one-element model identity and restore path are deliberately not reused.
    old_state, old_trial = single._schemas(model._order)
    history = old_state[1]['histories']
    element = old_trial[1]['response']
    array = lambda *s: ('array', s)
    integer = lambda n: ('integer', n)
    count, nodes = len(model._maps), model._nodes
    histories = ('sequence', (count, history))
    response = (AssemblyResponse, {'potential': float, 'residual': array(6*nodes),
        'tangent': array(6*nodes, 6*nodes), 'elements': ('sequence', (count, element))})
    state = (AssemblyState, {'epoch': integer(2147483647), 'positions': array(nodes, 3),
        'rotations': array(nodes, 3, 3), 'forces': array(nodes, 3), 'histories': histories})
    trial = (AssemblyTrial, {'origin_epoch': integer(2147483646), 'positions': array(nodes, 3),
        'rotations': array(nodes, 3, 3), 'forces': array(nodes, 3), 'origins': histories,
        'response': response, 'residual_norm': float, 'iterations': integer(16),
        'mixed_evaluations': integer(256*count)})
    return state, trial


def loads(payload, references, connectivity, sections, *, fixed_nodes=(0,), order=24, extent='SMALL8'):
    """Return a fresh fully checked model, or raise without publishing any state."""
    try:
        record = _parse(payload)
        staged = NonlinearAssemblyHistoryProbe(references, connectivity, sections,
            fixed_nodes=fixed_nodes, order=order, extent=extent)
        if canonical(record['identity']) != canonical(_identity(staged)):
            raise RestartError('expected assembly/implementation/runtime identity mismatch')
        state_schema, trial_schema = _schemas(staged)
        state = single._decode(record['state'], state_schema)
        if state.epoch == 0:
            if record['accepted'] is not None or digest(state) != digest(staged.committed):
                raise RestartError('initial checkpoint must be exact stress-free assembly')
            return staged
        accepted = single._decode(record['accepted'], trial_schema)
        if state.epoch != accepted.origin_epoch+1:
            raise RestartError('accepted epoch linkage mismatch')
        for name in ('positions', 'rotations', 'forces'):
            if canonical(getattr(state, name)) != canonical(getattr(accepted, name)):
                raise RestartError('committed/accepted geometry or load mismatch')
        _frames(state.rotations, staged._nodes, 'restored shared rotations')
        _, histories = staged._validated(accepted)
        if state.histories != histories:
            raise RestartError('committed element/station history mismatch')
        # _validated reconstructs all elements, scatter and equilibrium with
        # accepted origins and saved local unknowns, never a Newton solve.
        # Nothing caller-visible is published until even the last element passes.
        staged._checkpoint = (deepcopy(state), deepcopy(accepted))
        return staged
    except RestartError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError,
            UnicodeError, AssemblyTransactionError, np.linalg.LinAlgError) as exc:
        raise RestartError('invalid assembled research restart') from exc


def dumps(model):
    try:
        identity = _identity(model)
        if model._pending is not None:
            raise RestartError('discard or commit pending trial before export')
        state, accepted = model._checkpoint
        body = {'schema': SCHEMA, 'identity': identity, 'state': asdict(state),
                'accepted': None if accepted is None else asdict(accepted)}
        payload = canonical({**body, 'payload_sha256': _sha(body)})
        # Validate both export and import through the same fresh-model path. This
        # rejects private-state corruption without altering the exporting instance.
        loads(payload, model._references, [r.tolist() for r in model._maps], model._sections,
              fixed_nodes=model._fixed.tolist(), order=model._order, extent=model._extent)
        return payload
    except RestartError:
        raise
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError) as exc:
        raise RestartError('invalid assembled research export') from exc


def write_exclusive(path, model):
    """Same-directory staging and exclusive publication, not power-loss durability."""
    payload = dumps(model)
    target = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.ge-b3-assembly-restart-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        os.unlink(temporary)
    return hashlib.sha256(payload).hexdigest()
