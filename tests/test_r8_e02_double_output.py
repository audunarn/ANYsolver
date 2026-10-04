"""Independent count-framing controls for the pinned double-output evidence."""
import copy
import math
import struct
from dataclasses import dataclass

import pytest

from scripts.r8_e02_double_output import compare_double_with_print, read_double_output
from scripts.r8_e02_rigid_tip_reference import ReferenceParseError


def fixture():
    nodes = {n: (n/20, 0., .01) for n in range(1, 21)}
    metadata = dict(physical_nodes=nodes, elements={1: tuple(range(1, 21))}, root_nodes=[1, 2])
    u = {n: (n*1e-6, -n*1e-7, 0.) for n in nodes}
    rf = {1: (1., 2., 3.), 2: (-1., -2., -3.)}
    chunks = [b"    1C\n    1UPGM               CalculiX\n    1UVERSION           Version 2.23\n",
              b"    2C 20 3\n"]
    chunks.extend(struct.pack("<i3d", n, *p) for n, p in nodes.items())
    chunks.append(b"    3C 1 2\n")
    # Independent explicit he20 order, not imported parser constants.
    chunks.append(struct.pack("<24i", 1, 4, 0, 1,
        1,2,3,4,5,6,7,8,9,10,11,12,17,18,19,20,13,14,15,16))
    for number, name, prefix, values in ((1, "DISP", "D", u), (2, "FORC", "F", rf)):
        chunks.append((f"    1PSTEP {number} 1 1\n  100CL 101 1.000000000 {len(values)} 0 1 3\n"
                       f" -4 {name} 4 1\n").encode("ascii"))
        chunks.extend(f" -5 {prefix}{j} 1 2 {j} 0\n".encode("ascii") for j in range(1, 4))
        chunks.append(b" -5 ALL 1 2 0 0 1ALL\n")
        chunks.extend(struct.pack("<i3d", n, *v) for n, v in values.items())
    chunks.append(b" 9999\n")
    return b"".join(chunks), metadata, u, rf


def test_valid_binary64_and_owned_vectors_with_text_bytes_in_payload():
    data, metadata, u, rf = fixture()
    # A finite binary64 with bytes resembling an ASCII record is still data.
    value = struct.unpack("<d", b" -4  XXX")[0]
    assert math.isfinite(value)
    data = data.replace(struct.pack("<i3d", 20, *u[20]), struct.pack("<i3d", 20, value, 0., 0.))
    u[20] = (value, 0., 0.)
    assert read_double_output(data, metadata) == (u, rf)
    first, _ = read_double_output(data, metadata)
    first[1] = (9., 9., 9.)
    assert read_double_output(data, metadata)[0] == u


@pytest.mark.parametrize("old,new", [
    (b"2C 20 3", b"2C 20 2"), (b"2C 20 3", b"2C 21 3"),
    (b"3C 1 2", b"3C 2 2"), (b"Version 2.23", b"Version 2.22"),
    (b"DISP", b"FORC"), (b"D2 1 2 2 0", b"D2 1 2 3 0"),
    (b"1.000000000", b"2.000000000"), (b"1PSTEP 2 1 1", b"1PSTEP 2 2 1"),
    (b"1ALL", b"2ALL"), (b"9999", b"9998"),
])
def test_reject_wrong_framing_labels_counts_time_and_version(old, new):
    data, metadata, *_ = fixture()
    with pytest.raises(ReferenceParseError):
        read_double_output(data.replace(old, new, 1), metadata)


@pytest.mark.parametrize("offset", (1, 8, 28, 100, 400, 900))
def test_reject_truncation_and_trailing_data(offset):
    data, metadata, *_ = fixture()
    with pytest.raises(ReferenceParseError):
        read_double_output(data[:-offset], metadata)
    with pytest.raises(ReferenceParseError, match="trailing"):
        read_double_output(data+b"\n", metadata)


@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf))
def test_reject_nonfinite_vectors(value):
    data, metadata, u, _ = fixture()
    data = data.replace(struct.pack("<i3d", 3, *u[3]), struct.pack("<i3d", 3, value, 0., 0.))
    with pytest.raises(ReferenceParseError, match="nonfinite"):
        read_double_output(data, metadata)


def test_reject_duplicate_or_unexpected_nodes_and_changed_connectivity():
    data, metadata, u, _ = fixture()
    for wrong in (2, 21):
        bad = data.replace(struct.pack("<i3d", 3, *u[3]), struct.pack("<i3d", wrong, *u[3]))
        with pytest.raises(ReferenceParseError, match="node"):
            read_double_output(bad, metadata)
    changed = copy.deepcopy(metadata)
    changed["elements"][1] = tuple(reversed(changed["elements"][1]))
    with pytest.raises(ReferenceParseError, match="connectivity"):
        read_double_output(data, changed)


def test_coordinate_roundoff_admission_is_bounded_not_a_geometry_tolerance():
    data, metadata, *_ = fixture()
    changed = copy.deepcopy(metadata)
    changed["physical_nodes"][3] = (.15+math.ulp(1.), 0., .01)
    read_double_output(data, changed)
    changed["physical_nodes"][3] = (.15+1e-10, 0., .01)
    with pytest.raises(ReferenceParseError, match="coordinates"):
        read_double_output(data, changed)


def test_binary_values_must_match_dat_resolution_not_just_dataset_ids():
    data, metadata, u, rf = fixture()
    metadata.update(applied_wrench=(0., 0., 0., 1., 0., 0.), port_m=(0., 0., 0.))
    @dataclass
    class Observed:
        translation: tuple
    class Action:
        node_ids = ()
        forces_n = ()
        def work(self, values): return 0.
    class Area:
        def action(self, force, couple): return Action()
        def recover(self, values): return Observed(values[1])
    dat = ""
    for name, group, values in (("displacements", "ALL", u), ("forces", "ROOT", rf)):
        dat += f"{name} (vx,vy,vz) for set {group} and time 1.0000000E+00\n\n"
        dat += "".join(str(n)+" "+" ".join(f"{v:.6E}" for v in p)+"\n" for n, p in values.items())
    stdout = "CalculiX Version 2.23,\n Using up to 1 cpu(s)\n Job finished\n"
    result = compare_double_with_print(data, dat, stdout, metadata, Area())
    assert result["displacement_count"] == 20 and result["reaction_count"] == 2
    assert result["root_wrench_error"] == pytest.approx((0., 0., 0., 1., .15, -.1))
    split = dat.index("forces (")
    reordered = dat[split:] + dat[:split]
    assert compare_double_with_print(data, reordered, stdout, metadata, Area()) == result
    # Move one full-precision reaction while retaining a valid binary layout.
    bad = data.replace(struct.pack("<i3d", 1, *rf[1]), struct.pack("<i3d", 1, 1.00001, 2., 3.))
    with pytest.raises(ReferenceParseError, match="printed resolution"):
        compare_double_with_print(bad, dat, stdout, metadata, Area())
