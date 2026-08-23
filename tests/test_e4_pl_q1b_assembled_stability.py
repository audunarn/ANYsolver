from __future__ import annotations

import os
from pathlib import Path

import e4_pl_q1b_assembled_producer as producer
import e4_pl_q1b_common as common


ROOT = Path(__file__).resolve().parents[1]


def test_q1b_supported_assembled_stability_and_coercivity() -> None:
    registered = os.environ.get("Q1B_REGISTERED_EVIDENCE_ROOT")
    if registered:
        root = Path(registered)
        contract_sha = common.sha256((root / common.CONTRACT_PATH).read_bytes())
        _, cycle, _ = common.read_registered_cycle(root / "docs/reference_cases/e4_pl_q1b_cycle1.json", expected_cycle=1, expected_contract_sha256=contract_sha)
        shard = next(row for row in cycle["common_payload"]["shards"] if row["shard"] == "ASSEMBLED_STABILITY")
        assert shard["contradictions"] == [] and shard["disagreements"] == []
        assert len(shard["coverage"]["rows"]) == 24
        assert shard["coverage"]["domain_certificate"]["status"] == "UNRESOLVED_NOT_FINITE_SAMPLE_SUBSTITUTION"
        return
    evidence = os.environ.get("Q1B_Q1Y3_EVIDENCE_ROOT")
    assert evidence, "Q1B_Q1Y3_EVIDENCE_ROOT is required for exact commissioning"
    commissioning = producer.commission(ROOT, Path(evidence))
    assert commissioning["all_equivalent"] is True
    assert len(commissioning["rows"]) == 6
    result = producer.assembled_stability(ROOT)
    assert len(result["rows"]) == 6 * 4
    assert result["certified_failure"] is False
    assert result["domain_certificate"]["status"] == "UNRESOLVED_NOT_FINITE_SAMPLE_SUBSTITUTION"
    assert all(row["elements"] == row["level"] ** 2 for row in result["rows"])
