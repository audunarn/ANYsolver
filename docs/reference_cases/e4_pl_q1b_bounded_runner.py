"""Bounded parallel coordinator for the research-only Q1B campaign."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Sequence

import e4_pl_q1b_common as common


RUNNER_ID = "Q1B_BOUNDED_COORDINATOR"


@dataclass(frozen=True)
class ChildResult:
    name: str
    returncode: int
    elapsed_seconds: float
    timed_out: bool
    memory_exceeded: bool


def _memory_bytes(pid: int) -> int:
    if os.name != "nt":
        try:
            return int(Path(f"/proc/{pid}/status").read_text().split("VmRSS:",1)[1].splitlines()[0].strip().split()[0])*1024
        except (OSError,IndexError,ValueError):
            return 0
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_ulong),("PageFaultCount",ctypes.c_ulong),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
    counters=Counters(); counters.cb=ctypes.sizeof(counters)
    handle=ctypes.windll.kernel32.OpenProcess(0x0410,False,pid)
    if not handle: return 0
    try: return int(counters.WorkingSetSize) if ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb) else 0
    finally: ctypes.windll.kernel32.CloseHandle(handle)


def _terminate_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None: return
    if os.name=="nt":
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,check=False,timeout=30)
    else:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired: process.kill()


def run_wave(commands: list[tuple[str,list[str],Path]], *, timeout_seconds: int, memory_limit_gib: int) -> list[ChildResult]:
    if timeout_seconds<1 or timeout_seconds>600 or memory_limit_gib<1 or memory_limit_gib>24: raise common.Q1BError("child bounds exceed preregistration")
    active=[]; environment=common.one_thread_environment(); limit=memory_limit_gib*(1<<30)
    for name,command,directory in commands:
        directory.mkdir(parents=True,exist_ok=False)
        stdout=(directory/"stdout.log").open("wb"); stderr=(directory/"stderr.log").open("wb")
        process=subprocess.Popen(command,cwd=directory,env=environment,stdout=stdout,stderr=stderr,start_new_session=os.name!="nt")
        active.append((name,process,time.monotonic(),stdout,stderr))
    results=[]
    while active:
        remaining=[]
        for name,process,started,stdout,stderr in active:
            elapsed=time.monotonic()-started; timed_out=elapsed>timeout_seconds; memory_exceeded=_memory_bytes(process.pid)>limit
            if process.poll() is None and not (timed_out or memory_exceeded): remaining.append((name,process,started,stdout,stderr)); continue
            if timed_out or memory_exceeded: _terminate_tree(process)
            stdout.close(); stderr.close()
            returncode=process.returncode if process.returncode is not None else -9
            if returncode or timed_out or memory_exceeded:
                for canonical_name in ("record.json","check.json","cycle.json"):
                    (Path(stdout.name).parent/canonical_name).unlink(missing_ok=True)
            results.append(ChildResult(name,returncode,elapsed,timed_out,memory_exceeded))
        active=remaining
        if active: time.sleep(.05)
    return sorted(results,key=lambda row:row.name)


def validate_authority(repository_root: Path, contract_path: Path, contract_sha256: str, authority_path: Path, authority_sha256: str) -> tuple[dict[str,Any],dict[str,Any]]:
    return common.validate_execution_authority(repository_root=repository_root,contract_path=contract_path,contract_sha256=contract_sha256,authority_path=authority_path,authority_sha256=authority_sha256,runner_id=RUNNER_ID)


def _command(repository_root: Path, script: str, *args: str) -> list[str]:
    return [sys.executable,str(repository_root/"docs/reference_cases"/script),*args]


def run_cycle(*, repository_root: Path, contract_path: Path, contract_sha256: str, authority_path: Path, authority_sha256: str, q1y3_evidence_root: Path, output_root: Path, cycle: int, timeout_seconds: int, memory_limit_gib: int) -> dict[str,Any]:
    contract,_=validate_authority(repository_root,contract_path,contract_sha256,authority_path,authority_sha256)
    if cycle not in (1,2) or output_root.exists() or q1y3_evidence_root is None: raise common.Q1BError("cycle, evidence root, or exclusive output root invalid")
    output_root.mkdir(parents=True,exist_ok=False)
    # Re-enforce the frozen exact-equivalence commissioning gate after all
    # execution-authority checks and before any registered shard mechanics.
    commissioning_directory=output_root/"commissioning"
    commissioning_output=commissioning_directory/"record.json"
    commissioning_results=run_wave(
        [("EXACT_EQUIVALENCE_COMMISSIONING",_command(
            repository_root,"e4_pl_q1b_assembled_producer.py","--commission",
            "--repository-root",str(repository_root),"--q1y3-evidence-root",
            str(q1y3_evidence_root),"--output",str(commissioning_output),
        ),commissioning_directory)],
        timeout_seconds=timeout_seconds,memory_limit_gib=memory_limit_gib,
    )
    blocked=any(row.returncode or row.timed_out or row.memory_exceeded for row in commissioning_results)
    if not blocked:
        _,commissioning=common.read_json(commissioning_output)
        blocked=commissioning.get("schema")!="anysolver.s4.e4-pl-q1b-equivalence-commissioning-v1" or commissioning.get("all_equivalent") is not True
    producer_commands=[]
    for shard in common.SHARDS:
        directory=output_root/f"producer-{shard.lower()}"; output=directory/"record.json"
        producer_commands.append((shard,_command(repository_root,"e4_pl_q1b_assembled_producer.py","--run-shard","--repository-root",str(repository_root),"--shard",shard,"--cycle",str(cycle),"--contract",str(contract_path),"--contract-sha256",contract_sha256,"--authority",str(authority_path),"--authority-sha256",authority_sha256,"--output",str(output)),directory))
    producer_results=run_wave(producer_commands,timeout_seconds=timeout_seconds,memory_limit_gib=memory_limit_gib) if not blocked else []
    blocked|=any(row.returncode or row.timed_out or row.memory_exceeded for row in producer_results)
    checker_results=[]
    if not blocked:
        for replica in (1,2):
            commands=[]
            for shard in common.SHARDS:
                record=output_root/f"producer-{shard.lower()}"/"record.json"; directory=output_root/f"checker{replica}-{shard.lower()}"; output=directory/"check.json"
                commands.append((shard,_command(repository_root,"e4_pl_q1b_assembled_checker.py","--check-shard","--repository-root",str(repository_root),"--contract",str(contract_path),"--contract-sha256",contract_sha256,"--authority",str(authority_path),"--authority-sha256",authority_sha256,"--record",str(record),"--output",str(output)),directory))
            wave=run_wave(commands,timeout_seconds=timeout_seconds,memory_limit_gib=memory_limit_gib); checker_results.extend((replica,row) for row in wave); blocked|=any(row.returncode or row.timed_out or row.memory_exceeded for row in wave)
    shards=[]; diagnostic_hashes=[]; stability_no_go=locking_no_go=nonintrusion_no_go=False; unresolved=False
    if not blocked:
        for shard in common.SHARDS:
            producer_path=output_root/f"producer-{shard.lower()}"/"record.json"; raw,record=common.read_json(producer_path)
            checks=[]
            for replica in (1,2):
                check_raw,check=common.read_json(output_root/f"checker{replica}-{shard.lower()}"/"check.json"); checks.append((check_raw,check))
            if checks[0][0]!=checks[1][0] or checks[0][1]["disagreements"]: blocked=True
            contradictions=checks[0][1]["contradictions"]
            stability_no_go|=shard==common.SHARDS[0] and bool(contradictions)
            locking_no_go|=shard==common.SHARDS[1] and bool(contradictions)
            nonintrusion_no_go|=shard==common.SHARDS[2] and bool(contradictions)
            if shard==common.SHARDS[0]: unresolved=record["coverage"]["domain_certificate"]["status"]!="CERTIFIED"
            shards.append({"contradictions":contradictions,"coverage":record["coverage"],"disagreements":checks[0][1]["disagreements"],"shard":shard})
            diagnostic_hashes.append({"check_sha256":common.sha256(checks[0][0]),"producer_sha256":common.sha256(raw),"shard":shard})
    terminal=common.choose_terminal(blocked=blocked,stability_no_go=stability_no_go,locking_no_go=locking_no_go,nonintrusion_no_go=nonintrusion_no_go,unresolved=unresolved)
    common_payload={"candidate_id":common.CANDIDATE_ID,"coverage":{"checker_replicas_per_shard":2,"producer_shards":len(common.SHARDS)},"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","shards":shards,"study_id":common.STUDY_ID,"terminal":terminal}
    aggregate={"candidate_id":common.CANDIDATE_ID,"common_payload":common_payload,"common_payload_sha256":common.sha256(common.canonical_bytes(common_payload)),"contract_sha256":contract_sha256.upper(),"cycle":cycle,"diagnostic_hashes":diagnostic_hashes,"schema":common.CYCLE_SCHEMA,"study_id":common.STUDY_ID}
    common.write_exclusive(output_root/"cycle.json",aggregate); return aggregate


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(); parser.add_argument("--repository-root",type=Path,required=True); parser.add_argument("--contract",type=Path,required=True); parser.add_argument("--contract-sha256",required=True); parser.add_argument("--authority",type=Path,required=True); parser.add_argument("--authority-sha256",required=True)
    group=parser.add_mutually_exclusive_group(required=True); group.add_argument("--authority-check-only",action="store_true"); group.add_argument("--run-cycle",action="store_true")
    parser.add_argument("--q1y3-evidence-root",type=Path); parser.add_argument("--output-root",type=Path); parser.add_argument("--cycle",type=int); parser.add_argument("--workers",type=int,default=3); parser.add_argument("--timeout-seconds",type=int,default=600); parser.add_argument("--memory-limit-gib",type=int,default=24); return parser


def main(argv: Sequence[str]|None=None) -> int:
    args=_parser().parse_args(argv)
    try:
        if args.workers!=3: raise common.Q1BError("Q1B requires exactly three producer workers")
        if args.authority_check_only:
            validate_authority(args.repository_root,args.contract,args.contract_sha256,args.authority,args.authority_sha256); print(common.canonical_bytes({"runner_id":RUNNER_ID,"status":"PASS"}).decode(),end=""); return 0
        run_cycle(repository_root=args.repository_root,contract_path=args.contract,contract_sha256=args.contract_sha256,authority_path=args.authority,authority_sha256=args.authority_sha256,q1y3_evidence_root=args.q1y3_evidence_root,output_root=args.output_root,cycle=args.cycle,timeout_seconds=args.timeout_seconds,memory_limit_gib=args.memory_limit_gib); return 0
    except (OSError,ValueError,common.Q1BError) as exc: print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
