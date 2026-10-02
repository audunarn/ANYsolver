"""Selected finite recovery must be detached, ordered and replay-free."""
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from test_stiffened_shell_bl5_coupled_material import coupled
from test_stiffened_shell_bl5_material import make
from test_stiffened_shell_bl5_finite import _action


@pytest.mark.parametrize("kwargs", ({}, {"shell_nodes": [1]}, {"beam_nodes": (True,)},
                                    {"shell_nodes": (1, 1)}))
def test_invalid_selection(kwargs):
    with pytest.raises(ValueError): ss.GERecoverySelection(**kwargs)


def test_cached_ordered_recovery_after_displacement_restart(request, monkeypatch):
    owner = make(request, coupled())
    programme = ss.StagedDeadLoadProgramme(owner.preflight()["identity"], (_action(500.),))
    force = owner.solve(programme, (.5, 1.), max_iterations=20, max_backtracks=12)
    ids = tuple(r.element_id for r in force.shell_q4_material)
    selection = ss.GERecoverySelection(shell_nodes=(2, 1), beam_nodes=(105, 101),
        shell_material_elements=(ids[-1], ids[0]), beam_material_elements=(2, 1))
    force_selected = owner.recover(selection=selection)
    assert force_selected.load_position == 1. and force_selected.amplitude is None
    from scipy.spatial.transform import Rotation
    np.testing.assert_array_equal(force_selected.shell_frames,
        Rotation.from_rotvec(force.shell_displacement.reshape(-1, 6)[[1, 0], 3:]).as_matrix())
    initial = float(force.beam_positions[-1, 2] - .0675)
    controlled = owner.solve(_action(50.), (initial*1.01,),
        displacement_control=ss.DisplacementControl("beam", 105, 2),
        increment_control=ss.AdaptiveIncrementControl(2, 8),
        max_iterations=20, max_backtracks=12)
    snapshot = owner.checkpoint()
    resumed = make(request, coupled()); resumed.restore(snapshot)
    def forbidden(*args, **kwargs):
        raise AssertionError("selected recovery must not evaluate mechanics")
    for current in (owner, resumed):
        monkeypatch.setattr(current._finite_driver, "_assemble", forbidden)
    for current in (owner, resumed):
        for _ in range(2):
            selected = current.recover(selection=selection)
            assert selected.model_identity == current.preflight()["identity"]
            assert selected.generation == controlled.generation
            assert selected.amplitude == controlled.amplitude
            assert selected.displacement_target == controlled.target
            assert selected.load_position is None
            np.testing.assert_array_equal(selected.shell_displacement,
                                          controlled.shell_displacement.reshape(-1, 6)[[1, 0]])
            np.testing.assert_array_equal(selected.beam_positions, controlled.beam_positions[[4, 0]])
            np.testing.assert_array_equal(selected.shell_support_coordinate_covectors,
                controlled.support_reactions[:owner._shell_count].reshape(-1, 6)[[1, 0]])
            np.testing.assert_array_equal(selected.beam_support_coordinate_covectors,
                controlled.support_reactions[owner._shell_count:owner._shell_count+30].reshape(-1, 6)[[4, 0]])
            assert selected.beam_station_accumulated == controlled.beam_station_accumulated[::-1]
            assert tuple(r.element_id for r in selected.shell_material) == (ids[-1], ids[0])
            assert not np.shares_memory(selected.shell_material[0].layer_stress,
                                        controlled.shell_q4_material[-1].layer_stress)
            # Even a caller deliberately re-enabling writes cannot mutate owner data.
            selected.shell_displacement.setflags(write=True)
            selected.shell_displacement[:] = 123.
            selected.shell_material[0].layer_stress.setflags(write=True)
            selected.shell_material[0].layer_stress[:] = 123.
            assert current.checkpoint() == snapshot
        with pytest.raises(ValueError, match="unavailable"):
            current.recover(selection=ss.GERecoverySelection(beam_nodes=(999,)))
        with pytest.raises(ValueError, match="unavailable"):
            current.recover(selection=ss.GERecoverySelection(shell_material_elements=(999,)))
        empty = current.recover(selection=ss.GERecoverySelection(beam_nodes=(105,)))
        assert empty.shell_displacement.shape == (0, 6)
        assert empty.shell_frames.shape == (0, 3, 3)
        assert empty.shell_material == ()
