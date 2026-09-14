"""Independent stdlib checker for a proof-compressed G3c aggregate."""
from hashlib import sha256
import json

GRAPHS=("J_B2_PAIR","J_B3_PAIR","J_Q4_PAIR","J_S3_PAIR","J_MULTIFAMILY_LOOP")
VARIANTS=("BASE","SHUFFLED_INSERTION","RENUMBERED","CONNECTIVITY_REVERSED","PROPER_GLOBAL_TRANSFORM")
SCALES=("S0","S1","S2")
MOTIONS=("NONE","CM0","CM1","CM2","CM3")
EVENTS={"NONE":5,"CM0":9,"CM1":9,"CM2":9,"CM3":9}


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=True,allow_nan=False)+"\n").encode("ascii")


def sha(value):
    if type(value)is not str or len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("sha256")


def case_ids():
    return ["::".join((g,v,s,m)) for g in GRAPHS for v in VARIANTS
            for s in SCALES for m in MOTIONS]


def executed_ids():
    roots=[f"{g}::BASE::{s}::NONE" for g in GRAPHS for s in SCALES]
    return roots+[f"{g}::CONNECTIVITY_REVERSED::S1::CM2" for g in GRAPHS]+[
        f"{g}::PROPER_GLOBAL_TRANSFORM::S2::CM3" for g in GRAPHS]


def verify(value):
    if type(value)is not dict or set(value)!={"schema","candidate","manifest_sha256",
            "histories","assignments","counts","passed","terminal","full_g3c_qualified",
            "production_qualified","self_sha256"}:
        raise ValueError("aggregate schema")
    if (value["schema"]!="GE_BEAM3_G3C_PROOF_COMPRESSED_AGGREGATE_V2"
        or value["passed"] is not True or value["full_g3c_qualified"] is not False
        or value["production_qualified"] is not False
        or value["terminal"]!="COMPLETE_GE_BEAM3_G3C_PROOF_COMPRESSED_CYCLE_ONLY"):
        raise ValueError("aggregate identity")
    body={key:item for key,item in value.items() if key!="self_sha256"}
    if value["self_sha256"]!=sha256(canonical(body)).hexdigest():
        raise ValueError("aggregate hash")
    sha(value["manifest_sha256"])
    expected_counts={"histories":375,"executed_histories":25,"accepted_events":3075,
        "restart_prefixes":3450,"executed_restart_continuations":120,"assignments":3825}
    if type(value["counts"])is not dict or value["counts"]!=expected_counts:
        raise ValueError("aggregate counts")
    candidate=value["candidate"]
    if type(candidate)is not dict or set(candidate)!={"commit","tree"}:
        raise ValueError("candidate schema")
    for digest in candidate.values():
        if type(digest)is not str or len(digest)!=40 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("candidate identity")
    expected_cases=case_ids(); histories=value["histories"]
    if len(histories)!=375 or [row.get("case_id") for row in histories]!=expected_cases:
        raise ValueError("history coverage")
    executed=set(executed_ids()); history_hashes={};history_roots={}
    for row in histories:
        if type(row)is not dict or set(row)!={"case_id","provenance","root_case_id","holdout_case_id",
                "transforms","root_history_sha256","root_transport_sha256","executed_history_sha256",
                "passed","record_sha256"} or row["passed"] is not True:
            raise ValueError("history schema")
        parts=row["case_id"].split("::"); root=row["root_case_id"].split("::")
        if len(parts)!=4 or len(root)!=4 or row["root_case_id"] not in executed \
                or parts[0]!=root[0] or parts[2]!=root[2]:
            raise ValueError("root transport association")
        expected_provenance="EXECUTED" if row["case_id"] in executed else "DERIVED_BY_VERIFIED_TRANSPORT"
        if row["provenance"]!=expected_provenance:
            raise ValueError("truthful provenance")
        if row["holdout_case_id"] is not None and row["holdout_case_id"] not in executed:
            raise ValueError("holdout")
        if expected_provenance=="EXECUTED" and (row["transforms"] or row["executed_history_sha256"] is None):
            raise ValueError("executed record")
        if expected_provenance!="EXECUTED" and (not row["transforms"] or row["executed_history_sha256"] is not None):
            raise ValueError("derived record")
        sha(row["root_history_sha256"]);sha(row["root_transport_sha256"])
        if row["executed_history_sha256"] is not None:sha(row["executed_history_sha256"])
        check=dict(row); digest=check.pop("record_sha256");sha(digest)
        if digest!=sha256(canonical(check)).hexdigest():raise ValueError("history record hash")
        history_hashes[row["case_id"]]=digest
        history_roots[row["case_id"]]=row["root_case_id"]
    assignments=value["assignments"]
    if len(assignments)!=3825 or [row.get("assignment_index") for row in assignments]!=list(range(3825)):
        raise ValueError("assignment coverage")
    expected_assignments=[("history",case_id,None) for case_id in expected_cases]
    for case_id in expected_cases:
        motion=case_id.split("::")[3]
        expected_assignments.extend(("prefix",case_id,prefix) for prefix in range(EVENTS[motion]+1))
    restart_keys=set()
    for case_id in executed:
        parts=case_id.split("::")
        prefixes=range(6) if parts[1]=="BASE" else (0,4,9)
        restart_keys.update((case_id,prefix) for prefix in prefixes)
    executed_assignment_count=0
    for row,(expected_kind,expected_case,expected_prefix) in zip(assignments,expected_assignments):
        if type(row)is not dict or set(row)!={"assignment_index","kind","case_id","prefix","provenance",
                "history_record_sha256","executed_restart_sha256","root_case_id","passed","record_sha256"}:
            raise ValueError("assignment schema")
        if row["case_id"] not in history_hashes or row["history_record_sha256"]!=history_hashes[row["case_id"]]:
            raise ValueError("assignment history join")
        if (row["kind"],row["case_id"],row["prefix"])!=(expected_kind,expected_case,expected_prefix):
            raise ValueError("assignment authority")
        should_execute=(expected_kind=="history" and expected_case in executed) or \
            (expected_kind=="prefix" and (expected_case,expected_prefix) in restart_keys)
        expected_provenance="EXECUTED" if should_execute else "DERIVED_BY_VERIFIED_TRANSPORT"
        if (row["provenance"]!=expected_provenance or row["passed"] is not True
            or row["root_case_id"]!=history_roots[row["case_id"]]
            or (row["executed_restart_sha256"] is None)!=(not (expected_kind=="prefix" and should_execute))):
            raise ValueError("assignment provenance")
        if row["executed_restart_sha256"] is not None:sha(row["executed_restart_sha256"])
        executed_assignment_count+=should_execute
        check=dict(row);digest=check.pop("record_sha256");sha(digest)
        if digest!=sha256(canonical(check)).hexdigest():raise ValueError("assignment record hash")
    if executed_assignment_count!=145:raise ValueError("executed assignment count")
    return {"independently_verified":True,"histories":375,"assignments":3825,
            "executed_histories":25,"executed_restart_continuations":120,
            "full_g3c_qualified":False,"production_qualified":False}
