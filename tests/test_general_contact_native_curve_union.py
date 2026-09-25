"""Conservative two-cell nearest-feature search without dropped contact."""

import numpy as np
import pytest

from anysolver.general_contact.native_curve_union import NativeTwoCellUnionSearch


def _line(first, last, y):
    return np.array(((first, y, 0.0),
                     (0.5*(first+last), y, 0.0),
                     (last, y, 0.0)))


def _search(source=None, *, target_y=0.08, radius=0.1,
            maximum_cells=10000):
    if source is None:
        source = _line(0.0, 1.0, 0.0)
    return NativeTwoCellUnionSearch(
        source, (_line(0.0, 0.5, target_y),
                 _line(0.5, 1.0, target_y)),
        ((1, 2, 3), (3, 4, 5)),
        combined_radius_m=radius,
        distance_tolerance_m=1e-10,
        feature_tolerance_m=1e-9,
        parameter_tolerance=1e-3,
        maximum_depth=20,
        maximum_cells=maximum_cells,
    )


def _covering(scan, station):
    return next(interval for interval in scan.intervals
                if interval.left <= station <= interval.right)


def test_shared_junction_switch_and_conservative_contact_support():
    search = _search()
    assert search.nearest(0.25).target_cell == 0
    assert search.nearest(0.75).target_cell == 1
    middle = search.nearest(0.5)
    assert middle.shared_junction_tie and middle.target_cell == 0
    scan = search.scan()
    assert scan.unresolved_intervals > 0
    assert any(item.status == "active" and item.target_cell == 0
               for item in scan.intervals)
    assert any(item.status == "active" and item.target_cell == 1
               for item in scan.intervals)
    assert scan.conservative_lower_gap_m <= -0.02
    for station in np.linspace(0.0, 1.0, 101):
        if search.nearest(float(station)).gap_m < 0.0:
            assert _covering(scan, station).status != "open"


def test_open_and_narrow_contact_pocket_are_not_dropped():
    clear = _search(target_y=0.3).scan()
    assert all(item.status == "open" for item in clear.intervals)
    source = np.array(((0.0, 0.3, 0.0),
                       (0.5, 0.09, 0.0),
                       (1.0, 0.3, 0.0)))
    search = _search(source, target_y=0.0)
    scan = search.scan()
    assert search.nearest(0.5).gap_m < 0.0
    assert _covering(scan, 0.5).status != "open"
    assert _covering(scan, 0.0).status == "open"
    assert _covering(scan, 1.0).status == "open"
    for station in np.linspace(0.0, 1.0, 201):
        if search.nearest(float(station)).gap_m < 0.0:
            assert _covering(scan, station).status != "open"


def test_remote_equal_minima_and_resource_exhaustion_fail_explicitly():
    source = _line(-0.2, 0.2, 1.0)
    target_a = np.array(((-1.0, 1.0, 0.0),
                         (-0.5, 0.5, 0.0),
                         (0.0, 0.0, 0.0)))
    target_b = np.array(((0.0, 0.0, 0.0),
                         (0.5, 0.5, 0.0),
                         (1.0, 1.0, 0.0)))
    ambiguous = NativeTwoCellUnionSearch(
        source, (target_a, target_b), ((1, 2, 3), (3, 4, 5)),
        combined_radius_m=0.8,
        distance_tolerance_m=1e-10,
        feature_tolerance_m=1e-9,
        parameter_tolerance=1e-3,
        maximum_depth=20,
        maximum_cells=10000,
    )
    with pytest.raises(ValueError, match="competing remote target minima"):
        ambiguous.nearest(0.5)
    with pytest.raises(MemoryError, match="cell budget exhausted"):
        _search(maximum_cells=1).scan()
    with pytest.raises(ValueError, match="shared material junction identity"):
        NativeTwoCellUnionSearch(
            _line(0.0, 1.0, 0.0),
            (_line(0.0, 0.5, 0.08), _line(0.5, 1.0, 0.08)),
            ((1, 2, 3), (6, 4, 5)),
            combined_radius_m=0.1,
            distance_tolerance_m=1e-10,
            feature_tolerance_m=1e-9,
            parameter_tolerance=1e-3,
            maximum_depth=20,
            maximum_cells=10000,
        )
