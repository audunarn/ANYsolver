"""Installed native counterpart of the independently derived fixed B2 reference.

Only the reference fixture generator is imported; its OpenSees main is not run.
Connection rows must agree before an external loaded comparison is meaningful.
No mesh convergence or complete E01 qualification is claimed.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,'C:\\Users\\AUDUNA~1\\AppData\\Local\\Temp\\r8-b2-work-envelope-installed-v1\\site')
import numpy as np
from scipy import sparse
import numba
import threadpoolctl
from anysolver import stiffened_shell
import b2_e01_opensees_finite_point as reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pools = threadpoolctl.threadpool_info()
    assert pools and all(p["num_threads"] == 1 for p in pools)
    assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS == 1
    summary = {"status": "FAILED", "python": sys.version,
               "executable": sys.executable, "threads": pools, "jit_disabled": True,
               "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "reference_source_sha256": hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
               "imported_facade": stiffened_shell.__file__, "panels": []}
    try:
        law = stiffened_shell.LinearSection.isotropic(
            E=reference.E, nu=reference.NU, area=reference.A,
            Iy=reference.IY, Iz=reference.IZ, J=reference.J,
            ky=reference.KY, kz=reference.KZ)
        for sign in (-1, 1):
            model = reference.panel_input(sign)
            nodes = model["coordinates_m"]
            shells = tuple(stiffened_shell.Q4PanelShell(
                f"shell-{i}", cell, reference.E, reference.NU, reference.H)
                for i, cell in enumerate(reference.CELLS))
            members = tuple(stiffened_shell.PhysicalB2Member(
                f"beam-{i}", f"reference/beam-{i}", beam,
                tuple(nodes[node] for node in beam), (0., 1., 0.),
                "scalar-elastic", law)
                for i, beam in enumerate(reference.BEAMS))
            points = tuple(stiffened_shell.Q4B2Point(
                f"point-{i}", f"shell-{i}", f"beam-{i}", .5)
                for i in range(2))
            free = [i for i in range(54) if i not in model["fixed_coordinates"]]
            definition = stiffened_shell.B2Q4PanelDefinition(
                stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
                {node: nodes[node] for node in reference.SHELL_NODES},
                shells, members, points, sparse.eye(54, format="csr")[:, free],
                np.zeros(54))
            owner = stiffened_shell.create_analysis(definition=definition)
            try:
                # Private matrix access is a diagnostic law-equivalence check;
                # construction and solves go through the installed public API.
                observed = owner._C.toarray()
                expected = np.asarray(model["constraint_rows"])
                row_error = float(np.max(np.abs(observed-expected)))
                assert np.isfinite(row_error) and row_error <= 1e-10, row_error
                record = {"sign": sign, "constraint_row_max_error": row_error,
                          "constraint_rows": observed.tolist(), "cases": []}
                summary["panels"].append(record)
                for name, component, magnitude in reference.LOADS:
                    source=output.parent/f'panel-{sign}-{name}'/f'panel-{sign}-{name}.json'
                    external=json.loads(source.read_text())
                    u=np.array([v for node in reference.NODE_IDS for v in external['nodal_states'][str(node)]])
                    native_internal=np.asarray(owner._K@u).reshape(-1)
                    external_internal=np.asarray(external['internal_covector'])
                    external_elements={v['element']:np.asarray(v['global_covector']) for v in external['element_global_covectors']}
                    beam_native=np.zeros(54);beam_external=np.zeros(54);beam_checks=[]
                    scale_f=magnitude if component<3 else magnitude/2.
                    for member_id,(compiled,slots) in owner._members:
                        tag=101+int(member_id.split('-')[-1])
                        local_map=compiled.local_dof_map()
                        k=local_map.T@compiled.operator.evaluate(np.zeros(12)).tangent@local_map
                        force=np.asarray(k@u[slots]).reshape(-1)
                        expected_force=external_elements[tag]
                        beam_native[slots]+=force;beam_external[slots]+=expected_force
                        errors=np.abs(force-expected_force)/np.tile([scale_f]*3+[2*scale_f]*3,2)
                        beam_checks.append({'member':member_id,'load_scaled_covector_error':float(np.max(errors))})
                    row_scale=np.tile([scale_f]*3+[2*scale_f]*3,9)
                    shell_difference=native_internal-beam_native-(external_internal-beam_external)
                    full_difference=native_internal-external_internal
                    record['cases'].append({'name':name,'beam_checks':beam_checks,
                        'full_operator_difference_load_scaled':float(np.max(np.abs(full_difference)/row_scale)),
                        'shell_operator_difference_load_scaled':float(np.max(np.abs(shell_difference)/row_scale)),
                        'beam_covector_parity_passed':all(v['load_scaled_covector_error']<=1e-10 for v in beam_checks)})
            finally:
                owner.close()
        summary["status"] = "SAME_STATE_COVECTOR_DIAGNOSTIC_ONLY"
    finally:
        (output/"native.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status": summary["status"], "panels": len(summary["panels"]),
                      "cases": sum(len(p["cases"]) for p in summary["panels"])}))


if __name__ == "__main__":
    main()
