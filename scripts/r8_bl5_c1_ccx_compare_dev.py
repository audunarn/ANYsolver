"""Compare executed compact C1 CalculiX Fy/Mx U/RF against parsed-deck KKT.

One-grid solid solver parity only; not native BL5 or physical convergence.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts.r8_bl5_c1_line_kkt_dev import _assemble, _read, _wrench
from scripts.r8_e02_double_output import read_double_output

PINNED_CCX_SHA256="27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _accepted(sta: Path) -> bool:
    lines=sta.read_text(encoding="ascii").splitlines()
    rows=[line.split() for line in lines if line.strip().startswith("1")]
    return len(rows)==1 and len(rows[0])==7 and rows[0][:4]==["1","1","1","1"] and abs(float(rows[0][4])-1.)<1e-12


def evaluate(case: Path, independent: Path) -> dict:
    saved=json.loads(independent.read_text(encoding="utf-8"))
    if saved["status"]!="INDEPENDENT_KKT_ONLY_NOT_QUALIFIED":
        raise ValueError("completed exact-deck KKT required")
    models={name:_read(case/f"{name}.inp") for name in ("fy","mx")}
    for name in models:
        receipt=json.loads((case/f"{name}.receipt.json").read_text(encoding="utf-8"))
        if (receipt["case"]!=name or receipt["status"]!="EXITED" or
                receipt["exit_code"]!=0 or
                receipt["executable_sha256"]!=PINNED_CCX_SHA256 or
                receipt["deck_sha256"]!=saved["prepared_decks"][name] or
                _sha(case/f"{name}.inp")!=receipt["deck_sha256"] or
                receipt["file_sha256"].get(f"{name}.frd")!=_sha(case/f"{name}.frd") or
                receipt["file_sha256"].get(f"{name}.sta")!=_sha(case/f"{name}.sta") or
                not _accepted(case/f"{name}.sta")):
            raise ValueError(f"{name} exact completed external solve required")
    model=models["fy"]
    k,order,index,assembly=_assemble(model)
    size=k.shape[0]
    if size!=saved["physical_dofs"] or assembly!=saved["assembly"]:
        raise ValueError("independent operator inventory changed")
    rows,cols,values=[],[],[]
    for i,equation in enumerate(model["equations"]):
        for n,axis,value in equation:
            rows.append(i);cols.append(index[n]+axis-1);values.append(value)
    c=sparse.coo_matrix((values,(rows,cols)),shape=(len(model["equations"]),size)).tocsc()
    fixed=np.array([index[n]+j for n in sorted(model["supports"]) for j in range(3)])
    free=np.setdiff1d(np.arange(size),fixed)
    loads=np.zeros((size,2))
    for j,name in enumerate(("fy","mx")):
        for (n,axis),force in models[name]["loads"].items():
            loads[index[n]+axis-1,j]+=force
    kff=k[free,:][:,free]
    cf=c[:,free]
    dq=1./np.sqrt(kff.diagonal())
    dl=1./np.sqrt(np.asarray((cf@sparse.diags(dq)).power(2).sum(axis=1)).ravel())
    dp,dm=sparse.diags(dq),sparse.diags(dl)
    system=sparse.bmat([[dp@kff@dp,dp@cf.T@dm],[dm@cf@dp,None]],format="csc")
    rhs=np.vstack((dq[:,None]*loads[free,:],np.zeros((c.shape[0],2))))
    factor=splu(system)
    state=factor.solve(rhs)
    for _ in range(3):state+=factor.solve(rhs-system@state)
    predicted=np.zeros_like(loads)
    predicted[free,:]=dq[:,None]*state[:len(free),:]
    multiplier=dl[:,None]*state[len(free):,:]
    positions=np.array([model["nodes"][n] for n in order])
    external=np.zeros_like(loads)
    cases={}
    for j,name in enumerate(("fy","mx")):
        expected={"physical_nodes":models[name]["nodes"],
                  "elements":models[name]["elements"],
                  "root_nodes":models[name]["supports"]}
        displacement,reactions=read_double_output((case/f"{name}.frd").read_bytes(),expected)
        external[:,j]=np.concatenate([displacement[n] for n in order])
        reaction=np.zeros(size)
        for n,force in reactions.items():reaction[index[n]:index[n]+3]=force
        q=predicted[:,j]
        predicted_reaction=np.zeros(size)
        predicted_reaction[fixed]=(k@q+c.T@multiplier[:,j]-loads[:,j])[fixed]
        maximum=float(np.max(np.abs(q)))
        relative_displacement=float(np.max(np.abs(external[:,j]-q))/max(maximum,1e-12))
        reaction_relative=float(np.max(np.abs(reaction-predicted_reaction))/100.)
        external_work=float(loads[:,j]@external[:,j])
        kkt_work=saved["cases"][name]["applied_work_J"]
        work_relative=abs(external_work-kkt_work)/max(abs(kkt_work),1e-12)
        gap=float(np.max(np.abs(c@external[:,j])))
        balance=_wrench(positions,loads[:,j]+reaction)
        checks={"displacement_relative_max":relative_displacement,
                "support_reaction_over_100N":reaction_relative,
                "applied_work_relative":work_relative,
                "external_equation_gap_m":gap,
                "force_balance_over_100N":float(np.max(abs(balance[:3]))/100.),
                "moment_balance_over_100Nm":float(np.max(abs(balance[3:]))/100.)}
        limits={key:(1e-8 if "gap" in key else 1e-6) for key in checks}
        cases[name]={"external_work_J":external_work,
                     "independent_kkt_work_J":kkt_work,
                     "external_max_displacement_m":float(np.max(abs(external[:,j]))),
                     "external_support_wrench":_wrench(positions,reaction).tolist(),
                     "checks":checks,"limits":limits,
                     "passed":all(np.isfinite(v) and v<=limits[key]
                                  for key,v in checks.items())}
    cross=loads.T@external
    reciprocity=float(abs(cross[0,1]-cross[1,0])/max(np.linalg.norm(cross),1e-12))
    cross_error=float(np.max(abs(cross-np.asarray(saved["cross_work_matrix_J"])))
                      /max(np.linalg.norm(saved["cross_work_matrix_J"]),1e-12))
    passed=all(item["passed"] for item in cases.values()) and reciprocity<=1e-6 and cross_error<=1e-6
    return {"identity":"R8_BL5_C1_CCX_FY_MX_PARITY_DEV_V2",
            "status":"DEVELOPMENT_EXTERNAL_PARITY_NOT_QUALIFIED" if passed else
                     "DEVELOPMENT_EXTERNAL_PARITY_FAILED",
            "source_sha256":_sha(Path(__file__)),
            "independent_kkt_sha256":_sha(independent),
            "executable_sha256":PINNED_CCX_SHA256,
            "external_receipts":{n:_sha(case/f"{n}.receipt.json") for n in ("fy","mx")},
            "frd_sha256":{n:_sha(case/f"{n}.frd") for n in ("fy","mx")},
            "physical_dofs":size,"constraint_rows":c.shape[0],
            "cases":cases,"external_cross_work_matrix_J":cross.tolist(),
            "cross_work_reciprocity":reciprocity,
            "cross_work_relative_error":cross_error,
            "limitation":"same-grid C3D20R terminal centerline hinge only; no native BL5 or mesh-converged physical connection acceptance"}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=Path,required=True)
    parser.add_argument("--independent",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError("preserve previous comparison")
    result=evaluate(args.case,args.independent)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "checks":{n:v["checks"] for n,v in result["cases"].items()},
                      "reciprocity":result["cross_work_reciprocity"]}))
    if result["status"]!="DEVELOPMENT_EXTERNAL_PARITY_NOT_QUALIFIED":
        raise SystemExit(1)


if __name__=="__main__":main()
