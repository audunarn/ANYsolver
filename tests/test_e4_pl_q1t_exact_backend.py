from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases"
ENV_SHA = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"


def _strict(raw: bytes) -> dict[str, object]:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(key)
            out[key] = value
        return out

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert isinstance(value, dict)
    expected = (json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    assert raw == expected
    return value


def _run(program: Path, environment_root: Path | None = None) -> tuple[dict[str, object], bytes]:
    command = [sys.executable, str(program), "--toy-exact-backend"]
    if environment_root is not None:
        command.extend(["--environment-root", str(environment_root), "--environment-sha256", ENV_SHA])
    completed = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return _strict(completed.stdout), completed.stdout


def test_q1t_exact_backend_toy_cancellation_nested_radicals_inverse_rank_sign_and_serialization() -> None:
    root_text = os.environ.get("Q1T_EXACT_ENV_ROOT")
    assert root_text, "Q1T_EXACT_ENV_ROOT must name the frozen external exact environment"
    environment_root = Path(root_text).resolve(strict=True)
    assert environment_root.is_dir()

    ref1, raw_ref1 = _run(CASES / "e4_pl_q1t_reference.py")
    ref2, raw_ref2 = _run(CASES / "e4_pl_q1t_reference.py")
    ora1, raw_ora1 = _run(CASES / "e4_pl_q1t_oracle.py", environment_root)
    ora2, raw_ora2 = _run(CASES / "e4_pl_q1t_oracle.py", environment_root)
    assert raw_ref1 == raw_ref2 and raw_ora1 == raw_ora2

    for value, implementation_id in ((ref1, "Q1T_REFERENCE_STDLIB_FIELD_ALG"), (ora1, "Q1T_ORACLE_SYMPY_ALGEBRAIC_FIELD")):
        assert value["implementation_id"] == implementation_id
        assert value["mechanics_executed"] is False
        assert value["domain_equalities"]["exact_cancellation"] is True
        assert value["domain_equalities"]["inverse"] is True
        assert value["domain_equalities"]["nested_square"] is True
        assert value["matrix_rank"] == 2
        assert value["nested_positive"] is True
        assert value["zero_never_called_intervals"] is True
