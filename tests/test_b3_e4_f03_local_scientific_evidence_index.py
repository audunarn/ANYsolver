import json
from pathlib import Path

import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence


SOURCE = "a" * 40
REGISTRATION = "b" * 64
START = "c" * 64


@pytest.fixture(scope="module")
def plan():
    records = cases.preflight_inventory()
    return archive.make_case_plan(records[0], records, SOURCE)


def _populate(directory: Path, plan):
    directory.mkdir()
    for index, name in enumerate(evidence.expected_members(plan)):
        path = directory.joinpath(*Path(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((f"member-{index}-{name}\n").encode("ascii"))


def test_index_roundtrip_binds_exact_order_plan_start_and_member_bytes(plan, tmp_path):
    directory = tmp_path / "case"
    _populate(directory, plan)
    written, digest = evidence.write_index(directory, plan, REGISTRATION, START)
    restored, observed = evidence.read_index(directory, plan, REGISTRATION, START)
    assert restored == written
    assert observed == digest
    assert tuple(item.name for item in restored.members) == evidence.expected_members(plan)
    assert restored.total_bytes == sum(item.bytes for item in restored.members)
    with pytest.raises(FileExistsError):
        evidence.write_index(directory, plan, REGISTRATION, START)


def test_missing_changed_and_stale_identity_rejected(plan, tmp_path):
    missing = tmp_path / "missing"
    _populate(missing, plan)
    missing.joinpath(*Path(evidence.expected_members(plan)[3]).parts).unlink()
    with pytest.raises(FileNotFoundError):
        evidence.write_index(missing, plan, REGISTRATION, START)

    changed = tmp_path / "changed"
    _populate(changed, plan)
    evidence.write_index(changed, plan, REGISTRATION, START)
    changed.joinpath(*Path(evidence.expected_members(plan)[0]).parts).write_bytes(b"changed")
    with pytest.raises(ValueError, match="stale|mismatched"):
        evidence.read_index(changed, plan, REGISTRATION, START)
    with pytest.raises(ValueError):
        evidence.read_index(changed, plan, "d" * 64, START)


def _rewrite(path: Path, mutate):
    value = json.loads(path.read_text("ascii"))
    mutate(value)
    path.write_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )


def test_extra_reordered_duplicate_and_noncanonical_index_rejected(plan, tmp_path):
    mutations = (
        lambda value: value.update(extra=True),
        lambda value: value["members"].reverse(),
        lambda value: value["members"].append(dict(value["members"][0])),
        lambda value: value["members"][0].update(kind="json"),
    )
    for number, mutate in enumerate(mutations):
        directory = tmp_path / f"bad-{number}"
        _populate(directory, plan)
        evidence.write_index(directory, plan, REGISTRATION, START)
        _rewrite(directory / "evidence_index.json", mutate)
        with pytest.raises(ValueError):
            evidence.read_index(directory, plan, REGISTRATION, START)


def test_total_bound_rejects_before_first_hash(plan, tmp_path, monkeypatch):
    directory = tmp_path / "bounded"
    _populate(directory, plan)
    names = evidence.expected_members(plan)
    monkeypatch.setattr(
        evidence, "_hash_member", lambda *a, **k: pytest.fail("hashing must not begin"),
    )
    with pytest.raises(ValueError, match="byte limit"):
        evidence._sizes(directory, names, len(names) - 1)


def test_index_size_bound_precedes_json_decode(plan, tmp_path, monkeypatch):
    directory = tmp_path / "oversize"
    _populate(directory, plan)
    path = directory / "evidence_index.json"
    path.write_bytes(b"x" * 32)
    monkeypatch.setattr(evidence, "MAX_INDEX_BYTES", 16)
    monkeypatch.setattr(json, "loads", lambda *a, **k: pytest.fail("must reject first"))
    with pytest.raises(ValueError, match="bound"):
        evidence.read_index(directory, plan, REGISTRATION, START)
