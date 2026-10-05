"""Independent affine-field checks of the detached solid-side work map."""

import json

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_preflight import (
    DEFAULT_CASE, _element_domain_nodes, audit_rows, six_channel_rows,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import _replace_load
from scripts.b3_e4_f03_ccx_six_channel_reconstruct import _same_stiffness_deck
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


def test_detached_six_channel_reference_work():
    folder = DEFAULT_CASE
    meta = json.loads((folder / "model.json").read_text())
    deck, = folder.glob("*.inp")
    coords = _read_deck_nodes(deck)
    plate, bar = _element_domain_nodes(deck)
    assert not plate & bar
    rows, _ = six_channel_rows(coords, plate, bar, factor=4)
    audit = audit_rows(coords, rows,
                       supported=set(meta["boundary_node_ids"]))
    assert audit["rank"] == 6
    assert audit["max_rigid_translation_rotation_gap"] < 1e-12

    def evaluate(field):
        return np.array([sum(c * field(node, comp)
                             for (node, comp), c in row.items())
                         for row in rows])

    for comp in range(3):
        gap = evaluate(lambda node, axis: float(node in bar and axis == comp))
        expect = np.zeros(6)
        expect[comp] = -1.
        np.testing.assert_allclose(gap, expect, atol=2e-12)

    # A linear transverse shell-top displacement has a pure Mx/Mz gap.
    gap = evaluate(lambda node, axis: (coords[node][1] if
                   node in plate and abs(coords[node][2] - .0175) < 1e-10
                   and axis == 2 else 0.))
    np.testing.assert_allclose(gap, [0, 0, 0, 1, 0, 0], atol=2e-12)
    gap = evaluate(lambda node, axis: (-coords[node][1] if
                   node in plate and abs(coords[node][2] - .0175) < 1e-10
                   and axis == 0 else 0.))
    np.testing.assert_allclose(gap, [0, 0, 0, 0, 0, 1], atol=2e-12)

    # A plate-through-thickness pitch field has no top-face position gap.
    gap = evaluate(lambda node, axis: (-.035 if
                   node in plate and abs(coords[node][2] + .0175) < 1e-10
                   and axis == 0 else 0.))
    np.testing.assert_allclose(gap, [0, 0, 0, 0, 1, 0], atol=2e-12)

    rng = np.random.default_rng(8127)
    multipliers = rng.standard_normal(6)
    displacements = {key: value for key, value in zip(
        sorted({key for row in rows for key in row}),
        rng.standard_normal(audit["unique_nodal_dofs"]))}
    gap = evaluate(lambda node, axis: displacements.get((node, axis), 0.))
    side_work = sum(multipliers[channel] * coefficient * displacements[key]
                    for channel, row in enumerate(rows)
                    for key, coefficient in row.items())
    np.testing.assert_allclose(multipliers @ gap, side_work,
                               rtol=2e-14, atol=2e-13)

    # The external solve applies exactly C^T times its chosen dual scale.
    replacement = _replace_load(deck.read_text(), rows[3], 100.)
    cards = replacement.split("*CLOAD\n", 1)[1].split("*NODE PRINT", 1)[0]
    actual = {(int(node), int(axis)-1): float(value)
              for node, axis, value in
              (line.split(",") for line in cards.splitlines() if line)}
    assert len(actual) == len(rows[3])
    for key, value in rows[3].items():
        np.testing.assert_allclose(actual[key], 100 * value, rtol=2e-15)


def test_detached_loads_share_exact_stiffness_deck():
    torque, = DEFAULT_CASE.glob("*.inp")
    opening, = (DEFAULT_CASE.parent / "tip_fz").glob("*.inp")
    assert len(_same_stiffness_deck(torque, opening)) == 64
