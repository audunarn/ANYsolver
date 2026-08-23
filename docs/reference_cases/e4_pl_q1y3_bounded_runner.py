"""Q1Y3 schema/terminal wrapper around the accepted Q1Y2 pipeline."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import e4_pl_q1y2_bounded_runner as previous


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1y3-local-algebra-contract-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1y3-algebra-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1y3-algebra-aggregate-v1"


@contextmanager
def _q1y3_schemas() -> Iterator[None]:
    old = (previous.CONTRACT_SCHEMA, previous.CHECK_SCHEMA, previous.AGGREGATE_SCHEMA)
    previous.CONTRACT_SCHEMA = CONTRACT_SCHEMA
    previous.CHECK_SCHEMA = CHECK_SCHEMA
    previous.AGGREGATE_SCHEMA = AGGREGATE_SCHEMA
    try:
        yield
    finally:
        previous.CONTRACT_SCHEMA, previous.CHECK_SCHEMA, previous.AGGREGATE_SCHEMA = old

WeightedAdmission = previous.WeightedAdmission
discard_incomplete_output = previous.discard_incomplete_output
select_terminal = previous.select_terminal


def validate_successor_contract(*args: Any, **kwargs: Any) -> dict[str, Any]:
    with _q1y3_schemas():
        return previous.validate_successor_contract(*args, **kwargs)


def execute_pipelined(*args: Any, **kwargs: Any) -> dict[str, Any]:
    with _q1y3_schemas():
        return previous.execute_pipelined(*args, **kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    with _q1y3_schemas():
        return previous.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
