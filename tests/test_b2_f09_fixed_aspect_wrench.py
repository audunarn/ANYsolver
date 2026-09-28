"""Fixed mixed-wrench F09 check on one coherent constant-area rectangle path.

The earlier aspect diagnostic scaled the load with section depth.  Here the
same small physical wrench acts on every section, so a changing applied
force scale cannot hide a graph conditioning or stored-state balance loss.
This is private development evidence, not a continuous admission range.
"""

from fractions import Fraction as F

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver._b2_physical_linear_definition import PhysicalB2Member


WIDTH_DEPTH_M = (
    (F(12, 1000), F(3, 1000)),
    (F(48, 1000), F(3, 4000)),
    (F(192, 1000), F(3, 16000)),
)
FIRST_M = (F(80, 1000), F(3, 1000))
# One unchanged six-component tip load, with applied couples opposing the
# force-arm root moment.  The residual root moment is small but nonzero in
# all three directions; this wrench is not proportional to the earlier one.
TIP = (F(3, 1_000_000), F(-2, 1_000_000), F(1, 1_000_000),
       F(-13, 10_000_000), F(17, 10_000_000), F(86, 10_000_000))
TIP_FLOAT = np.array([float(value) for value in TIP])


def _section(width, depth):
    young, nu = F(210_000_000_000), F(3, 10)
    shear = young / (2 * (1 + nu))
    area = width * depth
    iy, iz = width * depth**3 / 12, depth * width**3 / 12
    # The same declared Saint-Venant rectangle approximation as the earlier
    # physical-aspect diagnostic.  width >= depth for all declared sections.
    torsion = width * depth**3 * (
        F(1, 3) - F(21, 100) * depth / width *
        (1 - depth**4 / (12 * width**4)))
    principal = (young * area, shear * area * F(5, 6),
                 shear * area * F(5, 6), shear * torsion,
                 young * iy, young * iz)
    rotation = [[F(int(i == j)) for j in range(6)] for i in range(6)]
    for first, second in ((1, 2), (4, 5)):
        rotation[first][first] = rotation[second][second] = F(4, 5)
        rotation[first][second], rotation[second][first] = -F(3, 5), F(3, 5)
    stiffness = [[sum((rotation[i][k] * principal[k] * rotation[j][k]
                       for k in range(6)), F(0))
                  for j in range(6)] for i in range(6)]
    compliance = [[sum((rotation[i][k] * rotation[j][k] / principal[k]
                        for k in range(6)), F(0))
                   for j in range(6)] for i in range(6)]
    return LinearSection.generalized(stiffness), compliance


def _members(second):
    first_law, first_compliance = _section(*FIRST_M)
    second_law, second_compliance = _section(*second)
    members = (
        PhysicalB2Member("m0", "physical-rectangle-0", (0, 1),
                         ((0., 0., 0.), (2., 0., 0.)), (0., 1., 0.),
                         "rectangle-80x3", first_law),
        PhysicalB2Member("m1", "physical-rectangle-1", (1, 2),
                         ((2., 0., 0.), (2., 1.5, 0.)), (-1., 0., 0.),
                         "constant-area-aspect", second_law),
    )
    return members, (first_compliance, second_compliance)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _cut_energy(compliances, tip):
    """Exact independent force-method energy; no B/H or element K is used."""
    points = ((F(0), F(0), F(0)), (F(2), F(0), F(0)),
              (F(2), F(3, 2), F(0)))
    frames = (((1, 0, 0), (0, 1, 0), (0, 0, 1)),
              ((0, 1, 0), (-1, 0, 0), (0, 0, 1)))
    force, couple = tip[:3], tip[3:]
    total = F(0)
    for index, (length, compliance) in enumerate(zip((F(2), F(3, 2)),
                                                    compliances, strict=True)):
        densities = []
        for station in (F(0), F(1, 2), F(1)):
            point = tuple(points[index][i] + station *
                          (points[index + 1][i] - points[index][i])
                          for i in range(3))
            arm = tuple(points[-1][i] - point[i] for i in range(3))
            moment_arm = _cross(arm, force)
            global_wrench = (*force, *(couple[i] + moment_arm[i]
                                        for i in range(3)))
            local = tuple(sum((F(axis[k]) * global_wrench[part * 3 + k]
                               for k in range(3)), F(0))
                          for part in range(2) for axis in frames[index])
            strain = [sum((compliance[i][j] * local[j]
                           for j in range(6)), F(0)) for i in range(6)]
            densities.append(sum((local[i] * strain[i]
                                  for i in range(6)), F(0)))
        # Wrench is affine in station, so Simpson is exact for its energy.
        total += length * (densities[0] + 4 * densities[1] +
                           densities[2]) / 12
    return total


def _physical_tip(compliances):
    # Independent Castigliano derivative of the exact cut-wrench energy.
    result = []
    for index in range(6):
        direction = tuple(F(int(i == index)) for i in range(6))
        plus = tuple(TIP[i] + direction[i] for i in range(6))
        minus = tuple(TIP[i] - direction[i] for i in range(6))
        result.append((_cut_energy(compliances, plus) -
                       _cut_energy(compliances, minus)) / 2)
    return result


def _assembled(members):
    matrix = np.zeros((18, 18))
    for member in members:
        transform = member.local_dof_map()
        local = member.local_operator().evaluate(np.zeros(12)).tangent
        contribution = transform.T @ local @ transform
        indices = np.array([6 * node + component
                            for node in member.node_ids
                            for component in range(6)])
        matrix[np.ix_(indices, indices)] += contribution
    return matrix


def _exact_residual(matrix, state, rhs):
    return [sum((F(float(matrix[i, j])) * F(float(state[j]))
                 for j in range(12)), F(0)) - F(float(rhs[i]))
            for i in range(12)]


def _check_case(second):
    members, compliances = _members(second)
    physical_energy = _cut_energy(compliances, TIP)
    physical_tip = np.array([float(value) for value in _physical_tip(compliances)])
    assert physical_energy > 0
    assert max(abs(value) for value in physical_tip[:3]) < .015
    assert max(abs(value) for value in physical_tip[3:]) < .01

    matrix = _assembled(members)
    reduced = sparse.csc_matrix(matrix[6:, 6:])
    rhs = np.r_[np.zeros(6), TIP_FLOAT]
    diagonal = reduced.diagonal()
    assert np.isfinite(diagonal).all() and np.all(diagonal > 0)
    scale = 1 / np.sqrt(diagonal)
    scaled = (sparse.diags(scale) @ reduced @ sparse.diags(scale)).tocsc()
    assert np.isfinite(scaled.data).all()
    state = scale * splu(scaled).solve(scale * rhs)
    assert np.isfinite(state).all()
    defect = _exact_residual(reduced.toarray(), state, rhs)
    force_scale = max(abs(float(value)) for value in TIP[:3])
    moment_scale = max(max(abs(float(value)) for value in TIP[3:]),
                       2 * force_scale)
    forces, moments = (0, 1, 2, 6, 7, 8), (3, 4, 5, 9, 10, 11)
    force_ratio = max(float(abs(defect[i])) for i in forces) / force_scale
    moment_ratio = max(float(abs(defect[i])) for i in moments) / moment_scale
    root_arm = _cross((F(2), F(3, 2), F(0)), TIP[:3])
    root_couple = tuple(root_arm[i] + TIP[3 + i] for i in range(3))
    root_expected = -np.array([float(value) for value in (*TIP[:3],
                                                            *root_couple)])
    root_reaction = matrix[:6, 6:] @ state
    root_force_ratio = float(np.max(np.abs(root_reaction[:3] -
                                           root_expected[:3])) / force_scale)
    root_moment_ratio = float(np.max(np.abs(root_reaction[3:] -
                                            root_expected[3:])) / moment_scale)
    tip_error = np.max(np.abs(state[6:] - physical_tip) /
                       (1e-10 + 1e-8 * np.abs(physical_tip)))
    work_error = (abs(.5 * float(rhs @ state) - float(physical_energy)) /
                  float(physical_energy))
    return (force_ratio, moment_ratio, root_force_ratio, root_moment_ratio,
            float(tip_error), work_error)


def test_same_small_mixed_wrench_across_constant_area_aspect_family():
    assert all(width * depth == F(9, 250000)
               for width, depth in WIDTH_DEPTH_M)
    root_arm = _cross((F(2), F(3, 2), F(0)), TIP[:3])
    root_couple = tuple(root_arm[i] + TIP[3 + i] for i in range(3))
    assert root_couple == (F(1, 5_000_000), -F(3, 10_000_000),
                           F(1, 10_000_000))
    results = [_check_case(second) for second in WIDTH_DEPTH_M]
    for (force_ratio, moment_ratio, root_force_ratio, root_moment_ratio,
         tip_error, work_error) in results:
        assert force_ratio < 1e-9
        assert moment_ratio < 1e-9
        assert root_force_ratio < 1e-9
        assert root_moment_ratio < 1e-9
        assert tip_error < 1
        assert work_error < 1e-8
