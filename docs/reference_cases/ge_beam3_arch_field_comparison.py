"""Bounded nodal geometry/station recovery comparison, not qualification.

Saved native states are read, never globally solved again. Native physical
recovery must reproduce each saved recovery hash. The separate continuum BVP
is sampled explicitly; no interpolation of previously saved stations occurs.
"""
from dataclasses import asdict
from hashlib import sha256
from math import fsum
import json
from types import SimpleNamespace
import numpy as np

from docs.reference_cases import ge_beam3_fibre_arch_comparison as geometry
from docs.reference_cases import ge_beam3_preserved_arch_load_comparison as audit
from docs.reference_cases import ge_beam3_curved_p5_arch_reference as continuum


TARGETS = (.01, .025, .04, .055)
STIFFNESS = np.array([1.e6, 4.e5, 4.e5, 80., 100., 100.])


def reference_fields(reference, locations, scale=1.e6):
    """Physical e2=+z: gamma_z=-V/GA and kappa_y=M/EI.

    The right half has x, theta and Fy reversed, with Fx and M unchanged.
    All cross-sections use the positive-reference-X orientation.
    """
    x = geometry._array(locations, (len(locations),))
    if np.any(abs(x) > 1.) or type(scale) is not float or not np.isfinite(scale) or scale <= 0:
        raise ValueError('bounded stations and physical force scale required')
    points, frames = geometry.sampled_geometry(reference, x)
    strain, force, moment = [], [], []
    for location in x:
        indices = np.flatnonzero(reference.parameter == -abs(location))
        if len(indices) != 1: raise ValueError('explicit collocation sample absent')
        angle, m = reference.fields[2:, indices[0]]
        fx, fy = reference.force
        if location > 0: angle, fy = -angle, -fy
        n = fx*np.cos(angle)+fy*np.sin(angle)
        v = -fx*np.sin(angle)+fy*np.cos(angle)
        strain.append([n/reference.axial, 0., -v/reference.shear, 0., m/reference.bending, 0.])
        force.append([scale*fx, scale*fy, 0.]); moment.append([0., 0., scale*m])
    return dict(positions=points, frames=frames, strain=np.array(strain),
                force=np.array(force), moment=np.array(moment))


def paired(high, low):
    h = geometry._array(high, (6,)); l = geometry._array(low, (6,))
    return np.array([fsum((float(a), float(b))) for a, b in zip(h, l)])


def compare_stations(stations, expected, reference_energy):
    if (not stations or type(reference_energy) is not float or not np.isfinite(reference_energy)
            or reference_energy <= 0): raise ValueError('nonempty stations and positive reference energy')
    n = len(stations)
    shapes = dict(strain=(n, 6), frames=(n, 3, 3), force=(n, 3), moment=(n, 3), positions=(n, 3))
    e = {k: geometry._array(expected[k], shape) for k, shape in shapes.items()}
    numerator = denominator = energy = 0.; force_error = []; moment_error = []; frames = []
    force_scale = float(np.max(np.linalg.norm(e['force'], axis=1)))
    moment_scale = float(np.max(np.linalg.norm(e['moment'], axis=1)))
    if min(force_scale, moment_scale) <= 0: raise ValueError('nonzero reference force/moment scales')
    for i, row in enumerate(stations):
        weight = row['measure']
        if type(weight) is not float or not np.isfinite(weight) or weight <= 0:
            raise ValueError('positive finite station measure')
        strain = paired(row['strain'], row['strain_low'])
        stress = paired(row['resultants'], row['resultants_low'])
        frame = geometry._array(row['current_frame'], (3, 3))
        if np.max(abs(frame.T@frame-np.eye(3))) > 1e-11 or abs(np.linalg.det(frame)-1) > 1e-11:
            raise ValueError('proper recovered frame')
        difference = strain-e['strain'][i]
        numerator += weight*float(difference@(STIFFNESS*difference))
        denominator += weight*float(e['strain'][i]@(STIFFNESS*e['strain'][i]))
        energy += .5*weight*float(strain@stress)
        force_error.append(float(np.linalg.norm(frame@stress[:3]-e['force'][i]))/force_scale)
        moment_error.append(float(np.linalg.norm(frame@stress[3:]-e['moment'][i]))/moment_scale)
        frames.append(float(np.max(abs(frame-e['frames'][i]))))
    if denominator <= 0 or not np.isfinite([numerator, denominator, energy]).all():
        raise ValueError('finite positive field norm')
    return dict(stations=n, nominal_energy_norm_relative_error=float(np.sqrt(numerator/denominator)),
        native_integrated_energy=energy, reference_energy=reference_energy,
        integrated_energy_relative_error=abs(energy-reference_energy)/reference_energy,
        spatial_force_max_relative_error=max(force_error), spatial_moment_max_relative_error=max(moment_error),
        recovered_frame_max_absolute_error=max(frames),
        reference_energy_from_native_station_rule=.5*denominator,
        reference_station_quadrature_relative_error=abs(.5*denominator-reference_energy)/reference_energy)


def native_recovery(model, row):
    # Lazy production imports are confined to this native producer-side adapter.
    # The continuum implementation and its field conversion import no ANYsolver.
    from anysolver._ge_beam3_p5_seeded.core import canonical, sha
    from anysolver._ge_beam3_fibre_cell import CellHistory
    elements = tuple(sorted(model.mesh.elements.items())); made = []; locations = []
    origins = tuple(e.operator.cell.virgin() for _, e in elements)
    if canonical(origins) != canonical(row['origins']) or canonical(origins) != canonical(row['histories']):
        raise ValueError('this reference admits only the exactly saved virgin elastic histories')
    mechanical = row['mechanical']
    for i, (eid, element) in enumerate(elements):
        op = element.operator
        recovered = op.recover(mechanical['cell_rotations'][i], mechanical['resultants'][i], origin=origins[i])
        if canonical(CellHistory(op.cell.identity, tuple(r['history'] for r in recovered))) != canonical(origins[i]):
            raise ValueError('recovery changed saved elastic history')
        made.append(dict(element_id=eid, stations=recovered))
        locations.extend(float(op.reference.position(r['xi'])[0]) for r in recovered)
    if sha(tuple(made)) != row['recovery_sha256']: raise ValueError('saved physical recovery hash mismatch')
    return tuple(made), locations


def recompute_rows(diagnostic, checkpoints):
    """Recompute every summary metric from saved fields; not a new oracle."""
    references = {}
    for saved in diagnostic['references']:
        data = dict(saved)
        for name in ('force', 'parameter', 'fields'): data[name] = np.asarray(data[name], dtype=float)
        ref = SimpleNamespace(**data)
        if ((ref.height, ref.axial, ref.shear, ref.bending) != (.1, 1., .4, .0001)
                or ref.production_qualified is not False): raise ValueError('nominal reference family changed')
        references[ref.displacement, ref.profile] = ref
    rows = []
    for recovery in diagnostic['recoveries']:
        target, macros = recovery['target'], recovery['macros']
        fine = references[target, 'BVP9']; coarse = references[target, 'BVP7']
        locations = recovery['locations']
        expected = reference_fields(fine, locations)
        expected_plain = {k: v.tolist() for k, v in expected.items()}
        observed = {k: np.asarray(v).tolist() for k, v in recovery['reference_fields'].items()}
        if audit.canonical(expected_plain) != audit.canonical(observed): raise ValueError('reference field conversion changed')
        stations = [s for e in recovery['fields'] for s in e['stations']]
        stats = compare_stations(stations, expected, float(1e6*fine.strain_energy))
        record = checkpoints[macros]['records'][TARGETS.index(target)]
        nodal = geometry.compare(record, np.linspace(-1., 1., 2*macros+1), 1e6, fine)
        rows.append(dict(macros=macros, displacement=target, nodal_geometry=nodal, station_recovery=stats,
            reference_profile_max_absolute_difference=float(np.max(abs(coarse.fields-fine.fields))),
            reference_profile_load_relative_difference=abs(coarse.load/fine.load-1)))
    return rows


def build(checkpoints, preserved_reference, progress):
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    if set(checkpoints) != {6, 12}: raise ValueError('exact preserved six/twelve comparison required')
    models = {m: family.model(m) for m in (6, 12)}
    samples = set(map(float, np.linspace(-1., 0., 129)))
    for m, model in models.items():
        audit.inspect_records(checkpoints[m], preserved_reference, macros=m)
        samples.update(-abs(float(node.x)) for node in model.mesh.nodes.values())
        for element in model.mesh.elements.values():
            samples.update(-abs(float(element.operator.reference.position(xi)[0]))
                for _, _, xi, _, _ in element.operator.stations)
    sample_parameters = sorted(samples)
    continuum.sampling_parameters(sample_parameters)
    references = []; recoveries = []; rows = []
    previous = {p: None for p in ('BVP7', 'BVP9')}
    for index, target in enumerate(TARGETS):
        current = {}
        for profile in ('BVP7', 'BVP9'):
            progress(dict(stage='REFERENCE', target=target, profile=profile))
            ref = continuum.solve(target, height=.1, axial=1., shear=.4, bending=.0001,
                previous=previous[profile], profile=profile, sample_parameters=sample_parameters)
            previous[profile] = current[profile] = ref
            references.append(asdict(ref))
        coarse, fine = current['BVP7'], current['BVP9']
        profile_difference = float(np.max(abs(coarse.fields-fine.fields)))
        for m in (6, 12):
            progress(dict(stage='RECOVERY', target=target, macros=m))
            row = checkpoints[m]['records'][index]
            recovered, locations = native_recovery(models[m], row)
            stations = [s for e in recovered for s in e['stations']]
            expected = reference_fields(fine, locations)
            stats = compare_stations(stations, expected, float(1e6*fine.strain_energy))
            nodes = [float(n.x) for n in models[m].mesh.nodes.values()]
            nodal = geometry.compare(row, nodes, 1e6, fine)
            raw_recovery = native_canonical(recovered)
            recoveries.append(dict(macros=m, target=target, recovery_sha256=sha256(raw_recovery).hexdigest(),
                fields=json.loads(raw_recovery), locations=locations, reference_fields=expected))
            rows.append(dict(macros=m, displacement=target, nodal_geometry=nodal,
                station_recovery=stats, reference_profile_max_absolute_difference=profile_difference,
                reference_profile_load_relative_difference=abs(coarse.load/fine.load-1)))
    return dict(schema='GE_BEAM3_ARCH_GEOMETRY_RECOVERY_DEVELOPMENT_V1',
        status='DEVELOPMENT_COMPARISON_NOT_QUALIFICATION', rows=rows,
        sampling_parameters=sample_parameters, native_nonlinear_solves=0, new_reference_solves=8,
        same_equilibrium_branch_proved=False, independent_review='PENDING', production_qualified=False,
        nominal_section_comparison_not_exact_dyadic_certificate=True), dict(references=references, recoveries=recoveries)
