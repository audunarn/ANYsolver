"""Pure inventory and evidence checker for the G3c proof-compressed successor.

This module deliberately imports no producer mechanics and no numerical
package.  It reconstructs the registered cross-product and validates truthful
EXECUTED/DERIVED provenance; numerical evidence is supplied by the bounded
producer and remains hash-bound input.
"""
from hashlib import sha256
import json

SCHEMA = "GE_BEAM3_G3C_PROOF_COMPRESSED_V2"
GRAPHS = (
    "J_B2_PAIR", "J_B3_PAIR", "J_Q4_PAIR", "J_S3_PAIR",
    "J_MULTIFAMILY_LOOP",
)
VARIANTS = (
    "BASE", "SHUFFLED_INSERTION", "RENUMBERED",
    "CONNECTIVITY_REVERSED", "PROPER_GLOBAL_TRANSFORM",
)
SCALES = (("S0", 0.01), ("S1", 1.0), ("S2", 10.0))
MOTIONS = ("NONE", "CM0", "CM1", "CM2", "CM3")
EVENTS = {"NONE": 5, "CM0": 9, "CM1": 9, "CM2": 9, "CM3": 9}
PROVENANCE = ("EXECUTED", "DERIVED_BY_VERIFIED_TRANSPORT")
PREREQUISITES = (
    ("accepted_local_25_variant_owner", "224df4c89f592959f66fecff4423cab8da2f5358336bcfc2ee3e6129ec1e56be"),
    ("accepted_corrected_rehearsal", "ab55c23d0591a74cf612b9b7ab19b83d687e3c1ad0523858a8866c35c053e076"),
    ("accepted_rehearsal_review", "47e8876ab262929160ff39231b2a677710a820eb39c3c356b96a1127139d2af2"),
    ("accepted_timing_gate_process", "39cdf5cc930b18fde3d0baf906c7f218589deab4f2c639efb772fc3d298a7384"),
)
SOURCE_HISTORY_INVENTORY_SHA256 = "c8e934143fd896d3d1c072c55819e35f05b8a2b1592c75b2f7207b543cba9fb9"
SOURCE_ASSIGNMENT_INVENTORY_SHA256 = "94fb5e294a802fe6b2515408b680b908330b66578453d2cfe93a35827c5c247e"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return set(actual) == set(expected) and all(
            exact(actual[key], expected[key]) for key in actual)
    if type(actual) is list:
        return len(actual) == len(expected) and all(
            exact(left, right) for left, right in zip(actual, expected))
    return actual == expected


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(
            char not in "0123456789abcdef" for char in value):
        raise ValueError("sha256")
    return value


def cases():
    rows = []
    for graph in GRAPHS:
        for variant in VARIANTS:
            for scale_id, scale in SCALES:
                for motion in MOTIONS:
                    case_id = "::".join((graph, variant, scale_id, motion))
                    rows.append(dict(case_id=case_id, graph=graph,
                                     variant=variant, scale_id=scale_id,
                                     force_scale=scale, common_motion=motion,
                                     accepted_stages=EVENTS[motion]))
    return rows


def executed_case_ids():
    result = []
    for graph in GRAPHS:
        result.extend(f"{graph}::BASE::{scale_id}::NONE"
                      for scale_id, _ in SCALES)
    result.extend(f"{graph}::CONNECTIVITY_REVERSED::S1::CM2"
                  for graph in GRAPHS)
    result.extend(f"{graph}::PROPER_GLOBAL_TRANSFORM::S2::CM3"
                  for graph in GRAPHS)
    return result


def restart_plan():
    by_id = {row["case_id"]: row for row in cases()}
    rows = []
    for case_id in executed_case_ids():
        case = by_id[case_id]
        if case["variant"] == "BASE":
            prefixes = list(range(6))
        else:
            final = case["accepted_stages"]
            prefixes = [0, final // 2, final]
        rows.append(dict(case_id=case_id, prefixes=prefixes))
    if sum(len(row["prefixes"]) for row in rows) != 120:
        raise AssertionError("restart plan count")
    return rows


def derivation_plan():
    executed = set(executed_case_ids())
    rows = []
    for case in cases():
        case_id = case["case_id"]
        if case_id in executed:
            rows.append(dict(case_id=case_id, provenance="EXECUTED",
                             root_case_id=case_id, holdout_case_id=None,
                             transforms=[]))
            continue
        root = f'{case["graph"]}::BASE::{case["scale_id"]}::NONE'
        transforms = []
        if case["variant"] != "BASE":
            transforms.append("NUMBERING::" + case["variant"])
        if case["common_motion"] != "NONE":
            transforms.append("COMMON_MOTION::" + case["common_motion"])
        if not transforms:
            raise AssertionError("nonexecuted identity")
        holdout = None
        if case["variant"] == "CONNECTIVITY_REVERSED" or case["common_motion"] == "CM2":
            holdout = f'{case["graph"]}::CONNECTIVITY_REVERSED::S1::CM2'
        elif case["variant"] == "PROPER_GLOBAL_TRANSFORM" or case["common_motion"] == "CM3":
            holdout = f'{case["graph"]}::PROPER_GLOBAL_TRANSFORM::S2::CM3'
        rows.append(dict(case_id=case_id,
                         provenance="DERIVED_BY_VERIFIED_TRANSPORT",
                         root_case_id=root, holdout_case_id=holdout,
                         transforms=transforms))
    return rows


def assignment_plan():
    result = []
    case_rows = cases()
    for index, case in enumerate(case_rows):
        result.append(dict(assignment_index=index, kind="history",
                           case_id=case["case_id"], prefix=None))
    cursor = len(case_rows)
    for case in case_rows:
        for prefix in range(case["accepted_stages"] + 1):
            result.append(dict(assignment_index=cursor, kind="prefix",
                               case_id=case["case_id"], prefix=prefix))
            cursor += 1
    return result


def manifest():
    body = dict(schema=SCHEMA, version=2, cases=cases(),
                executed_case_ids=executed_case_ids(),
                restart_plan=restart_plan(), derivations=derivation_plan(),
                assignments=assignment_plan(),
                prerequisites=[dict(name=name, sha256=digest)
                               for name, digest in PREREQUISITES],
                source_history_inventory_sha256=SOURCE_HISTORY_INVENTORY_SHA256,
                source_assignment_inventory_sha256=SOURCE_ASSIGNMENT_INVENTORY_SHA256,
                counts=dict(histories=375, executed_histories=25,
                            accepted_events=3075, restart_prefixes=3450,
                            executed_restart_continuations=120,
                            assignments=3825),
                limits=dict(workers=3, threads=1,
                            memory_bytes=24 * 1024**3,
                            child_seconds=600, inactivity_seconds=120,
                            wave_seconds=1800),
                production_qualified=False)
    return dict(body=body, self_sha256=sha256(canonical(body)).hexdigest())


def validate(value):
    """Independent closed validation; returns a detached canonical value."""
    expected = manifest()
    if not exact(value, expected):
        raise ValueError("proof-compressed manifest authority")
    body = value["body"]
    for prerequisite in body["prerequisites"]:
        _sha(prerequisite["sha256"])
    _sha(body["source_history_inventory_sha256"])
    _sha(body["source_assignment_inventory_sha256"])
    case_rows = body["cases"]
    if (len(case_rows) != 375 or len({row["case_id"] for row in case_rows}) != 375
            or sum(row["accepted_stages"] for row in case_rows) != 3075):
        raise ValueError("case coverage")
    assignments = body["assignments"]
    if (len(assignments) != 3825
            or [row["assignment_index"] for row in assignments] != list(range(3825))
            or sum(row["kind"] == "prefix" for row in assignments) != 3450):
        raise ValueError("assignment coverage")
    executed = set(body["executed_case_ids"])
    by_id = {row["case_id"]: row for row in case_rows}
    derivations = body["derivations"]
    if len(derivations) != 375 or [row["case_id"] for row in derivations] != list(by_id):
        raise ValueError("derivation order")
    for row in derivations:
        case = by_id[row["case_id"]]
        if row["provenance"] not in PROVENANCE or row["root_case_id"] not in executed:
            raise ValueError("derivation provenance")
        root = by_id[row["root_case_id"]]
        if root["graph"] != case["graph"] or root["scale_id"] != case["scale_id"]:
            raise ValueError("root association")
        if row["holdout_case_id"] is not None and row["holdout_case_id"] not in executed:
            raise ValueError("holdout association")
    return json.loads(canonical(value))


if __name__ == "__main__":
    print(canonical(validate(manifest())).decode("ascii"), end="")
