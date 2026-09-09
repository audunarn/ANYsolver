"""Small nonqualifying precision diagnostic for the frozen native package V1.

No mechanics replacement, authority generation, publication, or resource wave.
The exact rational witness is independent of the beam implementation. The
compensated comparison deliberately uses its unchanged local solver, not a new
formulation or an independent finite-element qualification oracle.
"""

from fractions import Fraction
import math

import numpy as np

from anysolver.fe_core import FEModel
from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from anysolver.nonlinear_state import NonlinearStateStore, create_model_native_rotation_store
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver._ge_beam3_p5 import NativeP5BeamElement, DirectedHardeningSection
from anysolver._ge_beam3_p5.compensated import CompensatedStationaryBeam
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5.core import canonical, sha
from anysolver._ge_beam3_p5.mixed import LocalForceAccuracy


BASE = 'cdf71995570b3d1aaeda44b7ed046c04528ae6b8'
SCHEMA = 'GE_BEAM3_P5_NATIVE_COORDINATE_DIAGNOSTIC_V1'
CASES = (('resolved_extension', -20, 1), ('sub_ulp_extension', -54, 1),
         ('sub_ulp_compression', -55, -1))


def exact_position_pairs(reference, total, view_high):
    """Diagnostic two-term addition, checked independently over exact rationals.

    This is not a native state schema. It accepts only the exact rounded high
    pose already supplied by the driver and does not infer displacement from
    that pose. A future state successor must retain both parts in every reader.
    """
    arrays = []
    for value, shape in ((reference, (3, 3)), (total, (18,)), (view_high, (3, 3))):
        if not isinstance(value, np.ndarray) or value.dtype != np.float64 or value.shape != shape:
            raise ValueError('exact binary64 coordinate/displacement shapes required')
        if not np.isfinite(value).all():
            raise ValueError('finite coordinate/displacement authority required')
        arrays.append(value.copy())
    reference, total, view_high = arrays
    displacement = total.reshape(3, 6)[:, :3]
    high = np.empty((3, 3)); low = np.empty((3, 3))
    for index in np.ndindex((3, 3)):
        a, b = float(reference[index]), float(displacement[index])
        high[index], low[index] = split_sum((a, b))
        if Fraction(float(high[index])) + Fraction(float(low[index])) != Fraction(a) + Fraction(b):
            raise ValueError('two-part position does not retain the exact supplied sum')
    if not np.array_equal(high, view_high):
        raise ValueError('native high pose disagrees with authoritative total displacement')
    return high, low


def problem(exponent, sign):
    if type(exponent) is not int or type(sign) is not int or sign not in (-1, 1):
        raise ValueError('exact witness exponent and sign required')
    strain = math.ldexp(float(sign), exponent)
    coordinates = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
    reference = CurvedBeam3ReferenceGeometry(coordinates, np.tile(np.eye(3), (3, 1, 1)))
    section = DirectedHardeningSection(np.eye(6), np.array([1., 0., 0., 0., 0., 0.]), 1., 1.)
    model = FEModel('native-p5-exact-axial-coordinate-witness')
    for i, point in enumerate(coordinates, 1):
        model.add_node(i, *point)
    element = NativeP5BeamElement(1, (1, 2, 3), reference, section)
    model.add_element(1, element)
    model.materials[element.material_name] = element.core.section
    total = np.zeros(18); total[[6, 12]] = [strain, 2*strain]
    return model, element, total, strain


def witness(case_id, exponent, sign):
    model, element, total, strain = problem(exponent, sign)
    initial = element.init_model_bound_nonlinear_state(model.mesh, element.core.section, 1)
    store = NonlinearStateStore.from_shell_layouts((), {1: initial})
    store.attach_native_rotation_store(create_model_native_rotation_store(model, {1: initial}, np.zeros(18)))
    before = canonical(store.materialize())
    reference = element.core.reference.coordinates
    high, low = exact_position_pairs(reference, total, reference + total.reshape(3, 6)[:, :3])
    try:
        force, _, payload = _assemble_nonlinear_system(model, total, store, 1)
        native = payload[1]['material_state']['response']
        # Existing accepted-origin validation currently accepts this rounded
        # response. This does not mean the independent axial identity passed.
        element.validate_model_bound_nonlinear_state(model.mesh, element.core.section, payload[1], 1,
            expected_committed_total_u=total)
        native_state_sha256 = sha(payload[1])
        compensated = CompensatedStationaryBeam(element.core.reference, element.core.section,
            order=element.core.order, position_low=low, origins=initial['material_state']['histories']).solve(
                high, element.core.reference.nodal_triads, force_accuracy=LocalForceAccuracy(1e-12, 2.))
    finally:
        token = store.active_trial_token()
        if token is not None:
            store.discard_trial(token)
    if canonical(store.materialize()) != before or store.generation != 0 or store.native_rotation_store.generation != 0:
        raise ValueError('diagnostic changed accepted native/material state')
    expected = np.zeros(18); expected[[0, 12]] = [-strain, strain]
    # Exact rational mechanics: EA=1, length=2, u(x)=strain*x.
    # N=strain, nodal force=(-N,0,N), potential=(EA*L/2)*strain**2.
    exact_energy = Fraction(strain)**2
    return dict(case_id=case_id, exponent=exponent, sign=sign, strain=strain,
        exact_energy=exact_energy, expected_force=expected, native_force=force,
        native_response=native, compensated_response=compensated, high=high, low=low,
        initial_state_sha256=sha(initial), native_state_sha256=native_state_sha256,
        accepted_state_unchanged=True)


def summarize(value):
    expected = value['expected_force']; strain = value['strain']
    native = value['native_response']; made = value['compensated_response']
    relative_native_error = float(np.linalg.norm(value['native_force']-expected)/np.linalg.norm(expected))
    relative_compensated_error = float(np.linalg.norm(made.residual-expected)/np.linalg.norm(expected))
    if relative_compensated_error > 1e-11:
        raise ValueError('compensated diagnostic failed the independent axial reference')
    if abs(made.potential-float(value['exact_energy'])) > 1e-11*float(value['exact_energy']):
        raise ValueError('compensated diagnostic failed the independent potential reference')
    for station in made.stations:
        if abs(station.response.strain[0]-strain) > 1e-11*abs(strain) or station.response.plastic_active:
            raise ValueError('compensated station failed the independent elastic strain reference')
    return dict(case_id=value['case_id'], exponent=value['exponent'], sign=value['sign'],
        exact_strain_ratio=[Fraction(strain).numerator, Fraction(strain).denominator],
        exact_energy_ratio=[value['exact_energy'].numerator, value['exact_energy'].denominator],
        native_force_sha256=sha(value['native_force']), compensated_force_sha256=sha(made.residual),
        native_response_sha256=sha(native), compensated_response_sha256=sha(made),
        native_force_relative_error_hex=relative_native_error.hex(),
        compensated_force_relative_error_hex=relative_compensated_error.hex(),
        native_axial_reference_passed=relative_native_error <= 1e-11,
        compensated_axial_reference_passed=True, accepted_state_unchanged=value['accepted_state_unchanged'],
        nonzero_low_coordinate_count=int(np.count_nonzero(value['low'])))


def run():
    records = [summarize(witness(*case)) for case in CASES]
    return dict(schema=SCHEMA, source_commit=BASE,
        disposition='DEVELOPMENT_NATIVE_POSITION_REPRESENTATION_DEFECT',
        production_qualified=False, activation_authorized=False,
        formal_evidence_reclassified=False, records=records)


if __name__ == '__main__':
    print(canonical(run()).decode('ascii'), end='')
