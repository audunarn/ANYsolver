"""Minimal process entry point for one registered F03 evidence producer."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from scripts import _b3_e4_f03_local_scientific_case_producer as producer


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts._b3_e4_f03_local_scientific_case_entry",
    )
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--registration-sha256", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    values = _arguments(argv)
    producer.produce_registered_case(
        values.directory,
        values.source_commit,
        values.registration_sha256,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
