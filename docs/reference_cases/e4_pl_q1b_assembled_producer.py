"""Fast research-only Q1B assembled producer.

The local operator is a direct binary64 transcription of the frozen Q1Y3
stationary formulation.  It is commissioned against the preserved exact
Q1Y3 tower witnesses before it may be registered for assembled evidence.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import linalg

import e4_pl_q1b_common as common


IMPLEMENTATION_ID = "Q1B_HYBRID_NUMERIC_INTERVAL_PRODUCER"
RUNNER_ID = IMPLEMENTATION_ID


def _shape(r: float, s: float) -> np.ndarray:
    return np.array(((1-r)*(1-s), (1+r)*(1-s), (1+r)*(1+s), (1-r)*(1+s)), dtype=float) / 4.0


def _shape_derivatives(r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.array((-(1-s), 1-s, 1+s, -(1+s)), dtype=float) / 4.0,
        np.array((-(1-r), -(1+r), 1+r, 1-r), dtype=float) / 4.0,
    )


def _frame(nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d1, d2 = nodes[2] - nodes[0], nodes[1] - nodes[3]
    a, b = d1 / np.linalg.norm(d1), d2 / np.linalg.norm(d2)
    t1 = a + b
    t1 /= np.linalg.norm(t1)
    t2 = a - b
    t2 /= np.linalg.norm(t2)
    t3 = np.cross(t1, t2)
    frame = np.column_stack((t1, t2, t3))
    centre = np.mean(nodes, axis=0)
    local = np.column_stack(((nodes-centre) @ t1, (nodes-centre) @ t2))
    return frame, local


def _coefficients(local: np.ndarray) -> dict[str, float]:
    modal = np.array((
        (1, 1, 1, 1), (-1, 1, 1, -1),
        (-1, -1, 1, 1), (1, -1, 1, -1),
    ), dtype=float) / 4.0
    x0, xr, xs, xrs = modal @ local[:, 0]
    y0, yr, ys, yrs = modal @ local[:, 1]
    return {
        "x0": x0, "xr": xr, "xs": xs, "xrs": xrs,
        "y0": y0, "yr": yr, "ys": ys, "yrs": yrs,
        "jc": xr*ys-xs*yr, "jr": xr*yrs-xrs*yr,
        "js": xrs*ys-xs*yrs,
    }


def _jacobian(c: Mapping[str, float], r: float, s: float) -> tuple[float, float, float, float, float]:
    xr, xs = c["xr"] + c["xrs"]*s, c["xs"] + c["xrs"]*r
    yr, ys = c["yr"] + c["yrs"]*s, c["ys"] + c["yrs"]*r
    return xr, xs, yr, ys, xr*ys-xs*yr


def _natural_shear(local: np.ndarray, r: float, s: float, direction: int) -> np.ndarray:
    shape = _shape(r, s)
    nr, ns = _shape_derivatives(r, s)
    derivative = nr if direction == 0 else ns
    x_d, y_d = local[:, 0] @ derivative, local[:, 1] @ derivative
    row = np.zeros(20)
    for index in range(4):
        base = 5*index
        row[base+2] = derivative[index]
        row[base+3] = -y_d*shape[index]
        row[base+4] = x_d*shape[index]
    return row


def _compatible(local: np.ndarray, c: Mapping[str, float], r: float, s: float) -> np.ndarray:
    nr, ns = _shape_derivatives(r, s)
    xr, xs, yr, ys, jac = _jacobian(c, r, s)
    nx, ny = (ys*nr-yr*ns)/jac, (-xs*nr+xr*ns)/jac
    out = np.zeros((8, 20))
    for index in range(4):
        base = 5*index
        out[0, base], out[1, base+1] = nx[index], ny[index]
        out[2, base], out[2, base+1] = ny[index], nx[index]
        out[3, base+4], out[4, base+3] = nx[index], -ny[index]
        out[5, base+4], out[5, base+3] = ny[index], -nx[index]
    # Accepted Q1Y3 MITC construction: interpolate covariant tying rows first,
    # then transform using the current Jacobian inverse transpose.
    gr_a, gr_c = _natural_shear(local, 0.0, -1.0, 0), _natural_shear(local, 0.0, 1.0, 0)
    gs_b, gs_d = _natural_shear(local, 1.0, 0.0, 1), _natural_shear(local, -1.0, 0.0, 1)
    gr = 0.5*(1-s)*gr_a + 0.5*(1+s)*gr_c
    gs = 0.5*(1+r)*gs_b + 0.5*(1-r)*gs_d
    out[6] = (ys*gr-yr*gs)/jac
    out[7] = (-xs*gr+xr*gs)/jac
    return out


def _tensor(xr: float, xs: float, yr: float, ys: float, a: float, b: float) -> np.ndarray:
    return np.array(((xr*xr, xs*xs, a*xr*xs), (yr*yr, ys*ys, a*yr*ys), (b*xr*yr, b*xs*ys, xr*ys+yr*xs)), dtype=float)


def _interpolations(c: Mapping[str, float], r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    jc, jr, js = c["jc"], c["jr"], c["js"]
    rbar, sbar = jr/(3*jc), js/(3*jc)
    ts, te = _tensor(c["xr"], c["xs"], c["yr"], c["ys"], 2, 1), _tensor(c["xr"], c["xs"], c["yr"], c["ys"], 1, 2)
    shear = np.array(((c["xr"], c["xs"]), (c["yr"], c["ys"])), dtype=float)
    nsigma, nepsilon = np.zeros((8, 14)), np.zeros((8, 21))
    nsigma[:, :8] = np.eye(8)
    nepsilon[:, :8] = np.eye(8)
    seed = np.array(((s-sbar, 0), (0, r-rbar), (0, 0)), dtype=float)
    stress_vary, strain_vary = ts @ seed, te @ seed
    for row, column in ((0, 8), (3, 10)):
        nsigma[row:row+3, column:column+2] = stress_vary
        nepsilon[row:row+3, column:column+2] = strain_vary
    shear_seed = np.array(((s-sbar, 0), (0, r-rbar)), dtype=float)
    nsigma[6:8, 12:14] = shear @ shear_seed
    nepsilon[6:8, 12:14] = shear @ shear_seed
    m7 = np.array(((r,0,0,0,r*s,0,0),(0,s,0,0,0,r*s,0),(0,0,r,s,0,0,r*s)), dtype=float)
    jac = _jacobian(c, r, s)[4]
    nepsilon[:3, 14:21] = (jc/jac) * (te @ m7)
    return nsigma, nepsilon


def _constitutive(thickness: float) -> np.ndarray:
    e, nu, shear, ks = 15.0, 0.25, 6.0, 5.0/6.0
    membrane = e*thickness/(1-nu*nu) * np.array(((1,nu,0),(nu,1,0),(0,0,(1-nu)/2)))
    bending = e*thickness**3/(12*(1-nu*nu)) * np.array(((1,nu,0),(nu,1,0),(0,0,(1-nu)/2)))
    transverse = ks*shear*thickness*np.eye(2)
    out = np.zeros((8,8)); out[:3,:3]=membrane; out[3:6,3:6]=bending; out[6:,6:]=transverse
    return out


def _centre_taylor(c: Mapping[str, float]) -> np.ndarray:
    f0 = np.ones(4)/4
    fr = np.array((-1,1,1,-1))/4
    fs = np.array((-1,-1,1,1))/4
    frs = np.array((1,-1,1,-1))/4
    out = np.zeros((3,24)); jc,jr,js=c["jc"],c["jr"],c["js"]
    for coordinate in range(24):
        node, component = divmod(coordinate, 6)
        ur = fr[node] if component==0 else 0.; us = fs[node] if component==0 else 0.; urs=frs[node] if component==0 else 0.
        vr = fr[node] if component==1 else 0.; vs = fs[node] if component==1 else 0.; vrs=frs[node] if component==1 else 0.
        d0=f0[node] if component==5 else 0.; dr=fr[node] if component==5 else 0.; ds=fs[node] if component==5 else 0.
        n0=-c["xs"]*ur+c["xr"]*us-c["ys"]*vr+c["yr"]*vs
        nr=-c["xrs"]*ur+c["xr"]*urs-c["yrs"]*vr+c["yr"]*vrs
        ns=-c["xs"]*urs+c["xrs"]*us-c["ys"]*vrs+c["yrs"]*vs
        out[0,coordinate]=d0+n0/(2*jc)
        out[1,coordinate]=dr+(nr*jc-n0*jr)/(2*jc*jc)
        out[2,coordinate]=ds+(ns*jc-n0*js)/(2*jc*jc)
    return out


def _gamma(local: np.ndarray, c: Mapping[str, float]) -> np.ndarray:
    x,y=local[:,0],local[:,1]; s1=x-c["x0"]; s2=y-c["y0"]
    xi=np.array((-1,1,1,-1),dtype=float); eta=np.array((-1,-1,1,1),dtype=float); h4=np.array((1,-1,1,-1),dtype=float)
    area=4*c["jc"]
    b1=((eta@s2)*xi-(xi@s2)*eta)/(4*area)
    b2=(-(eta@s1)*xi+(xi@s1)*eta)/(4*area)
    return (h4-(h4@s1)*b1-(h4@s2)*b2)/4


def local_components(nodes: Sequence[Sequence[float]], thickness: float=2/3) -> dict[str, np.ndarray | float | bool]:
    node_array=np.asarray(nodes,dtype=float)
    frame,local=_frame(node_array); c=_coefficients(local)
    gp=(-1/math.sqrt(3),1/math.sqrt(3))
    gauss=((gp[0],gp[0]),(gp[1],gp[0]),(gp[1],gp[1]),(gp[0],gp[1]))
    if min([c["jc"]]+[_jacobian(c,r,s)[4] for r,s in gauss]) <= 0:
        raise common.Q1BError("nonpositive local Jacobian")
    f=np.zeros((21,14)); gq=np.zeros((14,20)); h=np.zeros((21,21)); constitutive=_constitutive(thickness)
    for r,s in gauss:
        jac=_jacobian(c,r,s)[4]; ns,ne=_interpolations(c,r,s); compatible=_compatible(local,c,r,s)
        f-=jac*(ne.T@ns); gq+=jac*(ns.T@compatible); h+=jac*(ne.T@constitutive@ne)
    d35=np.zeros((35,35)); d35[:14,14:]=f.T; d35[14:,:14]=f; d35[14:,14:]=h
    q20=np.zeros((20,35)); q20[:,:14]=gq.T
    qcore=np.zeros((24,35))
    for node in range(4): qcore[6*node:6*node+5]=q20[5*node:5*node+5]
    core=-qcore@linalg.solve(d35,qcore.T,assume_a="sym")
    gram=np.zeros((3,3))
    for r,s in gauss:
        p=np.array((1,r,s)); gram+=thickness*_jacobian(c,r,s)[4]*np.outer(p,p)
    centre=_centre_taylor(c); pl=6.0*centre.T@gram@centre
    gamma=_gamma(local,c); gamma24=np.zeros(24); gamma24[5::6]=gamma
    hg=2*(1/1000)*6.0*thickness*(4*c["jc"])*np.outer(gamma24,gamma24)
    local_total=core+pl+hg
    block=np.zeros((24,24))
    for node in range(4):
        block[6*node:6*node+3,6*node:6*node+3]=frame
        block[6*node+3:6*node+6,6*node+3:6*node+6]=frame
    return {"core":block@core@block.T,"pl":block@pl@block.T,"hg":block@hg@block.T,"total":block@local_total@block.T,"local_total":local_total,"frame":frame,"jacobian_centre":c["jc"],"mixed_condensed":True}


def _assemble(nodes: list[tuple[float,float,float]], elements: list[tuple[int,int,int,int]], thickness: float) -> dict[str,np.ndarray]:
    size=6*len(nodes); matrices={name:np.zeros((size,size)) for name in ("core","pl","hg","total")}
    for element in elements:
        components=local_components([nodes[index] for index in element],thickness)
        dofs=np.array([6*node+component for node in element for component in range(6)])
        for name in matrices: matrices[name][np.ix_(dofs,dofs)] += np.asarray(components[name])
    return matrices


def _geometry_nodes(repository_root: Path) -> dict[str,list[list[float]]]:
    value=json.loads((repository_root/"docs/reference_cases/e4_pl_q1r_geometry_contract.json").read_text(encoding="utf-8"))
    return {row["id"]:[[float(Fraction(item)) for item in node] for node in row["nodes"]] for row in value["geometries"]}


def _supported_indices(nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray,np.ndarray]:
    xmin=min(node[0] for node in nodes); fixed=[]
    for index,node in enumerate(nodes):
        if abs(node[0]-xmin) <= 1e-12:
            fixed.extend(6*index+component for component in range(5))
    all_indices=np.arange(6*len(nodes)); free=np.setdiff1d(all_indices,np.array(fixed,dtype=int))
    return np.array(fixed,dtype=int),free


def _solve_strip(divisions: int, thickness: float) -> dict[str,float]:
    width=0.1
    nodes=[(index/divisions,y,0.0) for y in (0.0,width) for index in range(divisions+1)]
    stride=divisions+1
    elements=[(index,index+1,stride+index+1,stride+index) for index in range(divisions)]
    matrices=_assemble(nodes,elements,thickness); _,free=_supported_indices(nodes)
    force=np.zeros(6*len(nodes)); right=[i for i,node in enumerate(nodes) if abs(node[0]-1)<1e-12]
    for index in right: force[6*index+2]=1/len(right)
    k=matrices["total"][np.ix_(free,free)]; q=np.zeros_like(force)
    q[free]=linalg.solve(k,force[free],assume_a="sym")
    displacement=float(np.mean([q[6*i+2] for i in right])); reference=1/(15*(width*thickness**3/12)*3)
    core=float(q@matrices["core"]@q/2); pl=float(q@matrices["pl"]@q/2); hg=float(q@matrices["hg"]@q/2)
    return {"displacement":displacement,"reference":reference,"relative_error":abs(displacement/reference-1),"response_ratio":abs(displacement/reference),"numerical_fraction":abs((pl+hg)/core) if core else math.inf,"drill_participation":float(np.linalg.norm(q[5::6])/max(1.,np.linalg.norm(q)))}


def assembled_stability(repository_root: Path) -> dict[str,Any]:
    geometries=_geometry_nodes(repository_root); rows=[]; certified_failure=False
    for family,geometry_id in common.GEOMETRY_MAP.items():
        for level in common.REFINEMENTS:
            nodes,elements=common.uniform_mesh(geometries[geometry_id],level); matrices=_assemble(nodes,elements,2/3); _,free=_supported_indices(nodes)
            reduced=matrices["total"][np.ix_(free,free)]; symmetry=float(np.linalg.norm(reduced-reduced.T,ord=np.inf)/max(1.,np.linalg.norm(reduced,ord=np.inf)))
            minimum=float(np.linalg.eigvalsh((reduced+reduced.T)/2)[0])
            if symmetry > 1e-12 or minimum < -1e-9: certified_failure=True
            rows.append({"family":family,"level":level,"elements":len(elements),"nodes":len(nodes),"minimum_supported_eigenvalue":common.Bound.around(minimum,reduced.size).record(),"symmetry_error":common.Bound.around(symmetry,reduced.size).record()})
    return {"rows":rows,"certified_failure":certified_failure,"domain_certificate":{"alpha_star":"1e-6","branch_count":0,"status":"UNRESOLVED_NOT_FINITE_SAMPLE_SUBSTITUTION"}}


def locking_refinement() -> dict[str,Any]:
    rows=[]; certified_failure=False
    for division in common.LOCKING_DIVISIONS:
        for token in common.THICKNESS_RATIOS:
            value=_solve_strip(division,float(token)); row={"division":division,"thickness_ratio":token}
            row.update({key:common.Bound.around(metric,division*division).record() for key,metric in value.items()})
            rows.append(row)
    # Numeric benchmark failures are classification-authoritative only when a
    # conservative enclosure lies wholly beyond a frozen threshold.
    for row in rows:
        if common.Bound.from_record(row["relative_error"]).lo > 2e-2: certified_failure=True
    return {"rows":rows,"certified_failure":certified_failure}


def nonintrusion(repository_root: Path) -> dict[str,Any]:
    geometries=_geometry_nodes(repository_root); rows=[]; certified_failure=False
    for family,geometry_id in common.GEOMETRY_MAP.items():
        nodes,elements=common.uniform_mesh(geometries[geometry_id],2); matrices=_assemble(nodes,elements,2/3)
        q=np.array([((index*17)%23-11)/23 for index in range(6*len(nodes))],dtype=float)
        r_phys=matrices["core"]@q; r_pl=matrices["pl"]@q; r_hg=matrices["hg"]@q; r_total=matrices["total"]@q
        split=float(np.linalg.norm(r_total-r_phys-r_pl-r_hg,ord=np.inf))
        # Physical core has no drill columns/rows by construction.
        physical_drill=float(np.linalg.norm(r_phys[5::6],ord=np.inf))
        if split > 1e-10 or physical_drill > 1e-10: certified_failure=True
        rows.append({"family":family,"reaction_split_error":common.Bound.around(split,len(q)).record(),"physical_drill_contamination":common.Bound.around(physical_drill,len(q)).record(),"numerical_reactions_reported_separately":True})
    return {"rows":rows,"certified_failure":certified_failure}


def produce(repository_root: Path, shard: str, cycle: int) -> dict[str,Any]:
    if shard not in common.SHARDS or cycle not in (1,2): raise common.Q1BError("invalid shard or cycle")
    payload = assembled_stability(repository_root) if shard==common.SHARDS[0] else locking_refinement() if shard==common.SHARDS[1] else nonintrusion(repository_root)
    record={"candidate_id":common.CANDIDATE_ID,"coverage":payload,"cycle":cycle,"implementation_id":IMPLEMENTATION_ID,"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","schema":common.SHARD_SCHEMA,"shard":shard,"study_id":common.STUDY_ID}
    record["payload_sha256"]=common.sha256(common.canonical_bytes(payload))
    return record


def _tower_scalar(field: Mapping[str,Any], token: Sequence[str]) -> float:
    roots=[]
    for index,coefficients in enumerate(field["radicands"]):
        basis=[]
        for mask in range(1<<index):
            value=1.0
            for root_index,root in enumerate(roots):
                if mask&(1<<root_index): value*=root
            basis.append(value)
        radicand=sum(float(Fraction(value))*basis[i] for i,value in enumerate(coefficients))
        roots.append(math.sqrt(radicand))
    basis=[]
    for mask in range(1<<len(roots)):
        value=1.0
        for index,root in enumerate(roots):
            if mask&(1<<index): value*=root
        basis.append(value)
    return sum(float(Fraction(value))*basis[i] for i,value in enumerate(token))


def commission(repository_root: Path, evidence_root: Path) -> dict[str,Any]:
    contract=json.loads((repository_root/"docs/reference_cases/e4_pl_q1y3_local_algebra_contract.json").read_text(encoding="utf-8")); geometries=_geometry_nodes(repository_root); rows=[]
    expected={row["name"]:(row["bytes"],row["sha256"]) for row in contract["diagnostic_proofs"]}
    for geometry_id in common.GEOMETRY_IDS:
        path=evidence_root/f"{geometry_id}.proof.json"; size,digest=expected[path.name]; raw=common.verify_file(path,bytes_count=size,digest=digest); wrapper=json.loads(raw); proof=wrapper["proof"]
        exact=np.array([[_tower_scalar(proof["field"],token) for token in row] for row in proof["base"]["k_total"]])
        observed=np.asarray(local_components(geometries[geometry_id],2/3)["local_total"]); error=float(np.linalg.norm(observed-exact,ord=np.inf)); scale=max(1.,float(np.linalg.norm(exact,ord=np.inf)))
        rows.append({"geometry_id":geometry_id,"proof_bytes":size,"proof_sha256":digest,"relative_infinity_error":common.Bound.around(error/scale,24*24).record(),"within_enclosure":error/scale<=5e-12})
    return {"all_equivalent":all(row["within_enclosure"] for row in rows),"classification":"EXACT_EQUIVALENCE_COMMISSIONING_INPUT","rows":rows,"schema":"anysolver.s4.e4-pl-q1b-equivalence-commissioning-v1"}


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(); parser.add_argument("--repository-root",type=Path,required=True); parser.add_argument("--output",type=Path)
    group=parser.add_mutually_exclusive_group(required=True); group.add_argument("--run-shard",action="store_true"); group.add_argument("--commission",action="store_true"); group.add_argument("--authority-check-only",action="store_true")
    parser.add_argument("--shard",choices=common.SHARDS); parser.add_argument("--cycle",type=int); parser.add_argument("--q1y3-evidence-root",type=Path)
    parser.add_argument("--contract",type=Path); parser.add_argument("--contract-sha256"); parser.add_argument("--authority",type=Path); parser.add_argument("--authority-sha256")
    return parser


def main(argv: Sequence[str]|None=None) -> int:
    args=_parser().parse_args(argv)
    try:
        if args.commission:
            value=commission(args.repository_root,args.q1y3_evidence_root)
        else:
            common.validate_execution_authority(repository_root=args.repository_root,contract_path=args.contract,contract_sha256=args.contract_sha256,authority_path=args.authority,authority_sha256=args.authority_sha256,runner_id=RUNNER_ID)
            if args.authority_check_only:
                print(common.canonical_bytes({"runner_id":RUNNER_ID,"status":"PASS"}).decode(),end=""); return 0
            value=produce(args.repository_root,args.shard,args.cycle)
        if args.output is None: raise common.Q1BError("output is required")
        common.write_exclusive(args.output,value); return 0
    except (OSError,ValueError,np.linalg.LinAlgError,common.Q1BError) as exc:
        print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
