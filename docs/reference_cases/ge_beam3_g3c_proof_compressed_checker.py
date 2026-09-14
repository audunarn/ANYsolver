"""Independent stdlib checker for a proof-compressed G3c aggregate."""
from hashlib import sha256
import json

GRAPHS=("J_B2_PAIR","J_B3_PAIR","J_Q4_PAIR","J_S3_PAIR","J_MULTIFAMILY_LOOP")
VARIANTS=("BASE","SHUFFLED_INSERTION","RENUMBERED","CONNECTIVITY_REVERSED","PROPER_GLOBAL_TRANSFORM")
SCALES=("S0","S1","S2")
MOTIONS=("NONE","CM0","CM1","CM2","CM3")


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
    if type(value)is not dict or set(value)!={"schema","cycle","candidate","manifest_sha256",
            "histories","assignments","counts","passed","terminal","full_g3c_qualified",
            "production_qualified","self_sha256"}:
        raise ValueError("aggregate schema")
    if (value["schema"]!="GE_BEAM3_G3C_PROOF_COMPRESSED_AGGREGATE_V2"
        or value["cycle"] not in (1,2) or type(value["cycle"])is bool
        or value["passed"] is not True or value["full_g3c_qualified"] is not False
        or value["production_qualified"] is not False
        or value["terminal"]!="COMPLETE_GE_BEAM3_G3C_PROOF_COMPRESSED_CYCLE_ONLY"):
        raise ValueError("aggregate identity")
    body={key:item for key,item in value.items() if key!="self_sha256"}
    if value["self_sha256"]!=sha256(canonical(body)).hexdigest():
        raise ValueError("aggregate hash")
    sha(value["manifest_sha256"])
    expected_cases=case_ids(); histories=value["histories"]
    if len(histories)!=375 or [row.get("case_id") for row in histories]!=expected_cases:
        raise ValueError("history coverage")
    executed=set(executed_ids()); history_hashes={}
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
    assignments=value["assignments"]
    if len(assignments)!=3825 or [row.get("assignment_index") for row in assignments]!=list(range(3825)):
        raise ValueError("assignment coverage")
    for row in assignments:
        if type(row)is not dict or set(row)!={"assignment_index","kind","case_id","prefix","provenance",
                "history_record_sha256","executed_restart_sha256","root_case_id","passed","record_sha256"}:
            raise ValueError("assignment schema")
        if row["case_id"] not in history_hashes or row["history_record_sha256"]!=history_hashes[row["case_id"]]:
            raise ValueError("assignment history join")
        if row["provenance"] not in ("EXECUTED","DERIVED_BY_VERIFIED_TRANSPORT") or row["passed"] is not True:
            raise ValueError("assignment provenance")
        check=dict(row);digest=check.pop("record_sha256");sha(digest)
        if digest!=sha256(canonical(check)).hexdigest():raise ValueError("assignment record hash")
    return {"independently_verified":True,"histories":375,"assignments":3825,
            "executed_histories":25,"executed_restart_continuations":120,
            "full_g3c_qualified":False,"production_qualified":False}
