"""Generate the frozen nested Q4/S3 mixed-mesh connectivity manifest.

This research-only generator uses the standard library.  It creates no FE
mechanics and makes no production selection decision.  The base 20x20 cell
mask is expanded by factors 1, 2, 4 and 8, which is exactly the required
one-to-four refinement of both Q4 and paired-S3 topology.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator, Sequence


SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-connectivity-manifest-v1"
BASE_GRID = 20
LEVELS = (20, 40, 80, 160)
SPLIT_COUNTS = (0, 4, 20, 40, 100)
RESEARCH_CONTROL_SPLIT_COUNT = BASE_GRID**2
MASKS = (
    "dispersed",
    "chain",
    "compact_cluster",
    "boundary_band",
    "hole_band",
)
DIAGONALS = ("slash", "backslash", "alternating")
HASH_ENCODING = "UTF8_LF_N_COLON_KIND_COLON_COMMA_NODE_IDS_V1"


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _all_cells() -> tuple[tuple[int, int], ...]:
    return tuple(
        (i, j) for j in range(BASE_GRID) for i in range(BASE_GRID)
    )


def _perimeter(layer: int) -> Iterator[tuple[int, int]]:
    low = int(layer)
    high = BASE_GRID - 1 - low
    if low > high:
        return
    if low == high:
        yield low, low
        return
    for i in range(low, high + 1):
        yield i, low
    for j in range(low + 1, high + 1):
        yield high, j
    for i in range(high - 1, low - 1, -1):
        yield i, high
    for j in range(high - 1, low, -1):
        yield low, j


def ordered_mask_cells(mask: str) -> tuple[tuple[int, int], ...]:
    """Return one deterministic nested ordering of all 400 base cells."""

    name = str(mask)
    cells = _all_cells()
    if name == "dispersed":
        ordered = tuple(
            ((37 * index) % BASE_GRID, ((37 * index) % (BASE_GRID**2)) // BASE_GRID)
            for index in range(BASE_GRID**2)
        )
    elif name == "chain":
        rows: list[int] = []
        lower = BASE_GRID // 2 - 1
        upper = BASE_GRID // 2
        for offset in range(BASE_GRID // 2):
            rows.extend((lower - offset, upper + offset))
        chain: list[tuple[int, int]] = []
        for row_index, row in enumerate(rows):
            columns: Iterable[int] = range(BASE_GRID)
            if row_index % 2:
                columns = range(BASE_GRID - 1, -1, -1)
            chain.extend((column, row) for column in columns)
        ordered = tuple(chain)
    elif name == "compact_cluster":
        ordered = tuple(
            sorted(
                cells,
                key=lambda cell: (
                    max(abs(2 * cell[0] - 19), abs(2 * cell[1] - 19)),
                    (2 * cell[0] - 19) ** 2 + (2 * cell[1] - 19) ** 2,
                    cell[1],
                    cell[0],
                ),
            )
        )
    elif name == "boundary_band":
        ordered = tuple(
            cell
            for layer in range((BASE_GRID + 1) // 2)
            for cell in _perimeter(layer)
        )
    elif name == "hole_band":
        ordered = tuple(
            sorted(
                cells,
                key=lambda cell: (
                    abs(
                        (2 * cell[0] - 19) ** 2
                        + (2 * cell[1] - 19) ** 2
                        - 81
                    ),
                    cell[1],
                    cell[0],
                ),
            )
        )
    else:
        raise ValueError(f"unknown mixed-mesh mask {mask!r}")
    if len(ordered) != BASE_GRID**2 or len(set(ordered)) != len(ordered):
        raise AssertionError(f"mask {name!r} is not a permutation of the base grid")
    return ordered


def selected_base_cells(mask: str, split_count: int) -> tuple[tuple[int, int], ...]:
    count = int(split_count)
    if count not in SPLIT_COUNTS:
        raise ValueError(f"unsupported split-cell count {count}")
    if count == 0:
        return ()
    return tuple(sorted(ordered_mask_cells(mask)[:count], key=lambda value: (value[1], value[0])))


def expanded_split_cells(
    base_cells: Sequence[tuple[int, int]], level: int
) -> frozenset[tuple[int, int]]:
    n = int(level)
    if n not in LEVELS or n % BASE_GRID:
        raise ValueError(f"unsupported refinement level {n}")
    factor = n // BASE_GRID
    return frozenset(
        (factor * i + di, factor * j + dj)
        for i, j in base_cells
        for dj in range(factor)
        for di in range(factor)
    )


def _node_id(i: int, j: int, level: int) -> int:
    return int(j) * (int(level) + 1) + int(i) + 1


def _cell_connectivity(
    i: int,
    j: int,
    level: int,
    *,
    split: bool,
    diagonal: str,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    n00 = _node_id(i, j, level)
    n10 = _node_id(i + 1, j, level)
    n11 = _node_id(i + 1, j + 1, level)
    n01 = _node_id(i, j + 1, level)
    if not split:
        return (("Q4", (n00, n10, n11, n01)),)
    made = str(diagonal)
    if made == "alternating":
        made = "backslash" if (int(i) + int(j)) % 2 == 0 else "slash"
    if made == "backslash":
        return (
            ("S3", (n00, n10, n11)),
            ("S3", (n00, n11, n01)),
        )
    if made == "slash":
        return (
            ("S3", (n00, n10, n01)),
            ("S3", (n10, n11, n01)),
        )
    raise ValueError(f"unknown diagonal policy {diagonal!r}")


def connectivity_sha256(
    level: int,
    split_cells: frozenset[tuple[int, int]],
    diagonal: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(f"level:{int(level)}\n".encode("ascii"))
    element_id = 0
    for j in range(int(level)):
        for i in range(int(level)):
            for kind, node_ids in _cell_connectivity(
                i,
                j,
                int(level),
                split=(i, j) in split_cells,
                diagonal=diagonal,
            ):
                element_id += 1
                nodes = ",".join(str(value) for value in node_ids)
                digest.update(
                    f"{element_id}:{kind}:{nodes}\n".encode("ascii")
                )
    return digest.hexdigest().upper()


def build_manifest() -> dict[str, object]:
    records: list[dict[str, object]] = []
    for split_count in SPLIT_COUNTS:
        active_masks = (None,) if split_count == 0 else MASKS
        for mask in active_masks:
            base_cells = () if mask is None else selected_base_cells(mask, split_count)
            base_hash = hashlib.sha256(_canonical_bytes(base_cells)).hexdigest().upper()
            for diagonal in DIAGONALS:
                for level in LEVELS:
                    split_cells = expanded_split_cells(base_cells, level)
                    factor = int(level) // BASE_GRID
                    expected_split = int(split_count) * factor * factor
                    if len(split_cells) != expected_split:
                        raise AssertionError("refined split-cell count is inconsistent")
                    q4_count = int(level) ** 2 - expected_split
                    s3_count = 2 * expected_split
                    records.append(
                        {
                            "connectivity_sha256": connectivity_sha256(
                                level, split_cells, diagonal
                            ),
                            "diagonal": diagonal,
                            "element_count": q4_count + s3_count,
                            "level": int(level),
                            "mask": "none" if mask is None else mask,
                            "node_count": (int(level) + 1) ** 2,
                            "q4_element_count": q4_count,
                            "s3_area_fraction_percent": int(split_count) // 4,
                            "s3_element_count": s3_count,
                            "selected_base_cells_sha256": base_hash,
                            "split_base_cell_count": int(split_count),
                            "split_refined_cell_count": expected_split,
                        }
                    )
    control_base_cells = _all_cells()
    control_base_hash = hashlib.sha256(
        _canonical_bytes(control_base_cells)
    ).hexdigest().upper()
    research_control_records: list[dict[str, object]] = []
    for diagonal in DIAGONALS:
        for level in LEVELS:
            split_cells = expanded_split_cells(control_base_cells, level)
            expected_split = int(level) ** 2
            if len(split_cells) != expected_split:
                raise AssertionError("all-S3 control does not cover every refined cell")
            research_control_records.append(
                {
                    "connectivity_sha256": connectivity_sha256(
                        level, split_cells, diagonal
                    ),
                    "diagonal": diagonal,
                    "element_count": 2 * expected_split,
                    "level": int(level),
                    "mask": "all_cells",
                    "node_count": (int(level) + 1) ** 2,
                    "q4_element_count": 0,
                    "s3_area_fraction_percent": 100,
                    "s3_element_count": 2 * expected_split,
                    "selected_base_cells_sha256": control_base_hash,
                    "split_base_cell_count": RESEARCH_CONTROL_SPLIT_COUNT,
                    "split_refined_cell_count": expected_split,
                }
            )
    return {
        "base_grid": BASE_GRID,
        "connectivity_hash_encoding": HASH_ENCODING,
        "diagonal_policies": list(DIAGONALS),
        "levels": list(LEVELS),
        "mask_policies": list(MASKS),
        "records": records,
        "research_control": {
            "classification": "RESEARCH_CONTROL_NOT_A_PRODUCTION_GATE",
            "records": research_control_records,
            "s3_area_fraction_percent": 100,
            "split_base_cell_count": RESEARCH_CONTROL_SPLIT_COUNT,
        },
        "schema": SCHEMA,
        "split_campaign": [
            {
                "s3_area_fraction_percent": count // 4,
                "split_base_cell_count": count,
            }
            for count in SPLIT_COUNTS
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    if (args.output is None) == (args.check is None):
        parser.error("provide exactly one of --output or --check")
    payload = _canonical_bytes(build_manifest())
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
        return 0
    expected = args.check.read_bytes()
    if expected != payload:
        raise SystemExit("mixed-mesh manifest is not canonical or is stale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
