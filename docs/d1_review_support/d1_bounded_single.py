"""Run one development case with explicit elapsed-time and process-tree RSS caps."""

import argparse
import json
from pathlib import Path
import subprocess
import time

import psutil


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--time-limit-seconds", type=float, required=True)
parser.add_argument("--memory-limit-bytes", type=int, required=True)
parser.add_argument("--resource-output", type=Path, required=True)
parser.add_argument("--log", type=Path, required=True)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
if args.command and args.command[0] == "--":
    args.command.pop(0)
if not args.command or args.time_limit_seconds <= 0 or args.memory_limit_bytes <= 0:
    parser.error("provide a command and positive limits")
if args.resource_output.exists() or args.log.exists():
    parser.error("output already exists")

started = time.perf_counter()
peak = 0
status = "completed"
with args.log.open("w", encoding="utf-8") as log:
    child = subprocess.Popen(args.command, stdout=log, stderr=subprocess.STDOUT)
    root = psutil.Process(child.pid)
    while child.poll() is None:
        processes = [root]
        try:
            processes += root.children(recursive=True)
        except psutil.Error:
            pass
        rss = 0
        for process in processes:
            try:
                rss += process.memory_info().rss
            except psutil.Error:
                pass
        peak = max(peak, rss)
        if peak > args.memory_limit_bytes:
            status = "memory_limit_exceeded"
        elif time.perf_counter()-started > args.time_limit_seconds:
            status = "time_limit_exceeded"
        if status != "completed":
            for process in reversed(processes):
                try:
                    process.kill()
                except psutil.Error:
                    pass
            break
        time.sleep(0.05)
    exit_code = child.wait()

record = {
    "status": status,
    "exit_code": exit_code,
    "elapsed_seconds": time.perf_counter()-started,
    "peak_process_tree_memory_mb": peak/1e6,
    "time_limit_seconds": args.time_limit_seconds,
    "memory_limit_bytes": args.memory_limit_bytes,
    "command": args.command,
    "log": str(args.log),
}
args.resource_output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps(record, indent=2))
raise SystemExit(exit_code if status == "completed" else 1)
