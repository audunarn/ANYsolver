"""Bounded inert arc-length contact result exports; no solver restoration."""
from __future__ import annotations
from dataclasses import dataclass, fields
import hashlib
from types import MappingProxyType
import numpy as np
from . import transient_results_archive as codec
from . import static_results_archive as static

SCHEMA = 'ANYSOLVER_ARC_CONTACT_RESULTS_ARCHIVE_V1'
MAX_BYTES = codec.MAX_BYTES
CONVENTIONS = MappingProxyType({**dict(codec.CONVENTIONS),
    'analysis': 'arc_length_contact',
    'steps': 'accepted_increments_with_producer_indices',
    'snapshots': 'committed_generalized_displacement_and_material_data',
    'load_factor': 'producer_arc_proportional_parameter',
    'arc_radius': 'producer_spherical_metric_radius',
    'peaks': 'producer_peak_load_factor_index_and_accepted_step_flags'})
ArcContactArchiveError = codec.TransientContactArchiveError


def _types():
    from anysolver.arc_length import ArcLengthResult, ArcLengthStep
    from anysolver.nonlinear_static import NonlinearIncrementSnapshot
    _, records = codec._types()
    records = dict(records)
    for cls in (ArcLengthStep, NonlinearIncrementSnapshot):
        records[cls.__module__ + '.' + cls.__qualname__] = cls
    return ArcLengthResult, records


def _vector(value, width=None):
    if type(value) is not np.ndarray or value.ndim != 1 or value.size < 1 or \
            value.dtype.kind not in 'fi' or not np.all(np.isfinite(value)) or \
            (width is not None and value.size != width):
        codec._fail('invalid static generalized displacement vector')


def _state(value):
    if type(value) is not dict or any(type(k) is not int or k < 0 for k in value):
        codec._fail('material states require nonnegative integer element identities')


def _roles(cls, data):
    if cls.__module__ != 'anysolver.arc_length':
        return static._roles(cls, data)
    for key,value in data.items():
        if key in ('step_index','iterations','retries'):
            if (type(value) is not int and not isinstance(value,np.integer)) or isinstance(value,(bool,np.bool_)) or value < 0:
                codec._fail('invalid arc record counter')
        elif key == 'is_peak':
            if type(value) not in (bool,np.bool_): codec._fail('invalid arc peak flag')
        elif key == 'support_reactions':
            if type(value) is not dict: codec._fail('invalid support mapping')
            for name,vector in value.items():
                if type(name) is not str or type(vector) not in (tuple,list) or len(vector) != 6:
                    codec._fail('invalid generalized support dimensions')
                for component in vector: codec._number(component)
        else:
            codec._number(value)


def _diagnostics(value):
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is str and key in ('integration_force','target_force','shell_force','rigid_force',
                    'beam_force','integration_moment','target_moment','shell_moment','rigid_moment',
                    'beam_moment','wrench_origin_m'):
                if type(item) not in (tuple,list) or len(item) != 3: codec._fail('invalid diagnostic wrench vector')
                for component in item: codec._number(component)
            elif key in ('minimum_gap','sampled_overlap_gap','minimum_physical_gap'):
                if item is not None: codec._number(item, gap=True)
            elif key == 'gap_tolerance_met':
                if type(item) not in (bool,np.bool_): codec._fail('invalid diagnostic flag')
            _diagnostics(item)
    elif type(value) in (tuple,list):
        for item in value: _diagnostics(item)


def _validate(data):
    producer, _ = _types()
    if type(data) is not dict or set(data) != {f.name for f in fields(producer)}:
        codec._fail('arc producer field inventory mismatch')
    if type(data['status']) is not str or not data['status']:
        codec._fail('invalid arc result status')
    _vector(data['displacements'])
    codec._number(data['load_factor'])
    codec._number(data['peak_load_factor'])
    peak = data['peak_step_index']
    if peak is not None and ((type(peak) is not int and not isinstance(peak,np.integer)) or
            isinstance(peak,(bool,np.bool_)) or peak < 0):
        codec._fail('invalid peak step identity')
    _state(data['element_states'])
    if type(data['info']) is not dict or not any(
            key in data['info'] for key in ('general_contact', 'general_contact_history')):
        codec._fail('ordinary arc contact diagnostics required; no-contact result is unsupported')
    _diagnostics(data['info'])
    if data['restart_checkpoint'] is not None and type(data['restart_checkpoint']) is not dict:
        codec._fail('arc checkpoint must be mapping or None')
    for name, clsname, container in (('steps', 'anysolver.arc_length.ArcLengthStep', list),
                                   ('snapshots', 'anysolver.nonlinear_static.NonlinearIncrementSnapshot', tuple)):
        rows = data[name]
        if type(rows) is not container:
            codec._fail('invalid arc record sequence')
        previous = -1
        for row in rows:
            if type(row) is not dict or row.get('record_type') != clsname:
                codec._fail('invalid arc record role')
            values = row['fields']
            index = values['step_index']
            if type(index) is not int or index < 0 or index <= previous:
                codec._fail('invalid accepted record ordering')
            previous = index
            if name == 'snapshots':
                _vector(values['displacements'], data['displacements'].size)
                _state(values['element_states'])
            else:
                expected = {key:(int(value) if key in ('step_index','iterations','retries') else
                    bool(value) if key=='is_peak' else
                    {str(k):[float(x) for x in v] for k,v in value.items()} if key=='support_reactions' else
                    float(value)) for key,value in values.items()}
                summary = row['summary']
                if type(summary) is not dict or set(summary) != set(expected):
                    codec._fail('arc step summary inventory mismatch')
                for key in expected:
                    if codec._canonical(codec._encode(summary[key],codec._Budget(MAX_BYTES),{})) != codec._canonical(codec._encode(expected[key],codec._Budget(MAX_BYTES),{})):
                        codec._fail('arc step summary differs from exact fields')
                reactions = values['support_reactions']
                if type(reactions) is not dict:
                    codec._fail('invalid support reaction mapping')
                for key, vector in reactions.items():
                    if type(key) is not str or type(vector) not in (list, tuple) or len(vector) != 6:
                        codec._fail('invalid generalized support reaction dimensions')
                    for value in vector: codec._number(value)


def _read(raw, cap):
    return codec._read(raw, cap, schema=SCHEMA, conventions=CONVENTIONS,
                       records=_types()[1], validator=_validate, record_roles=_roles)


@dataclass(frozen=True, slots=True)
class ContactArcArchive:
    """Immutable canonical bytes; each decode returns detached inert data."""
    _raw: bytes
    _max_bytes: int = MAX_BYTES

    def __post_init__(self):
        _read(self._raw, codec._limit(self._max_bytes))

    @property
    def sha256(self):
        return hashlib.sha256(self._raw).hexdigest()

    def to_bytes(self):
        return self._raw

    def to_dict(self):
        return _read(self._raw, self._max_bytes)


def serialize_arc_contact_results(results, *, max_bytes=MAX_BYTES):
    """Export all ten producer fields using the existing exact numeric codec."""
    cap = codec._limit(max_bytes)
    producer, records = _types()
    if type(results) is not producer:
        codec._fail('exact ArcLengthResult required')
    try: data = {f.name: getattr(results, f.name) for f in fields(results)}
    except AttributeError: codec._fail('incomplete ArcLengthResult producer')
    from anysolver.arc_length import ArcLengthStep
    if type(data['steps']) is not list: codec._fail('arc steps must be list')
    for step in data['steps']:
        if type(step) is not ArcLengthStep: codec._fail('exact accepted step required')
        try: step_data = {f.name:getattr(step,f.name) for f in fields(step)}
        except AttributeError: codec._fail('incomplete accepted arc step')
        _roles(type(step), step_data)
    data = codec._prepare_material_data(data, cap)
    snapshots = data['snapshots']
    if type(snapshots) is not tuple:
        codec._fail('arc snapshots must be tuple')
    budget = codec._Budget(cap)
    data['snapshots'] = ()
    payload = codec._encode(data, budget, records)
    nodes = []
    from anysolver.nonlinear_static import NonlinearIncrementSnapshot
    for snapshot in snapshots:
        if type(snapshot) is not NonlinearIncrementSnapshot:
            codec._fail('exact committed snapshot required')
        try: values = {f.name: getattr(snapshot, f.name) for f in fields(snapshot)}
        except AttributeError: codec._fail('incomplete committed snapshot')
        values = codec._prepare_material_data(values, max(1, cap-budget.bytes))
        # Encode fields before a bounded known-producer summary. No constructor,
        # deepcopy or executable type restoration is invoked by the reader.
        encoded = codec._encode(values, budget, records, 2)
        nodes.append({'tag': 'record', 'record_type': 'anysolver.nonlinear_static.NonlinearIncrementSnapshot',
                      'fields': encoded,
                      'summary': codec._encode(snapshot.to_dict(), budget, records, 2)})
    next(node for key, node in payload['items'] if key == 'snapshots')['items'] = nodes
    document = dict(schema=SCHEMA, version=1, conventions=dict(CONVENTIONS), payload=payload)
    document['sha256'] = hashlib.sha256(codec._canonical(document)).hexdigest()
    raw = codec._canonical(document)
    if len(raw) > cap: codec._fail('archive encoded byte limit exceeded')
    _read(raw, cap)
    return raw


def read_arc_contact_results(raw, *, max_bytes=MAX_BYTES):
    return ContactArcArchive(raw, codec._limit(max_bytes))
