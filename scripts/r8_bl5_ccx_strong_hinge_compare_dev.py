"""Check executed strong-hinge Fy/Mx decks against physical-row C3D20 KKT."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts import r8_bl5_ccx_strong_hinge_deck_dev as specimen
from scripts import r8_bl5_strong_hinge_pair_dev as pair
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts.r8_e02_double_output import read_double_output
from scripts.r8_bl5_mx_section_port_dev import _wrench


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def compare(case: Path, independent: Path) -> dict:
    saved = json.loads(independent.read_text(encoding="utf-8"))
    metadata = json.loads((case/"metadata.json").read_text(encoding="utf-8"))
    decks, expected = specimen.decks(independent)
    if metadata != json.loads(json.dumps(expected)):
        raise ValueError("prepared geometry/constraint metadata changed")
    nx, ny, nz = pair.LEVEL
    shell_nodes, shell_elements = shell_ref._shell_mesh(nx,ny,nz)
    beam_nodes, beam_elements = beam_ref._mesh(nx,ny,nz)
    model = shell_ref._combined(shell_nodes,shell_elements,beam_nodes,beam_elements)
    if ({str(k):list(v) for k,v in model["physical_nodes"].items()} != metadata["physical_nodes"]
            or {str(k):list(v) for k,v in model["elements"].items()} != metadata["elements"]):
        raise ValueError("independent operator geometry differs from deck")
    shell = shell_ref._shell_body(shell_nodes,shell_elements,pair.LEVEL)
    beam = beam_ref._body(beam_nodes,beam_elements,pair.LEVEL)
    k = sparse.block_diag((shell,beam),format="csr")
    c = pair._strong_rows(model,nx+1)
    order,index,fixed,free,_ = continuum.layout(model)
    physical = k[free,:][:,free].tocsc()
    cf = c[:,free].tocsc()
    dq = 1./np.sqrt(physical.diagonal())
    dl = 1./np.sqrt(np.asarray((cf @ sparse.diags(dq)).power(2).sum(axis=1)).ravel())
    if not np.isfinite(dq).all() or not np.isfinite(dl).all():
        raise ValueError("nonfinite independent KKT scaling")
    dp,dm = sparse.diags(dq),sparse.diags(dl)
    system = sparse.bmat([[dp @ physical @ dp,dp @ cf.T @ dm],
                          [dm @ cf @ dp,None]],format="csc")
    factor = splu(system)
    actuals = {}
    loads = {}
    results = {}
    for name in ("fy","mx"):
        receipt = json.loads((case/f"{name}.receipt.json").read_text(encoding="utf-8"))
        if (receipt["status"] != "EXITED" or receipt["exit_code"] != 0
                or receipt["executable_sha256"] !=
                "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
                or receipt["metadata_sha256"] != digest(case/"metadata.json")
                or receipt["independent_sha256"] != digest(independent)
                or receipt["deck_sha256"] != sha256(decks[name]).hexdigest()
                or (case/f"{name}.inp").read_bytes() != decks[name]
                or any(digest(case/file) != value for file,value in receipt["file_sha256"].items())):
            raise ValueError("executed external identity mismatch")
        if "     1          1     1     1  0.100000E+01" not in (case/f"{name}.sta").read_text(encoding="ascii"):
            raise ValueError("one accepted external increment required")
        load = np.array(metadata["cases"][name]["physical_tip_load_N"],dtype=float)
        observed,reactions = read_double_output((case/f"{name}.frd").read_bytes(),metadata)
        actual = np.array([value for node in order for value in observed[node]])
        root_raw = np.array([value for node in model["root_nodes"] for value in reactions[node]])
        rhs = np.r_[dq*load[free],np.zeros(c.shape[0])]
        state = factor.solve(rhs)
        for _ in range(6):
            state += factor.solve(rhs-system @ state)
        reference = np.zeros(len(load))
        reference[free] = dq*state[:len(free)]
        lagrange = dl*state[len(free):]
        residual = np.asarray(k @ actual-load).ravel()
        fitted = np.linalg.lstsq(cf.T.toarray(),-residual[free],rcond=None)[0]
        interface = np.asarray(c.T @ fitted).ravel()
        corrected_root = root_raw+interface[fixed]
        support = np.zeros(len(load))
        support[fixed] = corrected_root
        applied_wrench = _wrench(np.array([model["physical_nodes"][n] for n in order]),load)
        support_wrench = _wrench(np.array([model["physical_nodes"][n] for n in order]),support)
        work = float(load @ actual)
        reference_work = float(load @ reference)
        checks = {
            "displacement_parity":float(np.linalg.norm(actual-reference)/max(np.linalg.norm(reference),1e-14)),
            "saved_independent_work":abs(reference_work-saved["strong"]["cases"][name]["applied_work_J"])/max(abs(reference_work),1e-12),
            "independent_equation":float(np.linalg.norm(system @ state-rhs)/max(np.linalg.norm(load),1.)),
            "strong_gap":float(np.max(abs(np.asarray(c @ actual).ravel()))),
            "free_equilibrium":float(np.linalg.norm(residual[free]+interface[free])/max(np.linalg.norm(load),1.)),
            "raw_reaction":float(np.linalg.norm(root_raw-residual[fixed])/max(np.linalg.norm(load),1.)),
            "physical_support":float(np.linalg.norm(corrected_root-(k @ reference-load+c.T @ lagrange)[fixed])/max(np.linalg.norm(load),1.)),
            "force_balance":float(np.max(abs((support_wrench+applied_wrench)[:3]))/max(np.linalg.norm(applied_wrench[:3]),1.)),
            "moment_balance":float(np.max(abs((support_wrench+applied_wrench)[3:]))/max(np.linalg.norm(applied_wrench[3:]),1.)),
            "work_balance":abs(float(actual @ (k @ actual))-work)/max(abs(work),1e-12),
        }
        limits = {key:(1e-9 if key=="strong_gap" else 1e-6) for key in checks}
        results[name] = {"checks":checks,"limits":limits,"external_work_J":work,
                         "independent_work_J":reference_work,
                         "applied_wrench_about_origin":applied_wrench.tolist(),
                         "corrected_support_wrench_about_origin":support_wrench.tolist(),
                         "interface_work_J":float(interface @ actual),
                         "frd_sha256":digest(case/f"{name}.frd"),
                         "receipt_sha256":digest(case/f"{name}.receipt.json")}
        actuals[name],loads[name] = actual,load
    cross = np.array([[float(loads[a] @ actuals[b]) for b in ("fy","mx")]
                      for a in ("fy","mx")])
    expected_cross = np.array(saved["strong"]["cross_work_matrix_J"])
    cross_error = float(np.linalg.norm(cross-expected_cross)/max(np.linalg.norm(expected_cross),1e-12))
    reciprocal_error = float(abs(cross[0,1]-cross[1,0])/max(np.linalg.norm(cross),1e-12))
    passed = (all(np.isfinite(v) and v <= results[name]["limits"][key]
                  for name in results for key,v in results[name]["checks"].items())
              and cross_error <= 1e-6 and reciprocal_error <= 1e-6)
    return {"identity":"R8_BL5_CCX_STRONG_HINGE_8X4X2_FY_MX_COMPARE_DEV_V1",
        "status":"DEVELOPMENT_PARITY_NOT_QUALIFIED" if passed else "DEVELOPMENT_PARITY_FAILED",
        "source_sha256":digest(Path(__file__)),"independent_sha256":digest(independent),
        "metadata_sha256":digest(case/"metadata.json"),"physical_rows":c.shape[0],
        "physical_dofs":k.shape[0],"kkt_nnz":system.nnz,"cases":results,
        "cross_work_matrix_J":cross.tolist(),"cross_work_relative_error":cross_error,
        "cross_work_reciprocity":reciprocal_error,
        "limitation":"same-grid sampled continuum director hinge; external parity does not establish native BL5/F03 or convergence"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case",type=Path,required=True)
    parser.add_argument("--independent",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous comparison")
    result = compare(args.case,args.independent)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"cross_work_relative_error":result["cross_work_relative_error"],
                      "checks":{name:case["checks"] for name,case in result["cases"].items()}}))
    if result["status"] != "DEVELOPMENT_PARITY_NOT_QUALIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
