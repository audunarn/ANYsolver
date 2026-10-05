"""Compare saved solid and native C1 P0 component work operators.

The 24 existing solid action fields are reused. This is a fixed-law,
fixed-mesh development attribution, not a connection or stability gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


CHANNELS = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")
SCALE = np.array([40000. if j % 6 < 3 else 4000. for j in range(24)])


def component_work(matrix: np.ndarray, coefficient: np.ndarray) -> dict:
    """Keep signed physical-channel terms, including cancellation."""
    h = np.asarray(matrix, dtype=float)
    c = np.asarray(coefficient, dtype=float)
    if h.shape != (24, 24) or c.shape != (24,) or not np.isfinite(h).all() or not np.isfinite(c).all():
        raise ValueError("finite P0 m4 work operator and action required")
    contributions = c*(h@c)
    grouped = contributions.reshape(4, 6).sum(axis=0)
    work = float(c@h@c)
    if abs(grouped.sum()-work) > 1e-10*max(1., abs(work)):
        raise ArithmeticError("channel work decomposition changed")
    return {"work_J": work,
            "signed_work_by_channel_J": dict(zip(CHANNELS, grouped.tolist()))}


def _solid_matrices(reconstruction):
    deck, _, coords, _, _, _ = _source(Path(reconstruction["source_root"])/"tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("solid deck identity changed")
    plate, bar = _element_domain_nodes(deck)
    nodes, rows, _ = integrated_rows(coords, plate, bar)
    plate_cols = np.array([3*j+k for j, node in enumerate(nodes)
                           if node in plate for k in range(3)])
    bar_cols = np.array([3*j+k for j, node in enumerate(nodes)
                         if node in bar for k in range(3)])
    if len(plate_cols)+len(bar_cols) != rows.shape[1]:
        raise ArithmeticError("solid side partition changed")
    values = []
    for j, record in enumerate(reconstruction["unit_records"]):
        if record["channel"] != j:
            raise ValueError("solid unit action order changed")
        frd = (Path(reconstruction["response_root"])/f"channel-{j}"/
               f"material-line-p0-{j}.frd")
        if digest(frd) != record["frd_sha256"]:
            raise ValueError("solid unit response changed")
        field = _read_frd_u(frd)
        if not set(nodes) <= set(field):
            raise ValueError("incomplete solid action displacement")
        values.append(np.array([field[node] for node in nodes]).ravel())
    unit = np.stack(values, axis=1)
    plate_work = SCALE[:, None]*(rows[:, plate_cols]@unit[plate_cols])
    bar_work = SCALE[:, None]*(rows[:, bar_cols]@unit[bar_cols])
    return plate_work, bar_work


def _native_matrices():
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    line = MaterialLinePosition(xs, ys, beam)
    rows, measure = _rows(
        line, LineMultiplierSpace("piecewise_constant",
                                  tuple(np.linspace(0., 1., 5))))
    if rows.shape[0] != 24 or not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("native P0 m4 basis changed")
    integrated = rows*measure.repeat(6)[:, None]
    shell_size = 6*line.shell_count
    shell_k, _ = raw_e4_tangent(xs, ys, thickness=.035)
    if beam.tangent is None:
        raise ArithmeticError("native retained beam tangent required")
    shell_fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
                   for i, x in enumerate(xs) if abs(x+.5) < 1e-12
                   for axis in range(6)}
    shell_free = np.array(sorted(set(range(shell_size))-shell_fixed))
    beam_free = np.array(sorted(set(range(beam.context.count))-
                                set(beam.context.fixed)))

    def response(tangent, columns, free):
        reduced = sparse.csc_matrix(tangent)[free, :][:, free]
        factor = splu(reduced)
        applied = columns[:, free].T*SCALE[None, :]
        solved = factor.solve(applied)
        defect = np.linalg.norm(reduced@solved-applied)/max(1., np.linalg.norm(applied))
        if defect > 1e-9:
            raise ArithmeticError("native component action equilibrium failed")
        return (SCALE[:, None]*columns[:, free])@solved, float(defect)

    shell, shell_error = response(shell_k, integrated[:, :shell_size], shell_free)
    bar, bar_error = response(beam.tangent, integrated[:, shell_size:], beam_free)
    return shell, bar, {"shell_equilibrium_ratio": shell_error,
                        "beam_equilibrium_ratio": bar_error,
                        "shell_free_variables": len(shell_free),
                        "beam_free_variables": len(beam_free)}


def evaluate(reconstruction_path: Path, same_action_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    same_action = json.loads(same_action_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            same_action["solid_reconstruction_sha256"] != digest(reconstruction_path)):
        raise ValueError("same-law saved comparison identities changed")
    solid_shell, solid_bar = _solid_matrices(reconstruction)
    native_shell, native_bar, native_diagnostics = _native_matrices()
    matrices = {"solid_shell": solid_shell, "solid_bar": solid_bar,
                "native_shell": native_shell, "native_bar": native_bar}
    diagnostics = {}
    for name, matrix in matrices.items():
        skew = np.linalg.norm(matrix-matrix.T)/max(1e-30, np.linalg.norm(matrix))
        if skew > (5e-6 if name.startswith("solid") else 1e-9):
            raise ArithmeticError(f"{name} action reciprocity changed: {skew}")
        singular = np.linalg.svd(matrix, compute_uv=False)
        symmetric = np.linalg.eigvalsh((matrix+matrix.T)/2.)
        diagnostics[name] = {"relative_skew": float(skew),
                             "frobenius_norm_J": float(np.linalg.norm(matrix)),
                             "relative_1e_minus_10_numerical_rank": int(np.count_nonzero(
                                 singular > 1e-10*singular[0])),
                             "minimum_symmetric_eigenvalue_J": float(symmetric[0])}
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
        if dual.shape != (24,):
            raise ValueError("saved line dual changed")
        coefficient = dual/SCALE
        components = {name: component_work(matrix, coefficient)
                      for name, matrix in matrices.items()}
        expected = same_action["cases"][label]
        for name, key in (("solid_shell", "solid_shell_action_only_work_J"),
                          ("solid_bar", "solid_beam_action_only_work_J"),
                          ("native_shell", "native_shell_action_only_work_J"),
                          ("native_bar", "native_beam_action_only_work_J")):
            observed = components[name]["work_J"]
            target = expected[key]
            if abs(observed-target) > 1e-5*max(abs(target), 1e-12):
                raise ArithmeticError(f"{label} {name} fixed-action work changed")
        differences = {channel: (components["native_shell"][
            "signed_work_by_channel_J"][channel]-components["solid_shell"][
                "signed_work_by_channel_J"][channel]) for channel in CHANNELS}
        cases[label] = {"components": components,
                        "native_minus_solid_shell_by_channel_J": differences,
                        "native_minus_solid_shell_total_J": float(sum(differences.values()))}
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "same physical P0 action, solid/native plate and beam compliance blocks",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "matrix_diagnostics": diagnostics,
        "native_diagnostics": native_diagnostics,
        "cases": cases,
        "limitations": [
            "fixed duals and linear component actions only; not loaded coupled sensitivity",
            "3D plate/bar and E4/B3 differ in kinematics and support spaces",
            "signed channel contributions may cancel and are not isolated energies",
            "no line-law selection, stability or F03/G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", required=True, type=Path)
    parser.add_argument("--same-action", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous component result")
    result = evaluate(args.reconstruction.resolve(), args.same_action.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: value["native_minus_solid_shell_by_channel_J"]
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
