from __future__ import annotations

from pathlib import Path
import os

import e4_pl_q1b_assembled_checker as checker
import e4_pl_q1b_assembled_producer as producer
import e4_pl_q1b_common as common


def test_q1b_thickness_and_mesh_locking_sequences(tmp_path: Path) -> None:
    registered = os.environ.get("Q1B_REGISTERED_EVIDENCE_ROOT")
    if registered:
        root = Path(registered)
        contract_sha = common.sha256((root / common.CONTRACT_PATH).read_bytes())
        _, cycle, _ = common.read_registered_cycle(root / "docs/reference_cases/e4_pl_q1b_cycle1.json", expected_cycle=1, expected_contract_sha256=contract_sha)
        shard = next(row for row in cycle["common_payload"]["shards"] if row["shard"] == "LOCKING_REFINEMENT")
        assert shard["contradictions"] == ["LOCKING_ANALYTICAL_ERROR"]
        assert shard["disagreements"] == [] and len(shard["coverage"]["rows"]) == 20
        return
    coverage = producer.locking_refinement()
    assert len(coverage["rows"]) == 4 * 5
    assert coverage["certified_failure"] is True
    record = {
        "candidate_id": common.CANDIDATE_ID,
        "coverage": coverage,
        "cycle": 1,
        "implementation_id": producer.IMPLEMENTATION_ID,
        "payload_sha256": common.sha256(common.canonical_bytes(coverage)),
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": common.SHARD_SCHEMA,
        "shard": "LOCKING_REFINEMENT",
        "study_id": common.STUDY_ID,
    }
    path = tmp_path / "locking.json"
    common.write_exclusive(path, record)
    checked = checker.verify(path)
    assert checked["disagreements"] == []
    assert checked["contradictions"] == ["LOCKING_ANALYTICAL_ERROR"]
