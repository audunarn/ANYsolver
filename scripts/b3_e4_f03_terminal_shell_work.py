"""Bounded native/independent shell work under matched terminal wrenches.

The square patch is x=[.9,1], y=[-.05,.05]. A distributing director
couple and a rigid-corner force couple have the same physical resultant,
but intentionally different local work functionals. This diagnostic does
not select either connection or qualify shell/beam accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import spsolve
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_strip_pose_candidate import reference_spatial_trace_strip
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_independent_terminal_six_channel import Model, PATCH


def native_force(panel, law: str, loading: str) -> np.ndarray:
    count = 6*panel.node_count
    f = np.zeros(count)
    if law == "distributing":
        trace = reference_spatial_trace_strip(
            panel, .95, half_length=.05, half_width=.05)
        return (100.*trace[3] if loading == "tip_mx" else
                1000.*trace[2] if loading == "tip_fz" else
                _invalid_load(loading))
    if law != "rigid" or loading not in ("tip_mx", "tip_fz"):
        raise ValueError("rigid/distributing and tip_mx/tip_fz required")
    for x, y in PATCH:
        nodes, weights = panel._shape(x, y)
        amplitude = 100.*y/.01 if loading == "tip_mx" else 250.
        for node, weight in zip(nodes, weights):
            f[6*node+2] += amplitude*weight
    return f


def _invalid_load(value: str):
    raise ValueError(f"unsupported shell-only load {value}")


def independent_force(model: Model, law: str, loading: str) -> np.ndarray:
    n = model.offsets[2]
    if law == "distributing":
        trace = model.shell_patch_pose()
        return (100.*trace[3, :n] if loading == "tip_mx" else
                1000.*trace[2, :n] if loading == "tip_fz" else
                _invalid_load(loading))
    if law != "rigid" or loading not in ("tip_mx", "tip_fz"):
        raise ValueError("rigid/distributing and tip_mx/tip_fz required")
    f = np.zeros(n)
    for x, y in PATCH:
        amplitude = 100.*y/.01 if loading == "tip_mx" else 250.
        f += amplitude*model.shell_translation(x, y)[2, :n]
    return f


def native_wrench(panel, f: np.ndarray) -> np.ndarray:
    q = f.reshape(-1, 6)
    xyz = reference_nodes(panel)
    return np.r_[q[:, :3].sum(axis=0),
                 (np.cross(xyz, q[:, :3])+q[:, 3:]).sum(axis=0)]


def response(k, f: np.ndarray, free: np.ndarray, *, physical=None) -> dict:
    q = np.zeros(len(f))
    block = k[free, :][:, free]
    q[free] = (spsolve(block.tocsc(), f[free]) if hasattr(block, "tocsc") else
               linalg.solve(block, f[free], assume_a="gen"))
    residual = np.asarray(k@q-f)
    work = float(f@q)
    total = float(q@(k@q))
    physical_work = (float(q@(physical@q)) if physical is not None else total)
    ratio = float(np.linalg.norm(residual[free])/
                  max(1., np.linalg.norm(f[free])))
    if (not np.isfinite(q).all() or work <= 0. or
            max(ratio, abs(total-work)/work) > 1e-8):
        raise ArithmeticError("shell-only work or equilibrium failed")
    return {"compliance_work_j":work,
            "free_equilibrium_ratio":ratio,
            "work_error_j":total-work,
            "physical_work_j":physical_work,
            "nonphysical_work_j":total-physical_work}


def one_level(n: int) -> list[dict]:
    panel = make_shell(n, "Q4", n_y=n)
    native = FlatE4TrialPanel(panel)
    ns = 6*panel.node_count
    kn = native.evaluate(np.zeros(ns), .95).tangent
    physical = physical_shell_stiffness(panel).toarray()
    skew = np.linalg.norm(kn-kn.T)/np.linalg.norm(kn)
    if skew > 1e-9:
        raise ArithmeticError("reference E4 tangent lost conservative symmetry")
    fixed = {6*j*(panel.x_interval_count+1)+a
             for j in range(panel.n_y+1) for a in range(6)}
    fn = np.array([index for index in range(ns) if index not in fixed])
    classical = Model(n)
    ni = classical.offsets[2]
    ki = classical.k[:ni, :ni]
    fi = np.setdiff1d(np.arange(ni), classical.fixed[classical.fixed < ni])
    records=[]
    for law in ("distributing", "rigid"):
        for loading in ("tip_mx", "tip_fz"):
            force_n = native_force(panel, law, loading)
            force_i = independent_force(classical, law, loading)
            expected = (np.array((0., 0., 0., 100., 0., 0.))
                        if loading == "tip_mx" else
                        np.array((0., 0., 1000., 0., -950., 0.)))
            wrench = native_wrench(panel, force_n)
            if not np.allclose(wrench, expected, atol=1e-9, rtol=0.):
                raise ArithmeticError("native patch resultant changed")
            rn = response(kn, force_n, fn, physical=physical)
            ri = response(ki, force_i, fi)
            if abs(rn["nonphysical_work_j"])/rn["compliance_work_j"] > 1e-8:
                raise ArithmeticError("patch response depends on numerical shell work")
            records.append({"resolution":n, "law":law, "load":loading,
                            "expected_wrench_N_Nm":expected.tolist(),
                            "native_wrench_N_Nm":wrench.tolist(),
                            "native":rn, "independent":ri,
                            "native_tangent_relative_skew":float(skew)})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    worktree = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(("git", "rev-parse", "HEAD"),
                                   cwd=worktree, text=True).strip()
    if subprocess.check_output(("git", "status", "--porcelain"),
                               cwd=worktree, text=True).strip():
        raise RuntimeError("shell work screen requires clean source")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"status":"DEVELOPMENT_DISCRIMINATOR_NOT_G0_ACCEPTANCE",
                "question":"How much of the terminal footprint difference is already present in E4 versus classical shell work under the same physical resultant?",
                "decision":"If shell-only differences materially vary by operator, inspect shell/footprint deformation and discretization before attributing coupled differences to the beam or constraints. If shell-only work agrees, inspect the coupled pullback. Neither selects a connection.",
                "source_head":head,
                "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "python":platform.python_version(),
                "geometry":"flat plate [-.5,1.5]x[-.5,.5], t=.07 m; patch x=[.9,1], y=[-.05,.05]",
                "supports":"all E4 physical coordinates on left edge; equivalent classical membrane and spline RM clamp",
                "loads":"separate +100 Nm Mx and +1000 N Fz at patch center; rigid corner forces and distributing director/mean work carry the same total wrench",
                "models":"actual virgin E4 Q4 tangent/physical energy versus independent Q4 membrane plus spline RM plate",
                "limitations":"different transverse trial spaces; modest resolution screen only, no converged external or connection accuracy"}
    with threadpool_limits(limits=1):
        manifest["threadpools"] = threadpool_info()
        (root/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        records=[]
        # The existing E4 fixture admits y divisions 2, 4 or 8. Two
        # matched modest levels suffice for this diagnostic; no convergence
        # claim is made from them.
        for n in (2, 4):
            for result in one_level(n):
                records.append(result)
                print(json.dumps({"resolution":n,"law":result["law"],
                                  "load":result["load"],
                                  "native_work_j":result["native"]["compliance_work_j"],
                                  "independent_work_j":result["independent"]["compliance_work_j"]}),
                      flush=True)
        (root/"results.json").write_text(json.dumps(records,indent=2,
                                    allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
