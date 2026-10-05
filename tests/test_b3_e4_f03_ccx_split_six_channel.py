"""Work-map and longitudinal-resolution witnesses for split solid rows."""

from pathlib import Path

import numpy as np
import pytest

from scripts.b3_e4_f03_ccx_split_six_channel import (
    _element_domain_nodes, _source, preflight, split_rows,
)
from scripts.b3_e4_f03_ccx_six_channel_preflight import six_channel_rows


SOURCE = Path(__file__).resolve().parents[1] / (
    ".qualification/b3-ge-e4-pl/f03-c1-detached-port-dev-20260926-v2/tip_mx")


@pytest.fixture(scope="module")
def split_fixture():
    deck, meta, coords, _, _, _ = _source(SOURCE)
    plate, bar = _element_domain_nodes(deck)
    rows = split_rows(coords, plate, bar)
    return coords, meta, plate, bar, rows


def _apply(row, variation):
    return sum(value*variation.get(key, 0.) for key, value in row.items())


def test_split_rows_preserve_global_mean_and_rigid_work(split_fixture):
    coords, meta, plate, bar, rows = split_fixture
    audit = preflight(coords, rows, set(meta["boundary_node_ids"]),
                      plate, bar)
    assert audit["rank"] == 12
    assert audit["max_rigid_gap"] < 2e-9
    assert audit["max_mean_recomposition_defect"] < 1e-12
    original, _ = six_channel_rows(coords, plate, bar, factor=4)
    rng = np.random.default_rng(43)
    directions = {key: rng.normal() for row in rows for key in row}
    np.testing.assert_allclose(
        [_apply(original[j], directions) for j in range(6)],
        [(_apply(rows[j], directions)+_apply(rows[j+6], directions))/2
         for j in range(6)], rtol=0, atol=1e-12)


def test_split_rows_detect_longitudinal_gap_invisible_to_global_mean(
        split_fixture):
    coords, _, plate, bar, rows = split_fixture
    variation = {(node, 2): float(coords[node][0]-.95)
                 for node in plate if
                 abs(coords[node][2]-.0175) < 1e-10 and
                 .9-1e-10 <= coords[node][0] <= 1.+1e-10 and
                 abs(coords[node][1]) <= .05+1e-10}
    original, _ = six_channel_rows(coords, plate, bar, factor=4)
    assert abs(_apply(original[2], variation)) < 1e-12
    assert abs(_apply(rows[2], variation)+.025) < 1e-12
    assert abs(_apply(rows[8], variation)-.025) < 1e-12
