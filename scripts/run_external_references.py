"""Generate external FE reference input decks and report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anysolver.external_references import DEFAULT_EXTERNAL_REFERENCE_PATH, write_external_reference_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_EXTERNAL_REFERENCE_PATH)
    parser.add_argument("--deck-dir", type=Path, default=Path("reports/external_references/decks"))
    parser.add_argument("--markdown", type=Path, default=None)
    args = parser.parse_args()

    report = write_external_reference_report(args.output, deck_dir=args.deck_dir, markdown=args.markdown)
    print(f"Wrote {args.output}")
    if args.markdown is not None:
        print(f"Wrote {args.markdown}")
    print(f"Generated {len(report.get('cases', []))} external reference decks in {args.deck_dir}")
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
