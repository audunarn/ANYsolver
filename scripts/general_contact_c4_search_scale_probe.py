"""Bounded search-only scaling comparison for planar owner-tree migration."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import psutil

from scripts.general_contact_c4_search_owner_probe import (
    OwnerPatchAABBTree, _historical_tree,
)


def _boxes(grid: int) -> np.ndarray:
    x, y = np.meshgrid(np.arange(grid), np.arange(grid), indexing="xy")
    lower = np.column_stack((x.ravel(), y.ravel())).astype(float)
    return np.column_stack((lower, lower+1.0))


def _measure(tree_type, boxes, windows):
    process = psutil.Process()
    gc.collect()
    before = process.memory_info().rss
    started = time.perf_counter()
    tree = tree_type(boxes)
    built = time.perf_counter()
    after_build = process.memory_info().rss
    responses = tuple(tree.query(window) for window in windows)
    queried = time.perf_counter()
    digest = hashlib.sha256(json.dumps(responses).encode()).hexdigest()
    candidates = sum(map(len, responses))
    del tree
    gc.collect()
    return {
        "build_seconds": built-started,
        "query_seconds": queried-built,
        "rss_before_bytes": before,
        "rss_after_build_bytes": after_build,
        "rss_build_increment_bytes": after_build-before,
        "query_count": len(windows),
        "candidate_count": candidates,
        "responses_sha256": digest,
    }


def main(output_path: Path, grid: int) -> None:
    if output_path.exists():
        raise FileExistsError(output_path)
    boxes = _boxes(grid)
    rng = np.random.default_rng(3011)
    selected = rng.integers(0, len(boxes), size=min(1000, len(boxes)))
    windows = boxes[selected].copy()
    old = _historical_tree()
    rows = {}
    for label, tree_type in (("historical", old),
                             ("owner", OwnerPatchAABBTree)):
        rows[label] = _measure(tree_type, boxes, windows)
    report = {
        "candidate": "c4_patch_search_scale_dev",
        "grid": grid,
        "face_count": len(boxes),
        "results_equal": (rows["historical"]["responses_sha256"]
                          == rows["owner"]["responses_sha256"]),
        "rows": rows,
    }
    output_path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--grid", type=int, choices=(32, 100, 316),
                        required=True)
    args = parser.parse_args()
    main(args.output, args.grid)
