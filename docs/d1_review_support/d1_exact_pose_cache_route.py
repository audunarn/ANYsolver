"""Historical route probe; requires the retained temporary cache patch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
import scipy

from anysolver.general_contact.s3_patch_augmented import MovingS3PatchProjectedNormal
from scripts.general_contact_d1_profile_coupled import main as run_route


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disable-cache", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    source = Path(__file__).resolve().parents[2].joinpath(
        "src/anysolver/general_contact/s3_patch_augmented.py")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha != "020939ccea9f29d7e5aa9ea85a935759cc037192d795f1261025f9a1dbfc2b14":
        raise RuntimeError("historical exact-pose cache candidate source is not installed")
    if args.disable_cache:
        original = MovingS3PatchProjectedNormal._nodal_force_unresolved

        def uncached(self, *call_args, **call_kwargs):
            self._nodal_geometry_cache = None
            return original(self, *call_args, **call_kwargs)

        MovingS3PatchProjectedNormal._nodal_force_unresolved = uncached
    try:
        run_route(args.output, candidate_rows=1, candidate_columns=8,
                  monolithic_route=True, omit_checkpoint=False)
    finally:
        if args.output.exists():
            record = json.loads(args.output.read_text(encoding="utf-8"))
            record["exact_pose_float_cache_enabled"] = not args.disable_cache
            record["source_commit"] = subprocess.check_output(
                ("git", "rev-parse", "HEAD"), text=True).strip()
            record["candidate_source_sha256"] = source_sha
            record["probe_sha256"] = hashlib.sha256(
                Path(__file__).read_bytes()).hexdigest()
            record["runtime_identity"] = {
                "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__,
            }
            args.output.write_text(json.dumps(record, indent=2)+"\n",
                                   encoding="utf-8")


if __name__ == "__main__":
    main()
