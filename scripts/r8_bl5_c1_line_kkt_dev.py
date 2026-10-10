"""Independently parse and solve the prepared C1 C3D20R hinge decks.

The reduced-integration solid KKT is a development parity oracle for the
serialized equations. It is not an E4-PL/native BL5 qualification result.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts.r8_bl5_released_director_reference import _elastic_matrix
from scripts.r8_e02_distributing_solid_area import _shape


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _block(lines: list[str], header: str) -> list[str]:
    start = lines.index(header)+1
    end = next(j for j in range(start,len(lines)) if lines[j].startswith("*"))
    return lines[start:end]


def _read(path: Path) -> dict:
    lines = path.read_text(encoding="ascii").splitlines()
    nodes = {}
    for line in _block(lines,"*NODE,NSET=AllNodes"):
        values = line.split(",")
        nodes[int(values[0])] = np.array([float(v) for v in values[1:]])
    elements, domains = {}, {}
    for name in ("Plate","Stiffener"):
        values = [int(v) for line in _block(lines,f"*ELEMENT,TYPE=C3D20R,ELSET={name}")
                  for v in line.split(",") if v]
        if len(values)%21:
            raise ValueError("incomplete quadratic solid element")
        these = {values[j]: tuple(values[j+1:j+21]) for j in range(0,len(values),21)}
        elements.update(these)
        domains[name] = {n for ids in these.values() for n in ids}
    if domains["Plate"] & domains["Stiffener"] or set(nodes)!=domains["Plate"]|domains["Stiffener"]:
        raise ValueError("physical domains share nodes or omit nodes")
    supports = {int(v) for line in _block(lines,"*NSET,NSET=Supports")
                for v in line.split(",") if v}
    equations = []
    j = 0
    while j < len(lines):
        if lines[j] != "*EQUATION":
            j += 1
            continue
        count = int(lines[j+1]); j += 2
        tokens = []
        while len(tokens) < 3*count:
            if lines[j].startswith("*"):
                raise ValueError("truncated serialized constraint equation")
            tokens.extend(v for v in lines[j].split(",") if v)
            j += 1
        if len(tokens)!=3*count:
            raise ValueError("extra serialized constraint coefficient")
        row = []
        for k in range(0,len(tokens),3):
            row.append((int(tokens[k]),int(tokens[k+1]),float(tokens[k+2])))
        equations.append(row)
    loads = {}
    for line in _block(lines,"*CLOAD"):
        n, axis, value = line.split(",")
        loads[(int(n),int(axis))] = loads.get((int(n),int(axis)),0.)+float(value)
    return {"nodes":nodes,"elements":elements,"domains":domains,
            "supports":supports,"equations":equations,"loads":loads}


def _wrench(xyz: np.ndarray, action: np.ndarray) -> np.ndarray:
    f = action.reshape(-1,3)
    return np.r_[np.sum(f,axis=0),np.sum(np.cross(xyz,f),axis=0)]


def _assemble(model: dict) -> tuple[sparse.csc_matrix,tuple[int,...],dict[int,int],dict]:
    order = tuple(sorted(model["nodes"]))
    index = {n:3*j for j,n in enumerate(order)}
    count = len(model["elements"])
    values = np.empty(count*3600)
    row = np.empty(count*3600,dtype=np.int32)
    col = np.empty(count*3600,dtype=np.int32)
    elastic = _elastic_matrix()
    gauss, weights = np.polynomial.legendre.leggauss(2)
    points = [(np.array([gauss[i] for i in ijk]),
               float(np.prod([weights[i] for i in ijk])))
              for ijk in itertools.product(range(2),repeat=3)]
    gradients = [(_shape(xi)[1],weight) for xi,weight in points]
    minimum_jacobian = float("inf")
    maximum_jacobian = 0.
    for e,(eid,ids) in enumerate(sorted(model["elements"].items())):
        coords = np.array([model["nodes"][n] for n in ids])
        ke = np.zeros((60,60))
        for grad,weight in gradients:
            jacobian = coords.T@grad
            determinant = float(np.linalg.det(jacobian))
            if not np.isfinite(determinant) or determinant<=0.:
                raise ValueError(f"nonpositive solid Jacobian at element {eid}")
            minimum_jacobian = min(minimum_jacobian,determinant)
            maximum_jacobian = max(maximum_jacobian,determinant)
            physical = np.linalg.solve(jacobian.T,grad.T).T
            b = np.zeros((6,60))
            for j,(gx,gy,gz) in enumerate(physical):
                b[:,3*j:3*j+3] = ((gx,0,0),(0,gy,0),(0,0,gz),
                                   (gy,gx,0),(0,gz,gy),(gz,0,gx))
            ke += (b.T@elastic@b)*(determinant*weight)
        slots = np.array([index[n]+j for n in ids for j in range(3)],dtype=np.int32)
        start = e*3600; end = start+3600
        row[start:end] = np.repeat(slots,60)
        col[start:end] = np.tile(slots,60)
        values[start:end] = ke.ravel()
    total = 3*len(order)
    stiffness = sparse.coo_matrix((values,(row,col)),shape=(total,total)).tocsc()
    stiffness.sum_duplicates()
    return stiffness,order,index,{"elements":count,"min_jacobian":minimum_jacobian,
                                   "max_jacobian":maximum_jacobian,
                                   "stiffness_nnz":stiffness.nnz}


def evaluate(folder: Path) -> dict:
    metadata_path = folder/"metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata["status"]!="PREPARED_NOT_EXECUTED_NOT_QUALIFIED" or metadata["physical_dofs"]>100_000:
        raise ValueError("prepared bounded model identity required")
    models = {name:_read(folder/f"{name}.inp") for name in ("fy","mx")}
    for name,model in models.items():
        if _sha(folder/f"{name}.inp")!=metadata["cases"][name]["deck_sha256"]:
            raise ValueError("prepared deck hash differs from registered input")
    first = models["fy"]
    second = models["mx"]
    if (first["nodes"].keys()!=second["nodes"].keys() or
            first["elements"]!=second["elements"] or
            first["supports"]!=second["supports"] or
            first["equations"]!=second["equations"] or
            any(np.max(np.abs(first["nodes"][n]-second["nodes"][n]))>0
                for n in first["nodes"])):
        raise ValueError("Fy/Mx decks do not share the exact physical operator")
    started = time.perf_counter()
    k,order,index,assembly = _assemble(first)
    size = k.shape[0]
    ci,cj,cv = [],[],[]
    dependent=[]
    for i,terms in enumerate(first["equations"]):
        if len(terms)<2:
            raise ValueError("incomplete mixed equation")
        pivot = index[terms[0][0]]+terms[0][1]-1
        dependent.append(pivot)
        for n,axis,value in terms:
            if axis not in (1,2,3):
                raise ValueError("invalid solid displacement DOF")
            ci.append(i); cj.append(index[n]+axis-1); cv.append(value)
    if len(set(dependent))!=25 or len(dependent)!=25:
        raise ValueError("expected 25 unique dependent physical DOFs")
    c = sparse.coo_matrix((cv,(ci,cj)),shape=(len(dependent),size)).tocsc()
    if np.max(abs(c[:,dependent].toarray()-np.eye(25)))>1e-12:
        raise ValueError("serialized pivot matrix is not isolated identity")
    fixed = np.array([index[n]+j for n in sorted(first["supports"]) for j in range(3)])
    if len(fixed)!=726 or any(p in fixed for p in dependent):
        raise ValueError("support inventory or equation pivot changed")
    free = np.setdiff1d(np.arange(size),fixed)
    positions = np.array([first["nodes"][n] for n in order])
    rigid_gaps=[]
    for axis in range(6):
        field = np.tile(np.eye(3)[axis],(len(order),1)) if axis<3 else np.cross(
            np.eye(3)[axis-3],positions)
        rigid_gaps.append(float(np.max(abs(c@field.ravel()))))
    if max(rigid_gaps)>1e-11:
        raise ValueError("serialized line equations violate common rigid motions")
    loads = np.zeros((size,2))
    for j,name in enumerate(("fy","mx")):
        for (n,axis),value in models[name]["loads"].items():
            loads[index[n]+axis-1,j] += value
    kff = k[free,:][:,free]
    cf = c[:,free]
    diagonal = kff.diagonal()
    if np.min(diagonal)<=0 or not np.isfinite(diagonal).all():
        raise ValueError("invalid physical stiffness diagonal")
    dq = 1./np.sqrt(diagonal)
    dl = 1./np.sqrt(np.asarray((cf@sparse.diags(dq)).power(2).sum(axis=1)).ravel())
    if not np.isfinite(dl).all():
        raise ValueError("invalid dual equation scaling")
    dp,dm = sparse.diags(dq),sparse.diags(dl)
    system = sparse.bmat([[dp@kff@dp,dp@cf.T@dm],[dm@cf@dp,None]],format="csc")
    rhs = np.vstack((dq[:,None]*loads[free,:],np.zeros((25,2))))
    factor = splu(system)
    solution = factor.solve(rhs)
    for _ in range(3):
        solution += factor.solve(rhs-system@solution)
    displacement = np.zeros_like(loads)
    displacement[free,:] = dq[:,None]*solution[:len(free),:]
    multiplier = dl[:,None]*solution[len(free):,:]
    cases={}
    for j,name in enumerate(("fy","mx")):
        q=displacement[:,j]; lam=multiplier[:,j]; load=loads[:,j]
        internal=np.asarray(k@q).ravel()
        interface=np.asarray(c.T@lam).ravel()
        residual=internal+interface-load
        support=np.zeros(size);support[fixed]=residual[fixed]
        work=float(load@q)
        gaps=np.asarray(c@q).ravel()
        load_wrench=_wrench(positions,load)
        support_wrench=_wrench(positions,support)
        interface_wrench=_wrench(positions,interface)
        checks={"free_equilibrium":float(np.max(abs(residual[free]))/100.),
                "equation_gap_m":float(np.max(abs(gaps))),
                "energy_work":abs(float(q@internal)-work)/max(abs(work),1e-12),
                "constraint_work":abs(float(q@interface))/max(abs(work),1e-12),
                "global_force_balance":float(np.max(abs((load_wrench+support_wrench)[:3]))/100.),
                "global_moment_balance":float(np.max(abs((load_wrench+support_wrench)[3:]))/100.),
                "interface_force_balance":float(np.max(abs(interface_wrench[:3]))/100.),
                "interface_moment_balance":float(np.max(abs(interface_wrench[3:]))/100.)}
        limit={key:(1e-9 if "gap" in key else 1e-8) for key in checks}
        if any(not np.isfinite(v) or v>limit[key] for key,v in checks.items()):
            raise ValueError(f"{name} KKT parity checks failed: {checks}")
        cases[name]={"applied_work_J":work,"load_wrench":load_wrench.tolist(),
                     "support_wrench":support_wrench.tolist(),
                     "interface_wrench":interface_wrench.tolist(),
                     "max_displacement_m":float(np.max(abs(q))),"checks":checks,
                     "limits":limit}
    cross=loads.T@displacement
    reciprocity=float(abs(cross[0,1]-cross[1,0])/max(np.linalg.norm(cross),1e-12))
    if reciprocity>1e-8:
        raise ValueError("same-operator Fy/Mx reciprocity failure")
    return {"identity":"R8_BL5_C1_DETACHED_F2_KKT_PARITY_DEV_V1",
            "status":"INDEPENDENT_KKT_ONLY_NOT_QUALIFIED",
            "source_sha256":_sha(Path(__file__)),
            "prepared_metadata_sha256":_sha(metadata_path),
            "prepared_decks":{n:_sha(folder/f"{n}.inp") for n in ("fy","mx")},
            "physical_dofs":size,"supported_dofs":len(fixed),
            "physical_constraint_rows":c.shape[0],
            "kkt_nnz":system.nnz,"assembly":assembly,
            "rigid_gap_by_mode":rigid_gaps,
            "cases":cases,"cross_work_matrix_J":cross.tolist(),
            "reciprocity":reciprocity,
            "wall_seconds_internal":time.perf_counter()-started,
            "limitation":"single factor-2 reduced-integration solid KKT; no external or native response parity, mesh convergence or F03"}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--prepared",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve earlier KKT attempt")
    result=evaluate(args.prepared)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"assembly":result["assembly"],
                      "work":{n:v["applied_work_J"] for n,v in result["cases"].items()},
                      "checks":{n:v["checks"] for n,v in result["cases"].items()},
                      "wall_seconds_internal":result["wall_seconds_internal"]}))


if __name__=="__main__":
    main()
