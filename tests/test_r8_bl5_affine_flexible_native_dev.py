"""Recovery counterexample independent of native assembly and external solver."""
import math

import pytest

from scripts.r8_bl5_affine_flexible_native_dev import exact_transfer_moments


def test_affine_force_quartic_wrench_moment_is_integrated_exactly():
    # Fy=2+3x; intrinsic Mz=4-5x; about-root Mz=4-3x+3x^2.
    points = [(1-t/math.sqrt(3))/2 for t in (1, -1)]
    records = [dict(x_m=x, measure_m=.5,
                    beam_wrench_about_root_density=[0., 2+3*x, 0., 0., 0., 4-3*x+3*x*x]) for x in points]
    result = exact_transfer_moments(records)
    for p in range(3):
        assert result[p][1] == pytest.approx(2/(p+1)+3/(p+2), abs=1e-13)
        assert result[p][5] == pytest.approx(4/(p+1)-3/(p+2)+3/(p+3), abs=1e-13)
    sampled = sum(r['measure_m']*r['x_m']**2*r['beam_wrench_about_root_density'][5] for r in records)
    assert abs(sampled-result[2][5]) > .01


def test_partial_or_wrong_measure_segment_is_rejected():
    with pytest.raises(ValueError, match='complete'):
        exact_transfer_moments([{}])
    records = [dict(x_m=x, measure_m=.1, beam_wrench_about_root_density=[0.]*6) for x in (.2, .8)]
    with pytest.raises(ValueError, match='measure'):
        exact_transfer_moments(records)


def test_adjacent_segments_fz_slope_has_opposite_my_lever_arm_sign():
    records = []
    for left, right in ((0., .25), (.25, 1.)):
        for t in (-1., 1.):
            x = (left+right)/2+(right-left)*t/(2*math.sqrt(3))
            records.append(dict(x_m=x, measure_m=(right-left)/2,
                beam_wrench_about_root_density=[0., 0., 1+2*x, 0., 3+4*x-x*(1+2*x), 0.]))
    result = exact_transfer_moments(records)
    for p in range(3):
        assert result[p][2] == pytest.approx(1/(p+1)+2/(p+2), abs=1e-13)
        assert result[p][4] == pytest.approx(3/(p+1)+3/(p+2)-2/(p+3), abs=1e-13)
    clipped = exact_transfer_moments(records, (.125, .75))
    for p in range(3):
        assert clipped[p][2] == pytest.approx((.75**(p+1)-.125**(p+1))/(p+1)
            +2*(.75**(p+2)-.125**(p+2))/(p+2), abs=1e-13)


@pytest.mark.parametrize('nx,span', ((16, 4), (32, 8)))
def test_mechanical_refinement_keeps_physical_interface_fixed(nx, span):
    import json
    from scripts import b3_e4_bl5_coherent_aggregation_dev as coherent
    from scripts.r8_bl5_affine_flexible_native_dev import fixed_support_model
    definition, policy = fixed_support_model(coherent, nx)
    assert len(definition.beams) == nx
    assert len(definition.shell.q4_elements) == nx*nx//4
    assert definition.lines[0].multiplier_span == span
    assert len(definition.lines[0].beam_halfcells)//span == 8
    assert policy['support_endpoints_m'] == [i/8 for i in range(9)]
    assert len(policy['support_membership']) == 8
    # Check actual geometry at every support endpoint, not only stored metadata.
    points = [json.loads(beam.raw)['reference']['coordinates'] for beam in definition.beams]
    node_x = [points[i//2][i%2][0] for i in range(2*nx)]+[points[-1][-1][0]]
    assert node_x[::span] == policy['support_endpoints_m']
    assert all(len(support) == span and support[0] % 2 == 0 and support[-1] % 2 == 1
               for support in policy['support_membership'])
