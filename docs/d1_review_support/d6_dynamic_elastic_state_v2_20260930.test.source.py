"""New free/clamped structural evaluator rank/work/objectivity discriminator."""
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from math import fsum
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import pytest

from anysolver.ge_beam3_native import create_analysis, SELECTOR, PROFILE_BYTES
from anysolver._ge_beam3_dynamic_elastic_state import DynamicElasticContext, AlgebraicRankError
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._ge_beam3_native_generalized_restart import _model
from anysolver._ge_beam3_centered_finite_inertia import evaluate_centered_finite_inertia, ALGEBRAIC_DOFS
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver.control import CancellationToken, SolveCancelled
from test_ge_beam3_native_midpoint import make_analysis


def retract(mechanical, direction, magnitude):
    data = {name: value.copy() for name, value in mechanical.descriptor().items()}
    for node in range(3):
        for axis in range(3):
            data['positions'][node, axis], data['position_low'][node, axis] = split_sum((
                float(mechanical.positions[node, axis]), float(mechanical.position_low[node, axis]),
                float(magnitude*direction[6*node+axis])))
        data['nodal_frames'][node] = rotation(magnitude*direction[6*node+3:6*node+6])@mechanical.nodal_frames[node]
    for cell in (0, 1):
        data['cell_rotations'][0, cell] = rotation(magnitude*direction[18+3*cell:21+3*cell])@mechanical.cell_rotations[0, cell]
    data['resultants'][0] += magnitude*direction[24:]
    return Mechanical(**data)


def relative(a, b):
    return float(np.linalg.norm(a-b)/max(1e-30, np.linalg.norm(b)))


def inertia(context, state):
    m = state.mechanical
    return evaluate_centered_finite_inertia(context.element.operator.reference,
        context.analysis._inertias[context.element.element_id], m.positions, m.position_low,
        m.cell_rotations[0], np.zeros(24), np.zeros(24), order=24)


def test_dynamic_elastic_free_rank_mass_work_and_objectivity(record_property):
    output = Path(os.environ['D6_DYNAMIC_ELASTIC_OUTPUT'])
    assert not output.exists()
    started = perf_counter()
    raw = dict(status='running', checks={}, elapsed_seconds=0.)

    def save(stage, **fields):
        raw.update(fields)
        raw['last_stage'] = stage
        raw['elapsed_seconds'] = perf_counter()-started
        output.write_text(json.dumps(raw, indent=2)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=raw['elapsed_seconds'])), flush=True)

    try:
        imported = Path(inspect.getsourcefile(DynamicElasticContext)).resolve()
        assert imported == Path(__file__).resolve().parents[1]/'src/anysolver/_ge_beam3_dynamic_elastic_state.py'
        raw['source_identity'] = dict(module=str(imported), sha256=sha256(imported.read_bytes()).hexdigest(),
            test_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), cache=os.environ['NUMBA_CACHE_DIR'])
        profile = PROFILE_BYTES
        clamp_analysis, definition = make_analysis()
        free_analysis = create_analysis(SELECTOR, (definition,), ())
        raw['definition'] = json.loads(definition.raw)
        assert free_analysis._admit_boundaries() == () and free_analysis.model.boundary_conditions == []
        assert not free_analysis.model.constraint_equations and free_analysis.model.mesh.element_activity is None
        assert not free_analysis.model.mesh.point_masses
        with pytest.raises(ValueError, match='supported distributed model required'):
            _model(free_analysis.model, retained=True)
        free = DynamicElasticContext(free_analysis)
        state = free.reference_state()
        assert free.physical_free == (0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20, 21, 22, 23)
        assert len(free.algebraic_free) == 27 and free.free == tuple(range(42))
        rank = free.algebraic_rank(state)
        mass = inertia(free, state)
        p = list(free.physical_free)
        mass15 = mass.mixed_mass[np.ix_(p, p)]
        eigenvalues = np.linalg.eigvalsh(mass15)
        np.linalg.cholesky((mass15+mass15.T)/2)
        assert eigenvalues[0] > 0.
        assert np.array_equal(mass.mixed_mass[list(ALGEBRAIC_DOFS), :], np.zeros((27, 42)))
        assert np.array_equal(mass.mixed_mass[:, list(ALGEBRAIC_DOFS)], np.zeros((42, 27)))
        raw['initial_rank_mass'] = dict(algebraic=rank, physical_mass_rank=int(np.linalg.matrix_rank(mass15)),
            physical_mass_eigenvalues=eigenvalues.tolist(), physical_mass_condition=float(eigenvalues[-1]/eigenvalues[0]))
        work = free.evaluate(state)
        _, singular, vh = np.linalg.svd(work.spatial_jacobian)
        tolerance = 64*np.finfo(float).eps*42*singular[0]
        raw['initial_rank_mass']['whole_static_rank'] = int(np.count_nonzero(singular > tolerance))
        raw['initial_rank_mass']['whole_static_singular_values'] = singular.tolist()
        raw['initial_rank_mass']['whole_static_null_vectors'] = vh[singular <= tolerance].tolist()
        raw['matrices'] = dict(K42=work.spatial_jacobian.tolist(), M42=mass.mixed_mass.tolist(),
            physical_indices=p, algebraic_indices=list(free.algebraic_free))
        assert raw['initial_rank_mass']['physical_mass_rank'] == 15
        assert rank['rank'] == 27
        assert raw['initial_rank_mass']['whole_static_rank'] == 36
        assert np.linalg.norm(work.residual) < 1e-11
        save('free_rank_and_mass_pass')

        # Rigid shape in the free case needs no artificial equilibrium support.
        translation = np.array((.31, -.22, .17))
        data = {key: val.copy() for key, val in state.mechanical.descriptor().items()}
        data['positions'] += translation
        translated = free.trial_state(Mechanical(**data))
        translation_work = free.evaluate(translated)
        translated_consistent = free.consistent(translated)
        assert translated_consistent.iterations == 0
        assert np.linalg.norm(translation_work.residual) < 1e-11
        assert relative(translation_work.spatial_jacobian, work.spatial_jacobian) < 1e-13
        assert np.array_equal(translated_consistent.state.mechanical.positions, translated.mechanical.positions)
        # Compensated high/low values retain a large common translation too.
        shift = np.array((2.**40, -2.**40, 2.**41))
        large = {key: val.copy() for key, val in state.mechanical.descriptor().items()}
        for node in range(3):
            for axis in range(3):
                large['positions'][node, axis], large['position_low'][node, axis] = split_sum((
                    float(state.mechanical.positions[node, axis]), float(shift[axis])))
        large_state = free.trial_state(Mechanical(**large))
        large_work = free.evaluate(large_state)
        assert np.array_equal(large_work.residual, work.residual)
        assert np.array_equal(large_work.spatial_jacobian, work.spatial_jacobian)
        raw['checks']['rigid_translation'] = dict(offset_m=translation.tolist(),
            residual_norm=float(np.linalg.norm(translation_work.residual)),
            large_offset_m=shift.tolist(), maximum_low_m=float(np.max(np.abs(large_state.mechanical.position_low))),
            large_translation_work_and_tangent_bit_identical=True)

        # Literal constant line force work: a common translation contracts with
        # the independently evaluated curved-reference quadrature arclength.
        force = np.array((.01, -.003, .006))
        parameter = .7
        line = DistributedPattern(LinePattern(((1, *map(float, force)),)), ())
        g, w = np.polynomial.legendre.leggauss(4)
        measure = fsum(float(weight)*np.sqrt(1+.16*(cell-1+(point+1)/2)**2)/2
            for cell in (0, 1) for point, weight in zip(g, w))
        loaded = free.evaluate(translated, pattern=line, parameter=parameter)
        expected_work = parameter*measure*float(force@translation)
        expected_force = -parameter*measure*force
        net = sum((loaded.residual[6*n:6*n+3] for n in range(3)), np.zeros(3))
        assert abs(loaded.line_work-expected_work) < 1e-15
        assert relative(net, expected_force) < 1e-13
        couple = np.array((.002, -.001, .003))
        coupled = free.evaluate(translated, pattern=DistributedPattern(line.line,
            ((1, *map(float, couple)),)), parameter=parameter)
        expected_couple = parameter*measure*couple
        assert relative(coupled.applied_couple42[18:21]+coupled.applied_couple42[21:24], expected_couple) < 1e-13
        assert not coupled.conservative_potential and loaded.conservative_potential
        assert np.array_equal(coupled.spatial_jacobian, loaded.spatial_jacobian)
        raw['checks']['literal_load_work'] = dict(arclength_quadrature_m=measure,
            line_work_j=loaded.line_work, expected_line_work_j=expected_work,
            integrated_force_n=net.tolist(), spatial_couple_nm=expected_couple.tolist(),
            nonpotential_couple_marked=True)

        # General non-equilibrium elastic work uses the existing operator, with
        # all physical and algebraic modes retained in virtual work/tangent.
        deformation = np.zeros(42)
        deformation[6:] = np.sin(np.arange(36)+.4)*.001
        deformation[24:] *= 2.
        general = free.trial_state(retract(state.mechanical, deformation, 1.))
        general_work = free.evaluate(general, pattern=line, parameter=parameter)
        direction = np.sin(np.arange(42)+.2)*.03
        directional = []
        for delta in (1e-5, 2e-6):
            plus = free.trial_state(retract(general.mechanical, direction, delta))
            minus = free.trial_state(retract(general.mechanical, direction, -delta))
            wp = free.evaluate(plus, pattern=line, parameter=parameter)
            wm = free.evaluate(minus, pattern=line, parameter=parameter)
            derivative = (wp.conservative_value-wm.conservative_value)/(2*delta)
            exact = float(general_work.residual@direction)
            tangent = (wp.residual-wm.residual)/(2*delta)
            directional.append(dict(delta=delta, work_relative=abs(derivative-exact)/abs(exact),
                tangent_relative=relative(tangent, general_work.spatial_jacobian@direction)))
        assert max(item[key] for item in directional for key in ('work_relative', 'tangent_relative')) < 1e-5
        raw['checks']['full42_virtual_work_and_tangent'] = directional

        # Complete rigid-frame covariance, including algebraic trace moments and
        # resultant blocks, with scalar potential invariant at zero load.
        q = rotation((.31, -.22, .19))
        shifted = np.array((.43, -.27, .18))
        rotated = {key: val.copy() for key, val in general.mechanical.descriptor().items()}
        rotated['positions'] = general.mechanical.positions@q.T+shifted
        rotated['position_low'] = general.mechanical.position_low@q.T
        # Normalize rotated low pairs after the finite common displacement.
        for node in range(3):
            for axis in range(3):
                rotated['positions'][node, axis], rotated['position_low'][node, axis] = split_sum((
                    float(rotated['positions'][node, axis]), float(rotated['position_low'][node, axis])))
        rotated['nodal_frames'] = q@general.mechanical.nodal_frames
        rotated['cell_rotations'] = q@general.mechanical.cell_rotations
        rotated_state = free.trial_state(Mechanical(**rotated))
        base = free.evaluate(general)
        transformed = free.evaluate(rotated_state)
        block = np.eye(42)
        for first in range(0, 24, 3):
            block[first:first+3, first:first+3] = q
        objectivity = dict(residual_relative=relative(transformed.residual, block@base.residual),
            tangent_relative=relative(transformed.spatial_jacobian, block@base.spatial_jacobian@block.T),
            conservative_value_error_j=abs(transformed.conservative_value-base.conservative_value))
        assert objectivity['residual_relative'] < 1e-11
        assert objectivity['tangent_relative'] < 1e-11
        assert objectivity['conservative_value_error_j'] < 1e-13
        raw['checks']['objectivity'] = objectivity

        # Initial/endpoint algebraics at a prescribed deformed physical pose:
        # no force-equilibrium solve or physical coordinate condensation.
        result = free.consistent(general)
        assert np.array_equal(result.state.mechanical.positions, general.mechanical.positions)
        assert np.array_equal(result.state.mechanical.position_low, general.mechanical.position_low)
        assert np.array_equal(result.state.mechanical.cell_rotations, general.mechanical.cell_rotations)
        assert np.linalg.norm(result.work.residual[p]) > 1e-5
        raw['checks']['fixed_physical_algebraic_consistency'] = dict(iterations=result.iterations,
            backtracks=result.backtracks, residual=result.residual_norm, correction=result.correction_norm,
            rank=result.algebraic_rank, condition=result.algebraic_condition,
            physical_residual_norm_n_m=float(np.linalg.norm(result.work.residual[p])),
            mechanical={name: value.tolist() for name, value in result.state.mechanical.descriptor().items()})
        save('free_work_objectivity_consistency_pass')

        # Clamp preserves the former structural result without invoking Context.
        clamp = DynamicElasticContext(clamp_analysis)
        clamped = clamp.reference_state()
        clamped_work = clamp.evaluate(clamped)
        old_path = Path(os.environ['D6_DYNAMIC_ELASTIC_CLAMP_REFERENCE'])
        old = json.loads(old_path.read_text())
        assert np.array_equal(clamped_work.spatial_jacobian, np.array(old['reference_matrices']['K42']))
        assert np.array_equal(inertia(clamp, clamped).mixed_mass, np.array(old['reference_matrices']['M42']))
        assert clamp.algebraic_rank(clamped)['rank'] == 24
        bad = {key: val.copy() for key, val in clamped.mechanical.descriptor().items()}
        bad['positions'][0, 0] += .001
        with pytest.raises(ValueError, match='prescribed physical'):
            clamp.trial_state(Mechanical(**bad))
        with pytest.raises(ValueError, match='issued immutable'):
            clamp.evaluate(state)
        with pytest.raises(ValueError, match='issued immutable'):
            free.evaluate(replace(state))
        before = canonical(state)
        token = CancellationToken()
        token.cancel('new structural evaluator cancellation control')
        with pytest.raises(SolveCancelled):
            free.consistent(state, cancellation_token=token)
        assert canonical(state) == before
        with free_analysis._operation():
            with pytest.raises(ValueError, match='already in use'):
                free.evaluate(state)
        for array in (state.mechanical.positions, state.mechanical.position_low,
                      state.mechanical.nodal_frames, state.mechanical.cell_rotations,
                      state.mechanical.resultants, work.residual, work.spatial_jacobian):
            with pytest.raises(ValueError):
                array.setflags(write=True)
        assert PROFILE_BYTES == profile
        raw['checks']['clamp_and_admission_controls'] = dict(clamped_K_M_bit_identical_to_midpoint_v2=True,
            fixed_translation_rejected=True, foreign_state_rejected=True,
            cancelled_consistency_preserved_state=True, lock_reentrancy_rejected=True,
            immutable_arrays=True, static_zero_support_guard_unchanged=True,
            public_profile_unchanged=True)
        record_property('free_rank_mass', json.dumps(raw['initial_rank_mass']))
        record_property('work_objectivity', json.dumps(raw['checks']))
        save('completed', status='PASS')
    except AlgebraicRankError as error:
        save('algebraic_singular', status='NONPASS', failure=str(error),
            singular_values=error.singular_values.tolist(), null_vector42=error.null_vector42.tolist(),
            rank=error.rank, null_vector_groups=dict(
                nodal_frames=float(np.linalg.norm(error.null_vector42[[3,4,5,9,10,11,15,16,17]])),
                resultants=float(np.linalg.norm(error.null_vector42[24:]))))
        raise
    except BaseException as error:
        save('failed', status='NONPASS', failure=repr(error))
        raise
