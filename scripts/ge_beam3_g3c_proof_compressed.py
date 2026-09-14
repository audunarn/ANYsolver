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


def _candidate(value):
    if type(value) is not dict or set(value) != {"commit", "tree"}:
        raise ValueError("candidate schema")
    for digest in value.values():
        if type(digest) is not str or len(digest) != 40 or any(
                char not in "0123456789abcdef" for char in digest):
            raise ValueError("candidate identity")
    return value


def aggregate(execution):
    """Create assignment-neutral evidence from a completed executed basis.

    The numerical coordinator supplies the execution object.  This function
    neither runs nor imports mechanics and cannot turn an absent result into an
    executed claim.
    """
    if type(execution) is not dict or set(execution) != {
            "schema", "cycle", "candidate", "manifest_sha256",
            "histories", "restarts", "prerequisite_receipts"}:
        raise ValueError("execution schema")
    if execution["schema"] != "GE_BEAM3_G3C_PROOF_COMPRESSED_EXECUTION_V2":
        raise ValueError("execution identity")
    if type(execution["cycle"]) is not int or type(execution["cycle"]) is bool \
            or execution["cycle"] not in (1, 2):
        raise ValueError("cycle")
    candidate = _candidate(execution["candidate"])
    manifest_value = manifest()
    if execution["manifest_sha256"] != sha256(canonical(manifest_value)).hexdigest():
        raise ValueError("manifest association")
    receipts = execution["prerequisite_receipts"]
    if type(receipts) is not list or len(receipts) != len(PREREQUISITES):
        raise ValueError("prerequisite receipt coverage")
    for actual, (name, digest) in zip(receipts, PREREQUISITES):
        if not exact(actual, {"name": name, "sha256": digest}):
            raise ValueError("prerequisite receipt")

    expected_ids = executed_case_ids()
    histories = execution["histories"]
    if type(histories) is not list or len(histories) != 25:
        raise ValueError("executed history coverage")
    history_by_id = {}
    for expected_id, row in zip(expected_ids, histories):
        if type(row) is not dict or set(row) != {
                "case_id", "events", "history_sha256", "final_sha256",
                "transport_sha256", "passed"}:
            raise ValueError("executed history schema")
        if row["case_id"] != expected_id or row["passed"] is not True:
            raise ValueError("executed history order")
        case = next(item for item in cases() if item["case_id"] == expected_id)
        if type(row["events"]) is not int or row["events"] != case["accepted_stages"]:
            raise ValueError("executed history events")
        for key in ("history_sha256", "final_sha256", "transport_sha256"):
            _sha(row[key])
        history_by_id[expected_id] = row

    expected_restarts = [(row["case_id"], prefix)
                         for row in restart_plan() for prefix in row["prefixes"]]
    restarts = execution["restarts"]
    if type(restarts) is not list or len(restarts) != 120:
        raise ValueError("executed restart coverage")
    restart_by_key = {}
    for expected_key, row in zip(expected_restarts, restarts):
        if type(row) is not dict or set(row) != {
                "case_id", "prefix", "input_sha256", "final_sha256", "passed"}:
            raise ValueError("executed restart schema")
        key = (row["case_id"], row["prefix"])
        if key != expected_key or row["passed"] is not True or key in restart_by_key:
            raise ValueError("executed restart order")
        if type(row["prefix"]) is not int or type(row["prefix"]) is bool:
            raise ValueError("executed restart prefix")
        _sha(row["input_sha256"]); _sha(row["final_sha256"])
        if row["final_sha256"] != history_by_id[row["case_id"]]["final_sha256"]:
            raise ValueError("restart final association")
        restart_by_key[key] = row

    derivation_by_id = {row["case_id"]: row for row in derivation_plan()}
    history_records = []
    for case in cases():
        derivation = derivation_by_id[case["case_id"]]
        root = history_by_id[derivation["root_case_id"]]
        executed_row = history_by_id.get(case["case_id"])
        body = dict(case_id=case["case_id"], provenance=derivation["provenance"],
                    root_case_id=derivation["root_case_id"],
                    holdout_case_id=derivation["holdout_case_id"],
                    transforms=derivation["transforms"],
                    root_history_sha256=root["history_sha256"],
                    root_transport_sha256=root["transport_sha256"],
                    executed_history_sha256=(None if executed_row is None
                                             else executed_row["history_sha256"]),
                    passed=True)
        body["record_sha256"] = sha256(canonical(body)).hexdigest()
        history_records.append(body)

    assignment_records = []
    for assignment in assignment_plan():
        case_id = assignment["case_id"]
        derivation = derivation_by_id[case_id]
        restart = restart_by_key.get((case_id, assignment["prefix"]))
        provenance = "EXECUTED" if (assignment["kind"] == "history"
            and case_id in history_by_id) or restart is not None else \
            "DERIVED_BY_VERIFIED_TRANSPORT"
        body = dict(assignment_index=assignment["assignment_index"],
                    kind=assignment["kind"], case_id=case_id,
                    prefix=assignment["prefix"], provenance=provenance,
                    history_record_sha256=history_records[
                        next(index for index, row in enumerate(cases())
                             if row["case_id"] == case_id)]["record_sha256"],
                    executed_restart_sha256=(None if restart is None else
                        sha256(canonical(restart)).hexdigest()),
                    root_case_id=derivation["root_case_id"], passed=True)
        body["record_sha256"] = sha256(canonical(body)).hexdigest()
        assignment_records.append(body)

    value = dict(schema="GE_BEAM3_G3C_PROOF_COMPRESSED_AGGREGATE_V2",
                 cycle=execution["cycle"], candidate=candidate,
                 manifest_sha256=execution["manifest_sha256"],
                 histories=history_records, assignments=assignment_records,
                 counts=manifest_value["body"]["counts"], passed=True,
                 terminal="COMPLETE_GE_BEAM3_G3C_PROOF_COMPRESSED_CYCLE_ONLY",
                 full_g3c_qualified=False, production_qualified=False)
    value["self_sha256"] = sha256(canonical(value)).hexdigest()
    return value


if __name__ == "__main__":
    print(canonical(validate(manifest())).decode("ascii"), end="")
