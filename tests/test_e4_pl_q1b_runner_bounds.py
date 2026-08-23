from __future__ import annotations

from pathlib import Path
import os
import sys
import time

import e4_pl_q1b_bounded_runner as runner
import e4_pl_q1b_common as common


def test_q1b_parallel_bounds_timeout_and_determinism(tmp_path: Path) -> None:
    registered = os.environ.get("Q1B_REGISTERED_EVIDENCE_ROOT")
    if registered:
        root = Path(registered) / "docs/reference_cases"
        contract_sha = common.sha256((Path(registered) / common.CONTRACT_PATH).read_bytes())
        _, first, first_payload = common.read_registered_cycle(root / "e4_pl_q1b_cycle1.json", expected_cycle=1, expected_contract_sha256=contract_sha)
        _, second, second_payload = common.read_registered_cycle(root / "e4_pl_q1b_cycle2.json", expected_cycle=2, expected_contract_sha256=contract_sha)
        assert first_payload == second_payload
        assert first["common_payload_sha256"] == second["common_payload_sha256"] == common.sha256(first_payload)
        return
    commands = []
    for index in range(3):
        directory = tmp_path / f"overlap-{index}"
        commands.append((str(index), [sys.executable, "-c", "import time; time.sleep(.15)"], directory))
    started = time.monotonic()
    rows = runner.run_wave(commands, timeout_seconds=2, memory_limit_gib=1)
    assert time.monotonic() - started < .40
    assert len(rows) == 3 and all(row.returncode == 0 for row in rows)
    timeout_dir = tmp_path / "timeout"
    timed = runner.run_wave(
        [("timeout", [sys.executable, "-c", "from pathlib import Path; Path('record.json').write_text('partial'); import time; time.sleep(2)"], timeout_dir)],
        timeout_seconds=1,
        memory_limit_gib=1,
    )
    assert timed[0].timed_out is True
    assert not (timeout_dir / "record.json").exists()
