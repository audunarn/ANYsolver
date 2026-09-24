"""Bounded child runner for exploratory high-order F03 spectral reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import psutil
import scipy


MAX_RSS = 8*1024**3
MAX_SECONDS = 300
SOURCES = ("b3_e4_f03_spectral_guarded.py",
           "b3_e4_f03_spectral_axial_reference.py",
           "_b3_e4_f03_segmented_y.py",
           "_b3_e4_f03_independent_beam.py")


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx",type=int,required=True)
    transverse=parser.add_mutually_exclusive_group(required=True)
    transverse.add_argument("--ny",type=int)
    transverse.add_argument("--segmented-degree",type=int)
    parser.add_argument("--beam",type=int,required=True)
    parser.add_argument("--mortar",type=int,required=True)
    parser.add_argument("--root",type=Path,required=True)
    args=parser.parse_args()
    ny=args.ny if args.ny is not None else 3*args.segmented_degree+1
    if not (1<=args.nx<=128 and 1<=ny<=64
            and 1<=args.beam<=512 and 1<=args.mortar<=256):
        parser.error("case exceeds the bounded exploratory envelope")
    if args.segmented_degree is not None and not 1<=args.segmented_degree<=16:
        parser.error("segmented transverse degree exceeds the bounded envelope")
    root=args.root.resolve()
    root.mkdir(parents=True,exist_ok=False)
    source_dir=Path(__file__).resolve().parent
    command=[sys.executable,"-B",str(source_dir/
              "b3_e4_f03_spectral_axial_reference.py"),
             "--nx",str(args.nx),
             "--beam",str(args.beam),"--mortar",str(args.mortar)]
    command.extend(["--ny",str(ny)] if args.segmented_degree is None else
                   ["--segmented-degree",str(args.segmented_degree)])
    environment=os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",
                       MKL_NUM_THREADS="1",NUMBA_NUM_THREADS="1")
    manifest=dict(
        purpose="UNREGISTERED_RESOURCE_BOUNDED_SPECTRAL_F03_DIAGNOSTIC",
        source_revision=subprocess.check_output(["git","rev-parse","HEAD"],
                                                text=True).strip(),
        source_sha256={name:hashlib.sha256((source_dir/name).read_bytes()).hexdigest()
                       for name in SOURCES},
        nx=args.nx,ny=ny,segmented_degree=args.segmented_degree,
        beam=args.beam,mortar=args.mortar,
        command=command,threads=1,sampled_rss_limit_bytes=MAX_RSS,
        wall_limit_seconds=MAX_SECONDS,sampling_seconds=.1,
        python=platform.python_version(),numpy=np.__version__,
        scipy=scipy.__version__,psutil=psutil.__version__,
        limitations=("sampled child RSS is not hard peak or process-tree memory",
                     "classical spectral development reference only",
                     "not native B3-GE/E4-PL or formal F03 qualification"))
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",
                                      encoding="utf-8")
    flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
    process=subprocess.Popen(command,cwd=source_dir.parent,env=environment,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,creationflags=flags)
    observed=psutil.Process(process.pid)
    started=time.monotonic()
    peak=0
    failure=None
    try:
        while process.poll() is None:
            try:
                peak=max(peak,observed.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak>MAX_RSS:
                failure="sampled child RSS exceeded 8 GiB"
                process.terminate()
                break
            if time.monotonic()-started>MAX_SECONDS:
                failure="child exceeded 300 seconds"
                process.terminate()
                break
            time.sleep(.1)
        try:
            stdout,stderr=process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout,stderr=process.communicate()
            failure="child failed to stop within 15 seconds"
    except BaseException as exc:
        if process.poll() is None:
            process.kill()
        stdout,stderr=process.communicate()
        failure=f"supervisor exception: {type(exc).__name__}: {exc}"
    (root/"stdout.json").write_text(stdout,encoding="utf-8")
    (root/"stderr.txt").write_text(stderr,encoding="utf-8")
    status=dict(exit_code=process.returncode,failure=failure,
                sampled_peak_child_rss_bytes=peak,
                elapsed_seconds=time.monotonic()-started)
    if failure is None and process.returncode==0:
        try:
            result=json.loads(stdout)
            if (result["status"]!="UNREGISTERED_SPECTRAL_AXIAL_REFERENCE_DIAGNOSTIC"
                    or (result["shell_modes_x"],result["shell_modes_y"],
                        result["beam_elements"],result["multiplier_intervals"])
                       !=(args.nx,ny,args.beam,args.mortar)):
                raise ValueError("spectral child identity mismatch")
            if args.segmented_degree is not None and (
                    result.get("transverse_basis")!="C0_THREE_INTERVAL_LOBATTO"
                    or result.get("transverse_degree")!=args.segmented_degree):
                raise ValueError("segmented transverse identity mismatch")
            if args.segmented_degree is None and "transverse_basis" in result:
                raise ValueError("unexpected transverse basis identity")
            (root/"result.json").write_text(
                json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            status["status"]="EXPLORATORY_COMPLETE"
        except (ValueError,KeyError,TypeError) as exc:
            status.update(status="EXPLORATORY_FAILURE",
                          failure=f"invalid child result: {exc}")
    else:
        status.update(status="EXPLORATORY_FAILURE",
                      failure=failure or "child exited nonzero")
    (root/"status.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n",
                                    encoding="utf-8")
    print(json.dumps(status,sort_keys=True))
    return 0 if status["status"]=="EXPLORATORY_COMPLETE" else 1


if __name__=="__main__":
    raise SystemExit(main())
