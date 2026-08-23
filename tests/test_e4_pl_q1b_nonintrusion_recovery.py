from __future__ import annotations

from pathlib import Path
import os

import e4_pl_q1b_assembled_producer as producer
import e4_pl_q1b_common as common


ROOT = Path(__file__).resolve().parents[1]


def test_q1b_numerical_diagnostics_remain_outside_physical_recovery() -> None:
    registered = os.environ.get("Q1B_REGISTERED_EVIDENCE_ROOT")
    if registered:
        root = Path(registered)
        contract_sha = common.sha256((root / common.CONTRACT_PATH).read_bytes())
        _, cycle, _ = common.read_registered_cycle(root / "docs/reference_cases/e4_pl_q1b_cycle1.json", expected_cycle=1, expected_contract_sha256=contract_sha)
        shard = next(row for row in cycle["common_payload"]["shards"] if row["shard"] == "NONINTRUSION_RECOVERY")
        assert shard["contradictions"] == [] and shard["disagreements"] == []
        assert len(shard["coverage"]["rows"]) == 6
        return
    result = producer.nonintrusion(ROOT)
    assert len(result["rows"]) == 6
    assert result["certified_failure"] is False
    for row in result["rows"]:
        assert row["numerical_reactions_reported_separately"] is True
        assert float.fromhex(row["physical_drill_contamination"]["hi"]) <= 1.0e-10
        assert float.fromhex(row["reaction_split_error"]["hi"]) <= 1.0e-10
