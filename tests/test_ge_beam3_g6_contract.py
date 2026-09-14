"""Static guards for the bounded G6 domain-parity contract."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "docs/reference_cases/ge_beam3_g6_contract_v1.json"


def _strict(raw: bytes):
    return json.loads(
        raw,
        object_pairs_hook=lambda pairs: _unique(pairs),
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)


def test_contract_is_canonical_complete_and_bounded():
    raw = CONTRACT.read_bytes().replace(b"\r\n", b"\n")
    contract = _strict(raw)
    assert raw == (
        json.dumps(contract, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    assert contract["base"] == {
        "commit": "84493c49bcf3792430fd67fc9176fa63eb4c0ea2",
        "tree": "c4a2094b2aa9ba8568bca65e6517bbff26edddbf",
    }
    assert len(contract["frozen_rows"]["parity"]) == 32
    assert len(contract["frozen_rows"]["unsupported"]) == 10
    assert contract["execution"] == {
        "automatic_retry": False,
        "child_seconds": 600,
        "formal_cycles": 2,
        "inactivity_seconds": 120,
        "max_workers": 3,
        "memory_gib": 24,
        "numerical_threads": 1,
        "scale_elements": [64, 256, 1024],
        "wave_seconds": 1800,
    }
    assert contract["production_default_qualified"] is False


def test_contract_bindings_match_frozen_git_blobs():
    contract = _strict(CONTRACT.read_bytes())
    for path, expected in contract["bindings"].items():
        raw = _git_bytes(path)
        assert len(raw) == expected["bytes"]
        assert sha256(raw).hexdigest() == expected["sha256"]


def test_contract_preserves_formulation_and_default_boundaries():
    contract = _strict(CONTRACT.read_bytes())
    assert set(contract["immutable"]) == {
        "accepted_g1_g5_evidence",
        "ge_local_formulation",
        "public_defaults",
        "qualified_q4_s3_mechanics",
    }
    assert all(contract["immutable"].values())
    assert contract["terminal_precedence"][-1] == (
        "PROVISIONAL_GO_GE_BEAM3_FULL_LEGACY_DOMAIN_PARITY_OPT_IN"
    )


def test_closeout_evidence_review_and_status_are_canonical_and_bound():
    directory = ROOT / "docs/reference_cases"
    paths = [directory / name for name in (
        "ge_beam3_g6_confirmation_v1.json",
        "ge_beam3_g6_confirmation_review_v1.json",
        "ge_beam3_g6_status_v1.json",
    )]
    values = []
    for path in paths:
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        value = _strict(raw)
        assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        values.append(value)
    confirmation, review, status = values
    confirmation_hash = sha256(paths[0].read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    review_hash = sha256(paths[1].read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert confirmation_hash == review["scope"]["confirmation_sha256"] == status["confirmation_sha256"]
    assert review_hash == status["review_sha256"]
    assert set(review) == {"decision", "findings", "reviewer", "scope", "subject_commit"}
    assert review["findings"] == [] and review["reviewer"]["independent"] is True
    assert confirmation["terminal"] == status["terminal"]
    assert confirmation["checks"]["formal_science_byte_identical"] is True
    assert confirmation["production_default_qualified"] is False
