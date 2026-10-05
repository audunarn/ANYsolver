"""Bounded independent six-channel plate/beam terminal-footprint comparator.

This assembles classical membrane, Reissner-Mindlin and Timoshenko energies
from existing independent operators. It shares no E4, native B3, or native
attachment residual. It is a formulation discriminator, not qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from threadpoolctl import threadpool_info, threadpool_limits

from scripts import _b3_e4_f03_independent_beam as membrane_beam
from scripts import _b3_e4_f03_independent_shell as membrane_shell
from scripts import b3_e4_f03_independent_transverse_reference as transverse
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


PATCH = ((.9, -.05), (1., -.05), (1., .05), (.9, .05))
BEAM_TIP = np.array((1., 0., .085))
PATCH_CENTER = np.array((.95, 0., 0.))


def skew(v: np.ndarray) -> np.ndarray:
    x, y, z = v
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


class Model:
    def __init__(self, n: int):
        if type(n) is not int or n not in (2, 3, 4):
            raise ValueError("bounded paired resolutions 2, 3, 4 required")
        self.n = n
        self.panel = membrane_shell.panel(n, n, "Q4")
        # The spline has its left-boundary value removed, imposing the same
        # full left-edge clamp on w, rx and ry as on the membrane field.
        st, bt, _, _, _, _ = transverse.assemble(
            2*n, n, 2*n, 2, basis="spline", origin="local",
            director="local", strip_half_length=.05,
            strip_half_width=.05)
        bt = bt.copy()
        torsion_dofs = bt.shape[0]//3
        bt[torsion_dofs:2*torsion_dofs,
           torsion_dofs:2*torsion_dofs] *= (
               square_torsion_constant()/transverse.BEAM_J)
        self.sizes = (self.panel.dof_count, len(st),
                      membrane_beam.dof_count(2*n), len(bt))
        self.offsets = np.cumsum((0, *self.sizes))
        self.k = sparse.block_diag((
            membrane_shell.stiffness(self.panel), sparse.csr_matrix(st),
            membrane_beam.assembled_stiffness(2*n), sparse.csr_matrix(bt)),
            format="csr")
        n_x = 2*self.panel.n_s
        fixed_membrane = [2*(j*(n_x+1))+a
                          for j in range(self.panel.n_y+1) for a in (0, 1)]
        fixed_beam = self.offsets[2]+membrane_beam.root_dofs(2*n)
        self.fixed = np.r_[fixed_membrane, fixed_beam].astype(int)
        self.free = np.setdiff1d(np.arange(self.k.shape[0]), self.fixed)

    def shell_translation(self, x: float, y: float) -> np.ndarray:
        result = np.zeros((3, self.k.shape[0]))
        nodes, weights = membrane_shell.sample(self.panel, x, y)
        for node, weight in zip(nodes, weights):
            result[0, 2*node] += weight
            result[1, 2*node+1] += weight
        basis, _, _ = transverse.plate_basis(
            2*self.n, self.n, x, y, basis="spline")
        result[2, self.offsets[1]:self.offsets[1]+len(basis)] = basis
        return result

    def shell_director(self, x: float, y: float) -> np.ndarray:
        result = np.zeros((2, self.k.shape[0]))
        basis, _, _ = transverse.plate_basis(
            2*self.n, self.n, x, y, basis="spline")
        m = len(basis)
        result[0, self.offsets[1]+m:self.offsets[1]+2*m] = basis
        result[1, self.offsets[1]+2*m:self.offsets[1]+3*m] = basis
        return result

    def beam_tip_pose(self) -> np.ndarray:
        result = np.zeros((6, self.k.shape[0]))
        planar = membrane_beam.trace(2*self.n, 1.).toarray()
        result[0, self.offsets[2]:self.offsets[3]] = planar[0]
        result[1, self.offsets[2]:self.offsets[3]] = planar[1]
        result[5, self.offsets[2]:self.offsets[3]] = planar[2]
        basis, _ = transverse.beam_basis(2*self.n, 1., basis="spline")
        m = len(basis)
        for row, block in ((2, 0), (3, 1), (4, 2)):
            start = self.offsets[3]+block*m
            result[row, start:start+m] = basis
        return result

    def shell_patch_pose(self) -> np.ndarray:
        """Area-mean position/director and mean-curl yaw of 0.1 m square."""
        result = np.zeros((6, self.k.shape[0]))
        roots, weights = np.polynomial.legendre.leggauss(4)
        # Split at both membrane hosts and spline knots; 4-point integration
        # then exactly covers the piecewise polynomial trial traces.
        x_edges = np.unique(np.r_[.9, 1.,
            self.panel.nodes[:, 0][(.9 < self.panel.nodes[:, 0]) &
                                    (self.panel.nodes[:, 0] < 1.)],
            transverse._spline(2*self.n, -.5, 1.5)[2][
                (.9 < transverse._spline(2*self.n, -.5, 1.5)[2]) &
                (transverse._spline(2*self.n, -.5, 1.5)[2] < 1.)]])
        y_edges = np.unique(np.r_[-.05, .05,
            self.panel.nodes[:, 1][(-.05 < self.panel.nodes[:, 1]) &
                                    (self.panel.nodes[:, 1] < .05)],
            transverse._spline(self.n, -.5, .5)[2][
                (-.05 < transverse._spline(self.n, -.5, .5)[2]) &
                (transverse._spline(self.n, -.5, .5)[2] < .05)]])
        area = .01
        for xa, xb in zip(x_edges[:-1], x_edges[1:]):
            for ya, yb in zip(y_edges[:-1], y_edges[1:]):
                for rx, wx in zip(roots, weights):
                    x = (xa+xb+rx*(xb-xa))/2
                    for ry, wy in zip(roots, weights):
                        y = (ya+yb+ry*(yb-ya))/2
                        darea = wx*wy*(xb-xa)*(yb-ya)/4
                        u = self.shell_translation(float(x), float(y))
                        director = self.shell_director(float(x), float(y))
                        result[:3] += darea/area*u
                        result[3:5] += darea/area*director
                        nodes, _ = membrane_shell.sample(
                            self.panel, float(x), float(y))
                        _, gradients, _ = membrane_shell.shape(
                            self.panel.nodes[list(nodes)], "Q4", (float(x), float(y)))
                        for node, (dx, dy) in zip(nodes, gradients):
                            result[5, 2*node] -= .5*darea/area*dy
                            result[5, 2*node+1] += .5*darea/area*dx
        return result

    def constraint(self, law: str) -> np.ndarray:
        beam = self.beam_tip_pose()
        if law == "distributing":
            shell = self.shell_patch_pose()
            result = beam-shell
            result[:3] += skew(BEAM_TIP-PATCH_CENTER)@shell[3:]
            return result
        if law != "rigid":
            raise ValueError("rigid or distributing footprint required")
        result = np.zeros((12, self.k.shape[0]))
        for index, (x, y) in enumerate(PATCH):
            point = np.array((x, y, 0.))
            result[3*index:3*index+3] = (
                self.shell_translation(x, y)-beam[:3]
                +skew(point-BEAM_TIP)@beam[3:])
        return result

    def solve(self, law: str, loading: str) -> dict:
        c = self.constraint(law)
        cf = c[:, self.free]
        rank = int(np.linalg.matrix_rank(cf, tol=1e-9))
        if rank != len(c):
            raise ArithmeticError("terminal rows are dependent")
        tip = self.beam_tip_pose()
        if loading == "tip_mx":
            f = 100.*tip[3]
            coordinate = 3
        elif loading == "tip_fz":
            f = 1000.*tip[2]
            coordinate = 2
        else:
            raise ValueError("tip_mx or tip_fz load required")
        primal_scale, multiplier_scale, energy_scale = 1e-5, 1e3, 1e-2
        kp = self.k[self.free, :][:, self.free]*(primal_scale**2/energy_scale)
        cp = sparse.csr_matrix(cf*(primal_scale*multiplier_scale/energy_scale))
        system = sparse.bmat(((kp, cp.T), (cp, None)), format="csc")
        rhs = np.r_[f[self.free]*primal_scale/energy_scale,
                    np.zeros(len(c))]
        scaled = spsolve(system, rhs)
        if not np.isfinite(scaled).all():
            raise ArithmeticError("nonfinite independent six-channel solve")
        q = np.zeros(self.k.shape[0])
        q[self.free] = primal_scale*scaled[:len(self.free)]
        lam = multiplier_scale*scaled[len(self.free):]
        residual = self.k@q+c.T@lam-f
        work = float(f@q)
        twice_energy = float(q@(self.k@q))
        free_error = float(np.linalg.norm(residual[self.free])/
                           max(1., np.linalg.norm(f[self.free])))
        gap = float(np.linalg.norm(c@q))
        if max(free_error, gap, abs(twice_energy-work)) > 1e-7:
            raise ArithmeticError("independent terminal equilibrium/work failed")
        return {"law":law, "load":loading, "rows":len(c), "rank":rank,
                "tip_work_coordinate":float(tip[coordinate]@q),
                "free_equilibrium_ratio":free_error,
                "constraint_gap_norm":gap,
                "work_error_j":twice_energy-work,
                "shell_energy_j":float(.5*q[:self.offsets[2]]@(
                    self.k[:self.offsets[2],:self.offsets[2]]@q[:self.offsets[2]])),
                "beam_energy_j":float(.5*q[self.offsets[2]:]@(
                    self.k[self.offsets[2]:,self.offsets[2]:]@q[self.offsets[2]:])),
                "external_work_j":work,
                "matrix_dimension":system.shape[0],
                "nnz":system.nnz}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    worktree = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(("git", "rev-parse", "HEAD"),
                                   cwd=worktree, text=True).strip()
    if subprocess.check_output(("git", "status", "--porcelain"),
                               cwd=worktree, text=True).strip():
        raise RuntimeError("independent reference requires clean source")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"status":"DEVELOPMENT_DISCRIMINATOR_NOT_G0_ACCEPTANCE",
                "question":"Do independently assembled six-channel classical plate/beam operators retain the distinct rigid/distributing terminal work responses?",
                "decision":"Consistent distinct responses support separate footprint idealizations; a reversal or failed work/rank sends the pose/constraint derivation back to review. Neither outcome selects or qualifies a native law.",
                "source_head":head,
                "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "python":platform.python_version(),
                "models":"Q4 plane-stress membrane + spline Reissner-Mindlin plate; independent planar and transverse Timoshenko beam with square Saint-Venant J",
                "geometry":"plate [-.5,1.5]x[-.5,.5], t=.07; square beam [0,1]x[-.05,.05], centroid z=.085; terminal patch x=[.9,1], y=[-.05,.05]",
                "loads":"separate +100 Nm tip Mx and +1000 N tip Fz",
                "supports":"full plate left edge and full beam root",
                "limitations":"small-strain classical models with different mesh spaces; no E4/B3 material, nonlinear chart, external accuracy, or true-line qualification"}
    with threadpool_limits(limits=1):
        manifest["threadpools"] = threadpool_info()
        (root/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        records=[]
        for n in (2, 3, 4):
            model=Model(n)
            for law in ("distributing", "rigid"):
                for load in ("tip_mx", "tip_fz"):
                    result=model.solve(law,load)
                    result["resolution"]=n
                    records.append(result)
                    print(json.dumps({"resolution":n,"law":law,"load":load,
                                      "tip_work_coordinate":result["tip_work_coordinate"]}),
                          flush=True)
        (root/"results.json").write_text(json.dumps(records, indent=2,
                                    allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
