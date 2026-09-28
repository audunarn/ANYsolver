"""Bounded checks for the S4 expanded-solid energy/work diagnostic."""

import pytest

from scripts.b3_e4_f03_ccx_expanded_solid_replay import (
    compare_element_energies,
    knot_action,
)
from scripts.b3_e4_f03_ccx_expanded_work_probe import (
    displacement_print_quantum,
    hat_displacements,
)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def test_seven_coordinate_knot_action_is_work_conjugate():
    reference = (0.4, -0.2, 0.7)
    points = [(0.4, -0.2, 0.665), (0.4, -0.2, 0.7),
              (0.4, -0.195, 0.7), (0.4, -0.205, 0.7)]
    forces = [(2., 3., 5.), (-1., 7., -2.),
              (11., -13., 17.), (-19., 23., -29.)]
    translation = (0.04, -0.08, 0.02)
    rotation = (-0.3, 0.1, 0.2)
    expansion = 0.07
    action = knot_action(points, forces, reference)
    direct = 0.
    for xyz, force in zip(points, forces):
        r = tuple(xyz[j] - reference[j] for j in range(3))
        rotated = _cross(rotation, r)
        du = tuple(translation[j] + rotated[j] + expansion*r[j]
                   for j in range(3))
        direct += sum(force[j]*du[j] for j in range(3))
    pulled = (sum(action[j]*translation[j] for j in range(3)) +
              sum(action[j+3]*rotation[j] for j in range(3)) +
              action[6]*expansion)
    assert direct == pytest.approx(pulled, rel=1e-14, abs=1e-14)
    assert action[6] != 0.


def test_element_energy_comparison_requires_both_complete_walls():
    def dat(multiplier=1.):
        return "\n".join(
            f"internal energy (element, energy) for set {name} and time 1E+00\n"
            + "\n".join(f" {i} {multiplier*i:.9E}" for i in ids)
            for name, ids in (("PLATE", range(1, 17)),
                              ("WEB", range(17, 33)))
        ) + "\n"

    result = compare_element_energies(dat(), dat(1.0001))
    assert result["plate"]["sum_relative_difference"] == pytest.approx(1e-4)
    assert result["web"]["max_element_relative_difference"] == pytest.approx(1e-4)
    with pytest.raises(ValueError, match="incomplete"):
        compare_element_energies(dat(), dat().replace(" 32 3.200000000E+01", ""))


def test_probe_hat_uses_one_common_seven_coordinate_knot_motion():
    coordinates = {10: (0.5, 0.0, -0.0175),
                   11: (0.5, 0.0, 0.0175),
                   12: (0.5, 0.005, 0.0175),
                   13: (0.5, -0.005, 0.0175)}
    plate = hat_displacements(coordinates, [10, 11])
    web = hat_displacements(coordinates, [12, 13])
    assert plate[10] == pytest.approx((0., 0.001035, -0.000035))
    assert plate[11] == pytest.approx((0., 0.001, 0.))
    assert web[12] == pytest.approx((0., 0.001005, 0.000005))
    assert web[13] == pytest.approx((0., 0.000995, -0.000005))


def test_ascii_frd_last_place_quantum_tracks_each_printed_exponent():
    frd = " -4  DISP\n" + "".join(
        f" -1{node:10d}1.23456E-007-2.34567E-0060.00000E+000\n"
        for node in range(1, 101)
    ) + " -3\n"
    result = displacement_print_quantum(frd)
    assert result[1] == pytest.approx((1e-12, 1e-11, 1e-5))
    assert set(result) == set(range(1, 101))
