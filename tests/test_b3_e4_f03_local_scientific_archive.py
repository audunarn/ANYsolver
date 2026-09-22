import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases


SOURCE = "a" * 40


@pytest.fixture(scope="module")
def records():
    return cases.preflight_inventory()


def test_plan_roundtrip_and_complete_single_use_inverse_stream(records, tmp_path):
    record = records[-1]
    plan = archive.make_case_plan(record, records, SOURCE)
    path = tmp_path / "plan.zip"
    archive.write_plan(path, plan)
    restored = archive.read_plan(path, record, records, SOURCE)
    assert restored == plan
    assert restored.inverse_blocks[0].start == 0
    assert restored.inverse_blocks[-1].start + restored.inverse_blocks[-1].columns == 1473
    assert sum(block.bytes for block in restored.inverse_blocks) == 17_357_832
    assert restored.raw_archive_bytes == 512 * 1024**2
    assert restored.resource_limits == cases.resource_contract()
    assert len(restored.members) == len(set(restored.members))
    with pytest.raises(FileExistsError):
        archive.write_plan(path, plan)


def _rewrite(path: Path, members: list[tuple[str, bytes]]):
    with zipfile.ZipFile(path, "w") as output:
        for name, payload in members:
            output.writestr(name, payload)


def test_missing_extra_duplicate_and_digest_corruption_rejected(records, tmp_path):
    record = records[0]
    plan = archive.make_case_plan(record, records, SOURCE)
    valid = tmp_path / "valid.zip"
    archive.write_plan(valid, plan)
    with zipfile.ZipFile(valid) as source:
        payload = source.read("plan.json")
        digest = source.read("plan.sha256")
    variants = (
        [("plan.json", payload)],
        [("plan.json", payload), ("plan.sha256", digest), ("extra", b"x")],
        [("plan.json", payload), ("plan.json", payload), ("plan.sha256", digest)],
        [("plan.json", payload + b" "), ("plan.sha256", digest)],
    )
    for index, members in enumerate(variants):
        target = tmp_path / f"bad-{index}.zip"
        if index == 2:
            with pytest.warns(UserWarning):
                _rewrite(target, members)
        else:
            _rewrite(target, members)
        with pytest.raises(ValueError):
            archive.read_plan(target, record, records, SOURCE)


def test_stale_source_case_topology_and_inventory_rejected(records, tmp_path):
    record = records[1]
    path = tmp_path / "plan.zip"
    archive.write_plan(path, archive.make_case_plan(record, records, SOURCE))
    with pytest.raises(ValueError, match="stale|mismatched"):
        archive.read_plan(path, record, records, "b" * 40)
    with pytest.raises(ValueError):
        archive.read_plan(path, records[0], records, SOURCE)
    with pytest.raises(ValueError):
        archive.make_case_plan(record, tuple(reversed(records)), SOURCE)


def test_manifest_missing_extra_reordered_blocks_and_names_rejected(records):
    plan = archive.make_case_plan(records[0], records, SOURCE)
    value = json.loads(archive._payload(plan))
    mutations = []
    missing = dict(value); missing.pop("case_id"); mutations.append(missing)
    extra = dict(value, extra=True); mutations.append(extra)
    reordered = dict(value); reordered["inverse_blocks"] = list(reversed(value["inverse_blocks"])); mutations.append(reordered)
    renamed = json.loads(json.dumps(value)); renamed["inverse_blocks"][0]["name"] = "inverse/stale.npy"; mutations.append(renamed)
    groups = dict(value); groups["group_members"] = value["group_members"][:-1]; mutations.append(groups)
    resources = json.loads(json.dumps(value)); resources["resource_limits"]["raw_archive_bytes"] += 1; mutations.append(resources)
    raw_cap = dict(value); raw_cap["raw_archive_bytes"] += 1; mutations.append(raw_cap)
    for mutation in mutations:
        payload = (json.dumps(mutation, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        with pytest.raises(ValueError):
            archive._decode(payload)


def test_archive_bound_checked_before_zip_open(records, tmp_path, monkeypatch):
    path = tmp_path / "oversize.zip"
    path.write_bytes(b"x" * 32)
    monkeypatch.setattr(archive, "MAX_PLAN_BYTES", 16)
    monkeypatch.setattr(zipfile, "ZipFile", lambda *a, **k: pytest.fail("bound must reject first"))
    with pytest.raises(ValueError, match="bound"):
        archive.read_plan(path, records[0], records, SOURCE)
