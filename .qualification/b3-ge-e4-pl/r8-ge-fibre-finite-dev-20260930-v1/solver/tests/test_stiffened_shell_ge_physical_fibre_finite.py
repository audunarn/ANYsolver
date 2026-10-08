"""Finite native histories through the existing experimental point owner."""
from dataclasses import replace
import json

import anysolver
import numpy as np
import pytest

from anysolver import b3_ge
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_ge_experimental import NodalAction
from anysolver._stiffened_shell_ge_checkpoint_binary import decode, encode
from anysolver._stiffened_shell_beam_history import arrays, histories, shapes
from test_stiffened_shell_ge_physical_fibre_linear import _definition


def _yielding_definition(mixed=False, triangles=False):
    definition = _definition(mixed, triangles)
    beams = []
    for native in definition.beams:
        element, inertia = native.instantiate()
        if type(element.section) is not b3_ge.PhysicalFibreSection:
            beams.append(native)
            continue
        section = b3_ge.PhysicalFibreSection(tuple(
            replace(fibre, curve=b3_ge.FlowCurve((0.,), (1e5,), 1e9))
            if index == 0 else fibre
            for index, fibre in enumerate(element.section.fibres)), element.section.background_factor)
        reference = element.operator.reference
        beams.append(b3_ge.define_beam('b3-ge', element.element_id,
            element.node_ids, reference.coordinates, reference.nodal_triads,
            section, inertia, quadrature=element.operator.order))
    return replace(definition, beams=tuple(beams))


@pytest.mark.parametrize('mixed,triangles', ((False,False),(True,False),(True,True)))
def test_finite_native_response_restart_and_predecessor(mixed, triangles):
    definition = _definition(mixed, triangles)
    owner = anysolver.stiffened_shell.create_analysis(definition=definition)
    actions = (NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
    first = owner.solve(actions, targets=(.5,1.))
    assert first.generation == 2
    assert first.beam_fibre_material
    assert all(record.fibres for record in first.beam_fibre_material)
    assert all(not record.strain.flags.writeable for record in first.beam_fibre_material)
    driver = owner._finite_driver
    saved = owner.checkpoint()
    resumed = anysolver.stiffened_shell.create_analysis(definition=definition)
    restored = resumed.restore(saved)
    assert resumed.checkpoint() == saved
    for name in ('beam_positions','beam_frames','cell_frames','cell_resultants',
                 'multipliers','shell_displacement'):
        np.testing.assert_array_equal(getattr(first,name),getattr(restored,name))
    for a,b in zip(first.beam_fibre_material, restored.beam_fibre_material):
        assert a.fibres == b.fibres
        np.testing.assert_array_equal(a.strain,b.strain)
        np.testing.assert_array_equal(a.resultants,b.resultants)
    def expected(kind, generation):
        assert kind == 'finite_native_material'
        count = owner._K.shape[0]
        return (("q",(count,)),("frames",(len(owner._beam_ids),3,3)),
            ("cells",(len(owner._beam_parts),2,3,3)),
            ("resultants",(len(owner._beam_parts),18)),
            ("multipliers",(owner._C.shape[0],)),("pattern",(count,)),
            ("accepted_factors",(generation,))) + shapes(owner._beam_parts,'origin') + shapes(owner._beam_parts,'accepted')
    kind,generation,values = decode(saved,owner._identity,expected)
    json_payload = json.dumps({'schema': 'B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7',
        'model': owner._identity, 'generation': generation,
        **{name:value.tolist() for name,value in values.items()}}).encode()
    json_owner = anysolver.stiffened_shell.create_analysis(definition=definition)
    with pytest.raises(ValueError,match='requires binary framing'):
        json_owner.restore(json_payload)
    assert json_owner._generation == 0
    json_owner.close()
    changed = {name: np.array(value,copy=True) for name,value in values.items()}
    changed['accepted_fibres'][0,2] += 1e-6
    corrupt = encode(kind,owner._identity,generation,tuple(changed.items()))
    untouched = anysolver.stiffened_shell.create_analysis(definition=definition)
    with pytest.raises(ValueError,match='update disagrees with accepted history'):
        untouched.restore(corrupt)
    assert untouched._generation == 0 and untouched._finite_driver is None
    untouched.close()
    continued = resumed.solve(actions,targets=(.5,))
    oracle = owner.solve(actions,targets=(.5,))
    np.testing.assert_array_equal(continued.cell_resultants,oracle.cell_resultants)
    assert continued.beam_station_accumulated == oracle.beam_station_accumulated
    packed = dict(arrays(owner._beam_parts,driver._beam_origins,'accepted'))
    rebuilt = histories(owner._beam_parts,packed,'accepted')
    assert rebuilt == driver._beam_origins
    packed['accepted_fibres'][:] = np.nan
    assert rebuilt == driver._beam_origins
    with pytest.raises(ValueError,match='finite model-bound'):
        histories(owner._beam_parts,packed,'accepted')
    owner.close(); resumed.close()


@pytest.mark.parametrize('mixed,triangles', ((False,False),(True,False)))
def test_native_yield_unload_reject_cancel_and_restore(mixed,triangles):
    definition = _yielding_definition(mixed,triangles)
    owner = anysolver.stiffened_shell.create_analysis(definition=definition)
    actions = (NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
    first = owner.solve(actions,targets=(.5,1.),
                        max_iterations=18,max_backtracks=8)
    assert max(v for row in first.beam_station_accumulated for v in row) > 0.
    assert any(sum(f.plastic_increment) != 0. for record in first.beam_fibre_material
               for f in record.fibres)
    saved = owner.checkpoint()
    with pytest.raises(RuntimeError):
        owner.solve(actions,targets=(2.,),max_iterations=1,max_backtracks=0)
    assert owner.checkpoint() == saved
    token = CancellationToken(); token.cancel()
    with pytest.raises(SolveCancelled):
        owner.solve(actions,targets=(1.5,),cancellation_token=token)
    assert owner.checkpoint() == saved
    resumed = anysolver.stiffened_shell.create_analysis(definition=definition)
    restored = resumed.restore(saved)
    assert resumed.checkpoint() == saved
    assert any(sum(f.plastic_increment) != 0. for record in restored.beam_fibre_material
               for f in record.fibres)
    assert resumed._finite_driver._beam_predecessors != resumed._finite_driver._beam_origins
    a = owner.solve(actions,targets=(.5,),max_iterations=18)
    b = resumed.solve(actions,targets=(.5,),max_iterations=18)
    np.testing.assert_array_equal(a.cell_resultants,b.cell_resultants)
    assert owner.checkpoint() == resumed.checkpoint()
    owner.close(); resumed.close()


def test_native_cancel_after_material_recovery_preserves_accepted_state(monkeypatch):
    from anysolver import _stiffened_shell_ge_finite_experimental as finite
    owner = anysolver.stiffened_shell.create_analysis(definition=_yielding_definition())
    actions = (NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
    first = owner.solve(actions,targets=(.5,))
    saved = owner.checkpoint()
    token = CancellationToken()
    original = finite.cancellation_safe_point
    def cancel(token_value, stage):
        if stage == 'stiffened-shell.finite.material-publish':
            token.cancel('after native recovery')
        return original(token_value,stage)
    with monkeypatch.context() as context:
        context.setattr(finite,'cancellation_safe_point',cancel)
        with pytest.raises(SolveCancelled,match='after native recovery'):
            owner.solve(actions,targets=(1.,),cancellation_token=token)
    assert owner.recover() is first
    assert owner.checkpoint() == saved
    assert owner._generation == first.generation
    owner.close()


@pytest.mark.parametrize('yielding', (False,True))
def test_pure_fibre_s3_completion_or_truthful_accepted_prefix(yielding):
    """Pending response case: numerical failure must never become equilibrium.

    This checks result/failure ownership, not physical acceptance of the route.
    Its observed convergence failure remains recorded in development evidence.
    """
    definition = (_yielding_definition(False,True) if yielding else _definition(False,True))
    owner = anysolver.stiffened_shell.create_analysis(definition=definition)
    actions = (NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),)
    try:
        result = owner.solve(actions,targets=(.5,1.))
    except RuntimeError as error:
        assert str(error) in ('finite mixed backtrack budget exhausted',
                             'finite mixed Newton iteration limit')
        if owner._finite_driver is None:
            assert owner._generation == 0
            with pytest.raises(RuntimeError,match='no accepted'):
                owner.recover()
        else:
            prefix = owner.recover()
            assert prefix.accepted_factors == (.5,)
            assert prefix.free_equilibrium_ratio <= 1e-8
            assert prefix.constraint_max <= 1e-9
    else:
        assert result.accepted_factors == (.5,1.)
        assert result.free_equilibrium_ratio <= 1e-8
        assert result.constraint_max <= 1e-9
    owner.close()
