"""Parallel bounded coordinator for Q1D precision closure."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
from decimal import Decimal, getcontext
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Sequence

import e4_pl_q1b_common as common


STUDY_ID="study_e4_pl_q1d.q1c_ultrathin_conditioning_closure_v1"
CANDIDATE_ID="candidate_e4_pl_q1d.wg2020_ultrathin_block_precision_v1"
CONTRACT_SCHEMA="anysolver.s4.e4-pl-q1d-contract-v1"
CYCLE_SCHEMA="anysolver.s4.e4-pl-q1d-bounded-cycle-v1"
SHARDS=("FULL_BLOCK_LDL","DRILL_SCHUR","ULTRATHIN_REFINEMENT")
TERMINALS=("BLOCKED_E4_PL_Q1D_PROOF_OR_REVIEW","NO_GO_E4_PL_Q1D_ULTRATHIN_LOCKING","NO_GO_E4_PL_Q1D_SOLVER_EQUIVALENCE","UNCLASSIFIED_E4_PL_Q1D_PRECISION","UNCLASSIFIED_E4_PL_Q1D_ULTRATHIN_CONDITIONING_CLOSED_ONLY")


@dataclass(frozen=True)
class ChildResult:
    name: str
    returncode: int
    timed_out: bool
    memory_exceeded: bool


def _memory_bytes(pid: int) -> int:
    if os.name!="nt":
        try: return int(Path(f"/proc/{pid}/status").read_text().split("VmRSS:",1)[1].splitlines()[0].strip().split()[0])*1024
        except (OSError,IndexError,ValueError): return 0
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_ulong),("PageFaultCount",ctypes.c_ulong),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
    counters=Counters(); counters.cb=ctypes.sizeof(counters); handle=ctypes.windll.kernel32.OpenProcess(0x0410,False,pid)
    if not handle: return 0
    try: return int(counters.WorkingSetSize) if ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb) else 0
    finally: ctypes.windll.kernel32.CloseHandle(handle)


def _terminate_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None: return
    if os.name=="nt": subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,check=False,timeout=30)
    else:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired: process.kill()


def _environment(repository_root: Path, environment_root: Path) -> dict[str,str]:
    value=os.environ.copy(); value["PYTHONPATH"]=os.pathsep.join((str(repository_root/"docs/reference_cases"),str(environment_root)))
    for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"): value[name]="1"
    return value


def run_wave(commands: list[tuple[str,list[str],Path,str]], *, repository_root: Path, environment_root: Path, timeout_seconds: int, memory_limit_gib: int) -> list[ChildResult]:
    if not 1<=timeout_seconds<=120 or not 1<=memory_limit_gib<=8: raise common.Q1BError("Q1D child bounds exceed contract")
    active=[]; environment=_environment(repository_root,environment_root); limit=memory_limit_gib*(1<<30)
    for name,command,directory,canonical_name in commands:
        directory.mkdir(parents=True,exist_ok=False); stdout=(directory/"stdout.log").open("wb"); stderr=(directory/"stderr.log").open("wb"); process=subprocess.Popen(command,cwd=directory,env=environment,stdout=stdout,stderr=stderr,start_new_session=os.name!="nt"); active.append((name,process,time.monotonic(),stdout,stderr,directory/canonical_name))
    results=[]
    while active:
        remaining=[]
        for name,process,started,stdout,stderr,canonical in active:
            timed_out=time.monotonic()-started>timeout_seconds; memory_exceeded=_memory_bytes(process.pid)>limit
            if process.poll() is None and not (timed_out or memory_exceeded): remaining.append((name,process,started,stdout,stderr,canonical)); continue
            if timed_out or memory_exceeded: _terminate_tree(process)
            stdout.close(); stderr.close(); returncode=process.returncode if process.returncode is not None else -9
            if returncode or timed_out or memory_exceeded: canonical.unlink(missing_ok=True)
            results.append(ChildResult(name,returncode,timed_out,memory_exceeded))
        active=remaining
        if active: time.sleep(.05)
    return sorted(results,key=lambda row:row.name)


def _verify_environment(root: Path, record: dict[str,Any]) -> None:
    if root.is_symlink() or not root.is_dir() or record.get("schema")!="e4_pl_q1t_environment_record_v1" or record.get("extracted_file_count")!=1662: raise common.Q1BError("Q1D exact environment identity mismatch")
    expected=record.get("extracted_file_hash_graph"); actual=[]
    for directory,directory_names,file_names in os.walk(root,topdown=True,followlinks=False):
        current=Path(directory)
        if current.is_symlink() or any((current/name).is_symlink() for name in directory_names): raise common.Q1BError("linked directory in Q1D environment")
        for name in file_names:
            path=current/name
            if path.is_symlink() or not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode): raise common.Q1BError("nonregular file in Q1D environment")
            raw=path.read_bytes(); actual.append({"bytes":len(raw),"path":path.relative_to(root).as_posix(),"sha256":hashlib.sha256(raw).hexdigest().lower()})
    actual.sort(key=lambda row:row["path"])
    if actual!=expected: raise common.Q1BError("Q1D exact environment graph mismatch")


def validate_contract(repository_root: Path, contract_path: Path, contract_sha256: str, environment_root: Path) -> dict[str,Any]:
    expected=(repository_root/"docs/reference_cases/e4_pl_q1d_contract.json").resolve()
    if contract_path.resolve()!=expected: raise common.Q1BError("Q1D contract path mismatch")
    raw,contract=common.read_json(expected)
    if common.sha256(raw)!=contract_sha256.upper() or contract.get("schema")!=CONTRACT_SCHEMA or contract.get("candidate_id")!=CANDIDATE_ID or contract.get("study_id")!=STUDY_ID or contract.get("shards")!=list(SHARDS) or contract.get("terminals")!=list(TERMINALS): raise common.Q1BError("Q1D contract identity mismatch")
    if contract.get("runtime")!={"automatic_retry":False,"checker_replicas":2,"memory_limit_gib":8,"numerical_threads":1,"precision_bits":[128,192,256],"timeout_seconds":120,"workers":3}: raise common.Q1BError("Q1D runtime mismatch")
    if contract.get("base_commit")!="22c57838f64205716d5e9272328acc9d0f06289e": raise common.Q1BError("Q1D base mismatch")
    for row in (contract["q1c_authority"]["contract"],contract["q1c_authority"]["result"],contract["environment"]): common.verify_file(repository_root/row["path"],bytes_count=row["bytes"],digest=row["sha256"])
    _,environment=common.read_json(repository_root/contract["environment"]["path"]); _verify_environment(environment_root.resolve(),environment)
    ancestry=subprocess.run(["git","merge-base","--is-ancestor",contract["base_commit"],"HEAD"],cwd=repository_root,capture_output=True,check=False)
    if ancestry.returncode: raise common.Q1BError("Q1D base is not an ancestor")
    return contract


def _command(repository_root: Path, script: str, *args: str) -> list[str]: return [sys.executable,str(repository_root/"docs/reference_cases"/script),*args]


def choose_terminal(*,blocked: bool,locking: bool,equivalence: bool,precision: bool) -> str:
    if blocked:return TERMINALS[0]
    if locking:return TERMINALS[1]
    if equivalence:return TERMINALS[2]
    if precision:return TERMINALS[3]
    return TERMINALS[4]


def run_cycle(*,repository_root: Path,contract_path: Path,contract_sha256: str,environment_root: Path,output_root: Path,workers: int,timeout_seconds: int,memory_limit_gib: int) -> dict[str,Any]:
    validate_contract(repository_root,contract_path,contract_sha256,environment_root)
    if workers!=3 or output_root.exists(): raise common.Q1BError("Q1D workers or exclusive output root mismatch")
    output_root.mkdir(parents=True,exist_ok=False); commands=[]
    for shard in SHARDS:
        directory=output_root/f"producer-{shard.lower()}"; commands.append((shard,_command(repository_root,"e4_pl_q1d_precision_producer.py","--emit-precision-proof","--shard",shard,"--output",str(directory/"proof.json")),directory,"proof.json"))
    producer_results=run_wave(commands,repository_root=repository_root,environment_root=environment_root,timeout_seconds=timeout_seconds,memory_limit_gib=memory_limit_gib); blocked=any(row.returncode or row.timed_out or row.memory_exceeded for row in producer_results); checker_results=[]
    if not blocked:
        commands=[]
        for shard in SHARDS:
            proof=output_root/f"producer-{shard.lower()}"/"proof.json"
            for replica in (1,2):
                directory=output_root/f"checker{replica}-{shard.lower()}"; commands.append((f"{shard}:{replica}",_command(repository_root,"e4_pl_q1d_precision_checker.py","--verify-precision-proof","--proof",str(proof),"--output",str(directory/"check.json")),directory,"check.json"))
        checker_results=run_wave(commands,repository_root=repository_root,environment_root=environment_root,timeout_seconds=timeout_seconds,memory_limit_gib=memory_limit_gib); blocked=any(row.returncode or row.timed_out or row.memory_exceeded for row in checker_results)
    shards=[]; diagnostic_hashes=[]; locking=equivalence=precision=False; full_ratio=schur_ratio=None
    if not blocked:
        getcontext().prec=100
        for shard in SHARDS:
            proof_path=output_root/f"producer-{shard.lower()}"/"proof.json"; proof_raw,proof=common.read_json(proof_path); checks=[common.read_json(output_root/f"checker{replica}-{shard.lower()}"/"check.json") for replica in (1,2)]
            if checks[0][0]!=checks[1][0] or checks[0][1]["disagreements"]: blocked=True
            check=checks[0][1]; contradictions=check["contradictions"]; locking|=bool(contradictions) and shard in (SHARDS[0],SHARDS[2]); equivalence|=bool(contradictions) and shard==SHARDS[1]; precision|=bool(check["precision_unresolved"])
            if shard==SHARDS[0]: full_ratio=Decimal(proof["payload"]["rows"][-1]["response_ratio_eb"])
            if shard==SHARDS[1]: schur_ratio=Decimal(proof["payload"]["rows"][-1]["response_ratio_eb"])
            shards.append({"classification_facts":check["classification_facts"],"contradictions":contradictions,"disagreements":check["disagreements"],"precision_unresolved":check["precision_unresolved"],"shard":shard}); diagnostic_hashes.append({"check_sha256":common.sha256(checks[0][0]),"proof_sha256":common.sha256(proof_raw),"shard":shard})
        if full_ratio is None or schur_ratio is None or abs(full_ratio-schur_ratio)>Decimal("1e-18"): equivalence=True
    terminal=choose_terminal(blocked=blocked,locking=locking,equivalence=equivalence,precision=precision); common_payload={"candidate_id":CANDIDATE_ID,"coverage":{"checker_replicas":2,"completed_shards":len(shards),"producer_shards":3},"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","shards":shards,"study_id":STUDY_ID,"terminal":terminal}; aggregate={"candidate_id":CANDIDATE_ID,"common_payload":common_payload,"common_payload_sha256":common.sha256(common.canonical_bytes(common_payload)),"contract_sha256":contract_sha256.upper(),"diagnostic_hashes":diagnostic_hashes,"schema":CYCLE_SCHEMA,"study_id":STUDY_ID}; common.write_exclusive(output_root/"aggregate.json",aggregate); return aggregate


def main(argv: Sequence[str]|None=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--run-bounded",action="store_true",required=True); parser.add_argument("--repository-root",type=Path,required=True); parser.add_argument("--contract",type=Path,required=True); parser.add_argument("--contract-sha256",required=True); parser.add_argument("--environment-root",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--workers",type=int,default=3); parser.add_argument("--timeout-seconds",type=int,default=120); parser.add_argument("--memory-limit-gib",type=int,default=8); args=parser.parse_args(argv)
    try: run_cycle(repository_root=args.repository_root.resolve(),contract_path=args.contract,contract_sha256=args.contract_sha256,environment_root=args.environment_root,output_root=args.output_root,workers=args.workers,timeout_seconds=args.timeout_seconds,memory_limit_gib=args.memory_limit_gib); return 0
    except (OSError,ValueError,common.Q1BError) as exc: print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
