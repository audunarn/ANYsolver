"""Compare guarded normalization of one saved checkpoint, without a solve.

Only the named normalization function changes. Full model guards delegate
unchanged. Timing is this saved canonical serialization layer, not checkpoint
creation or a complete coupled route.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time

import anysolver
from anysolver import nonlinear_restart as restart
from scripts.general_contact_d1_interior_press_dev import build_radial_guided_case


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.saved.read_bytes()
    saved = json.loads(raw)
    root = saved["restart_checkpoint"]
    baseline_raw = args.baseline_source.read_bytes()
    tree = ast.parse(baseline_raw)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "_normalize_json")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(args.baseline_source), "exec"),
         restart.__dict__, namespace)
    baseline = namespace["_normalize_json"]
    candidate = restart._normalize_json
    record = dict(status="development_started", scope=__doc__,
                  saved_sha256=hashlib.sha256(raw).hexdigest(),
                  baseline_source_sha256=hashlib.sha256(baseline_raw).hexdigest(),
                  candidate_source_sha256=hashlib.sha256(Path(restart.__file__).read_bytes()).hexdigest(),
                  imported_module=str(Path(anysolver.__file__).resolve()), phases={})

    def save():
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")

    save()
    model, *_ = build_radial_guided_case(target_cells=saved["target_cells"],
        target_y0_m=saved["target_y0_m"], target_right_x_m=saved["target_right_x_m"])
    assert restart.model_configuration_fingerprint(model) == root["model_fingerprint"]
    expected = restart.canonical_checkpoint_json_bytes(root)
    original_guard = restart._EXACT_QUALIFIED_COMPONENT_LIFECYCLE_GUARD
    try:
        for label, function in (("baseline", baseline), ("candidate", candidate)):
            stats = dict(guard_calls=0, guard_seconds=0.0)
            record["phases"][label] = stats
            save()

            def guard(*a, **kw):
                before = time.perf_counter()
                try:
                    return original_guard(*a, **kw)
                finally:
                    stats["guard_calls"] += 1
                    stats["guard_seconds"] += time.perf_counter()-before
                    if stats["guard_calls"] % 100 == 0:
                        save()

            restart._normalize_json = function
            start = time.perf_counter()
            normalized = function(root, _exact_guard=guard, _guard_model=model)
            stats["elapsed_seconds"] = time.perf_counter()-start
            actual = restart.canonical_checkpoint_json_bytes(normalized)
            stats["canonical_sha256"] = hashlib.sha256(actual).hexdigest()
            stats["exact_payload_parity"] = actual == expected
            assert actual == expected
            save()
    finally:
        restart._normalize_json = candidate
    # The actual authority check and original saved fixture are still intact.
    original_guard(model, context="saved normalization probe output")
    assert args.saved.read_bytes() == raw
    record.update(status="development_complete", original_input_unchanged=True)
    save()


if __name__ == "__main__":
    main()
