"""Read-only geometric comparison, not a mechanics replay or qualification.

Reuse the separately implemented planar continuum equations without importing
ANYsolver. Uniform stiffness normalization changes force units, not geometry,
quadrature, tolerances or the branch boundary conditions. A symmetric spatial
snapshot does not by itself prove it follows the same continuum branch.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum

import numpy as np
from docs.reference_cases import ge_beam3_curved_p5_arch_reference as continuum


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError('duplicate key')
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError('nonfinite JSON')


def preserved(raw, expected_sha256):
    """Validate preserved bytes and hash chain only; do not replay mechanics."""
    if type(raw) is not bytes or len(raw) > 2*1024*1024 or sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('preserved external packet hash/size')
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_bad_constant)
    if canonical(value) != raw: raise ValueError('canonical packet required')
    if value['schema'] != 'GE_BEAM3_PHYSICAL_FIBRE_TRANSLATION_CONTROL_CHAIN_V1':
        raise ValueError('foreign checkpoint')
    if value['program']['schema'] != 'GE_BEAM3_KINEMATIC_SEEDED_SPATIAL_NEWTON_FIBRE_CONTROL_V1':
        raise ValueError('foreign controller')
    body = {k: v for k, v in value.items() if k != 'checkpoint_sha256'}
    if sha256(canonical(body)).hexdigest() != value['checkpoint_sha256']: raise ValueError('checkpoint seal')
    if type(value['completed_targets']) is not int or value['completed_targets'] != len(value['records']):
        raise ValueError('record count')
    previous = None
    for index, row in enumerate([value['initial'], *value['records']]):
        body = {k: v for k, v in row.items() if k != 'record_sha256'}
        if sha256(canonical(body)).hexdigest() != row['record_sha256']: raise ValueError('record seal')
        if type(row['target']) is not int or row['target'] != index: raise ValueError('record order')
        if previous is not None and row['previous_sha256'] != previous: raise ValueError('record chain')
        previous = row['record_sha256']
    return value


def _array(value, shape):
    flat = np.asarray(value, dtype=object)
    if flat.shape != shape or any(type(v) not in (int, float) for v in flat.flat):
        raise ValueError('numeric shape required; booleans forbidden')
    result = np.asarray(value, dtype=float)
    if not np.isfinite(result).all(): raise ValueError('finite values required')
    return result


def geometry_diagnostics(mechanical):
    """Reflection across x=0, with physical e2=+z preserved.

    Q_right = S Q_left D, S=D=diag(-1,1,1): two reflections give a proper
    triad. Cell relative rotations instead obey U_right = S U_left S.
    Position sums/differences retain both high/low parts as exact dyadics.
    """
    count = len(mechanical['positions'])
    if count < 3 or count % 2 != 1: raise ValueError('odd arch node count')
    high = _array(mechanical['positions'], (count, 3))
    low = _array(mechanical['position_low'], (count, 3))
    frames = _array(mechanical['nodal_frames'], (count, 3, 3))
    cells = _array(mechanical['cell_rotations'], ((count-1)//2, 2, 3, 3)).reshape(-1, 3, 3)
    for matrices in (frames, cells):
        if (np.max(abs(matrices.transpose(0, 2, 1)@matrices-np.eye(3))) > 1e-11
                or np.max(abs(np.linalg.det(matrices)-1)) > 1e-11):
            raise ValueError('proper orthogonal frames required')
    paired = [[Fraction(float(h))+Fraction(float(l)) for h, l in zip(a, b)] for a, b in zip(high, low)]
    s = np.diag([-1., 1., 1.])
    position_error = max(abs(float(paired[i][j]-int(s[j, j])*paired[-1-i][j]))
                         for i in range(count) for j in range(3))
    return dict(position_reflection_error=position_error,
        out_of_plane_position=max(abs(float(p[2])) for p in paired),
        nodal_frame_reflection_error=float(np.max(abs(frames-s@frames[::-1]@s))),
        cell_rotation_reflection_error=float(np.max(abs(cells-s@cells[::-1]@s))),
        physical_second_director_error=float(np.max(abs(frames[:, :, 1]-[0., 0., 1.]))))


def normalized_reference(displacement, *, axial, shear, bending, height=.1, previous=None, profile='BVP9'):
    values = (axial, shear, bending)
    if any(type(v) not in (int, float) or not np.isfinite(v) or v <= 0 for v in values):
        raise ValueError('positive finite physical stiffness required')
    scale = max(values)
    if min(v/scale for v in values) <= 0: raise ValueError('normalization underflow')
    reference = continuum.solve(displacement, axial=axial/scale, shear=shear/scale,
        bending=bending/scale, height=height, previous=previous, profile=profile)
    # Keep residual diagnostics in their actual normalized units. Do not
    # relabel them as residuals of an unnormalized collocation solve.
    return scale, reference


def sampled_geometry(reference, reference_x):
    """Use existing stored stations exactly; never interpolate unnoticed."""
    x = np.asarray(reference_x, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all() or np.any(abs(x) > 1): raise ValueError('reference nodes')
    positions, frames = [], []
    for location in x:
        indices = np.flatnonzero(reference.parameter == -abs(location))
        if len(indices) != 1: raise ValueError('reference node is not a stored continuum station')
        px, py, angle, _ = reference.fields[:, indices[0]]
        if location > 0: px, angle = -px, -angle
        tangent = np.array([np.cos(angle), np.sin(angle), 0.])
        second = np.array([0., 0., 1.])
        positions.append([float(px), float(py), 0.])
        frames.append(np.column_stack((tangent, second, np.cross(tangent, second))))
    return np.asarray(positions), np.asarray(frames)


def compare(row, reference_x, scale, reference):
    if (row['displacement_target'] != reference.displacement or type(scale) not in (int, float)
            or not np.isfinite(scale) or scale <= 0): raise ValueError('reference/target/units mismatch')
    mechanical = row['mechanical']; diagnostics = geometry_diagnostics(mechanical)
    points, frames = sampled_geometry(reference, reference_x)
    if points.shape != (len(mechanical['positions']), 3): raise ValueError('node coverage mismatch')
    errors = [abs(fsum((float(h), float(l), -float(r))))
              for a, b, c in zip(mechanical['positions'], mechanical['position_low'], points)
              for h, l, r in zip(a, b, c)]
    load = scale*reference.load
    if not np.isfinite(load) or load == 0: raise ValueError('nonzero finite reference load required')
    return dict(displacement=reference.displacement, native_load=row['parameter'], reference_load=load,
        load_relative_error=abs(row['parameter']-load)/abs(load),
        nodal_position_error=max(errors),
        nodal_frame_error=float(np.max(abs(np.asarray(mechanical['nodal_frames'])-frames))),
        geometry=diagnostics, reference_profile=reference.profile, stiffness_scale=scale,
        reference_energy=scale*reference.strain_energy, reference_load_slope=scale*reference.load_slope,
        reference_errors_normalized=dict(boundary=reference.boundary_error,
            differential=reference.differential_error, sensitivity=reference.sensitivity_error,
            work=float(reference.work_error)),
        same_equilibrium_branch_proved=False, mechanics_replayed=False, production_qualified=False)
