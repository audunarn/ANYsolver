"""Same-body 17-station C3D20 exact quadratic five-channel trace design.

This bounded solid-proxy construction is development evidence, not a native
BL5 law, F03 assessment or continuum-shell/beam accuracy qualification.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts import r8_bl5_strong_hinge_pair_dev as pair
from scripts import r8_bl5_mx_matched_refinement_dev as matched
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts import r8_bl5_ccx_strong_hinge_deck_dev as previous_deck
from scripts.r8_bl5_mx_section_port_dev import _wrench


ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/".development/bl5-strong-hinge-pair-20261008-v1/result.json"
PREVIOUS_SHA="8dd8a81088aa4b072b87251208438899ccf08c506505bff077e406c37e0ad31e"
LEVEL=(8,4,2)
STATIONS=17


def digest(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def evaluate()->dict:
    if digest(PREVIOUS)!=PREVIOUS_SHA:
        raise ValueError("exact prior same-body two-load design result required")
    previous=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if previous["status"]!="DEVELOPMENT_REFERENCE_DESIGN_NOT_QUALIFIED" or tuple(previous["level"])!=LEVEL:
        raise ValueError("prior design completion or geometry changed")
    runtime=pair._runtime()
    started=time.perf_counter()
    shell_nodes,shell_elements=shell_ref._shell_mesh(*LEVEL)
    beam_nodes,beam_elements=beam_ref._mesh(*LEVEL)
    model=shell_ref._combined(shell_nodes,shell_elements,beam_nodes,beam_elements)
    shell=shell_ref._shell_body(shell_nodes,shell_elements,LEVEL)
    beam=beam_ref._body(beam_nodes,beam_elements,LEVEL)
    k=sparse.block_diag((shell,beam),format="csr")
    c=pair._strong_rows(model,STATIONS)
    order,index,fixed,free,_=continuum.layout(model)
    dependent=np.array([
        index[previous_deck._node_at(model,(j/(STATIONS-1),0.,.01 if channel<3 else .07))]
        +(channel if channel<3 else channel-3)
        for channel in range(5) for j in range(STATIONS)],dtype=int)
    if (c.shape!=(5*STATIONS,k.shape[0]) or len(set(dependent))!=len(dependent)
            or any(slot in fixed for slot in dependent)):
        raise ValueError("complete unique physical 85-row pivot set required")
    pivot_condition=float(np.linalg.cond(c[:,dependent].toarray()))
    if not np.isfinite(pivot_condition) or pivot_condition>1e10:
        raise ValueError("rank-deficient or ill-conditioned physical pivot set")
    tip,tip_meta=beam_ref._port(beam_nodes,beam_elements,1.,LEVEL)
    loads=np.zeros((k.shape[0],2))
    loads[-beam.shape[0]:,0]=tip.T @ np.array((0.,pair.FORCE_Y_N,0.,0.,0.,0.))
    loads[-beam.shape[0]:,1]=tip.T @ np.array((0.,0.,0.,pair.TORQUE_X_NM,0.,0.))
    physical=k[free,:][:,free].tocsc()
    cf=c[:,free].tocsc()
    dq=1./np.sqrt(physical.diagonal())
    dl=1./np.sqrt(np.asarray((cf @ sparse.diags(dq)).power(2).sum(axis=1)).ravel())
    if not np.isfinite(dq).all() or not np.isfinite(dl).all():
        raise ValueError("nonfinite independent physical scaling")
    dp,dm=sparse.diags(dq),sparse.diags(dl)
    system=sparse.bmat([[dp @ physical @ dp,dp @ cf.T @ dm],
                        [dm @ cf @ dp,None]],format="csc")
    factor=splu(system)
    q=np.zeros_like(loads)
    multipliers=np.zeros((c.shape[0],2))
    cases={}
    xyz=np.array([model["physical_nodes"][n] for n in order])
    faces=matched._face_index(model)
    gauss,weights=np.polynomial.legendre.leggauss(3)
    rows=np.stack([np.stack([
        matched._five_rows(model,index,faces,(edge+(1.+float(g))/2.)/LEVEL[0])
        for g in gauss]) for edge in range(LEVEL[0])])
    for j,name in enumerate(("fy","mx")):
        load=loads[:,j]
        rhs=np.r_[dq*load[free],np.zeros(c.shape[0])]
        state=factor.solve(rhs)
        for _ in range(6):
            state+=factor.solve(rhs-system @ state)
        q[free,j]=dq*state[:len(free)]
        multipliers[:,j]=dl*state[len(free):]
        internal=np.asarray(k @ q[:,j]).ravel()
        residual=internal+np.asarray(c.T @ multipliers[:,j]).ravel()-load
        support=np.zeros(len(load))
        support[fixed]=residual[fixed]
        work=float(load @ q[:,j])
        samples=np.einsum("sgcd,d->sgc",rows,q[:,j])
        rms=np.sqrt(np.einsum("g,sgc->c",weights,samples*samples)/(2*LEVEL[0]))
        balanced=_wrench(xyz,load+support)
        checks={
            "free_equilibrium":float(np.linalg.norm(residual[free])/max(pair.FORCE_Y_N,pair.TORQUE_X_NM)),
            "station_gap":float(np.max(abs(np.asarray(c @ q[:,j]).ravel()))),
            "interior_gap":float(np.max(abs(samples))),
            "strain_work":abs(float(q[:,j] @ internal)-work)/max(abs(work),1e-12),
            "interface_work":abs(float(q[:,j] @ (c.T @ multipliers[:,j])))/max(abs(work),1e-12),
            "force_balance":float(np.max(abs(balanced[:3]))/pair.FORCE_Y_N),
            "moment_balance":float(np.max(abs(balanced[3:]))/pair.TORQUE_X_NM),
        }
        limits={key:(1e-9 if "gap" in key else 1e-8) for key in checks}
        if any(not np.isfinite(value) or value>limits[key] for key,value in checks.items()):
            raise ValueError(f"{name} quadratic physical trace failed: {checks}")
        old_work=float(previous["strong"]["cases"][name]["applied_work_J"])
        cases[name]={"applied_work_J":work,"nine_station_work_J":old_work,
                     "relative_to_nine_station":work/old_work-1.,
                     "interior_rms_by_channel":rms.tolist(),
                     "checks":checks,"limits":limits,
                     "applied_wrench_about_origin":_wrench(xyz,load).tolist(),
                     "support_wrench_about_origin":_wrench(xyz,support).tolist()}
    cross=loads.T @ q
    reciprocity=float(abs(cross[0,1]-cross[1,0])/max(np.linalg.norm(cross),1e-12))
    if reciprocity>1e-8:
        raise ValueError("physical reciprocity changed")
    return {"identity":"R8_BL5_C3D20_QUADRATIC_TRACE_FY_MX_DESIGN_DEV_V1",
        "status":"DEVELOPMENT_QUADRATIC_TRACE_NOT_QUALIFIED",
        "source_sha256":digest(Path(__file__)),"previous_sha256":PREVIOUS_SHA,
        "level":LEVEL,"stations":STATIONS,"physical_rows":c.shape[0],
        "pivot_condition":pivot_condition,"physical_dofs":k.shape[0],
        "kkt_nnz":system.nnz,"tip_port":tip_meta,
        "cases":cases,"cross_work_matrix_J":cross.tolist(),
        "cross_work_reciprocity":reciprocity,"runtime":runtime,
        "wall_seconds":time.perf_counter()-started,
        "limitation":"exact piecewise-quadratic solid trace closure on this grid only; native BL5 physical equivalence and F03 open"}


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior quadratic-trace design")
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"rows":result["physical_rows"],
        "pivot_condition":result["pivot_condition"],
        "cases":{name:{"work":case["applied_work_J"],
                        "relative_to_nine_station":case["relative_to_nine_station"],
                        "interior_gap":case["checks"]["interior_gap"]}
                 for name,case in result["cases"].items()},
        "wall_seconds":result["wall_seconds"]}))


if __name__=="__main__":
    main()
