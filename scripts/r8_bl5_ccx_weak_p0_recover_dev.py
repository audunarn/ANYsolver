"""Recover a saved weak-P0 CalculiX run without launching another solve."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"src")]

from scripts import r8_bl5_ccx_weak_p0_dev as specimen
from scripts import r8_bl5_ccx_weak_p0_run_dev as execution


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--saved",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    started=perf_counter()
    result=dict(identity="R8_BL5_CCX_WEAK_P0_SAVED_RECOVERY_DEV_V1",
                status="FAILED",saved=str(args.saved.resolve()),
                source_sha256={"recovery":execution.digest(__file__),
                               "execution":execution.digest(execution.__file__),
                               "specimen":execution.digest(specimen.__file__)})
    try:
        metadata=json.loads((args.saved/"metadata.json").read_text(encoding="utf-8"))
        receipt=json.loads((args.saved/"ccx.receipt.json").read_text(encoding="utf-8"))
        case=metadata["case"]
        expected,rebuilt=specimen.deck(case)
        if (receipt["status"]!="EXITED" or receipt["exit_code"]!=0 or
                receipt["executable_sha256"]!=execution.EXPECTED_CCX_SHA256 or
                (args.saved/"weak.inp").read_bytes()!=expected or
                metadata!=json.loads(json.dumps(rebuilt,allow_nan=False)) or
                receipt["case"]!=case or
                "     1          1     1     1  0.100000E+01" not in
                    (args.saved/"weak.sta").read_text(encoding="utf-8")):
            raise ValueError("saved complete accepted run or exact deck identity required")
        result["case"]=case
        result["saved_sha256"]={name:execution.digest(args.saved/name) for name in
            ("weak.inp","metadata.json","ccx.receipt.json","weak.frd","weak.sta",
             "ccx.stdout.txt","ccx.stderr.txt")}
        result.update(execution.compare(args.saved,metadata))
    except Exception as exc:
        result.update(status="FAILED",error=repr(exc))
    result["process_wall_seconds"]=perf_counter()-started
    (args.output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({name:result.get(name) for name in ("status","case",
        "ccx_displacement_relative_to_independent_same_law","error")}))
    if result["status"]!="DEVELOPMENT_COMPARISON_NOT_QUALIFIED":
        raise SystemExit(1)


if __name__=="__main__":
    main()
