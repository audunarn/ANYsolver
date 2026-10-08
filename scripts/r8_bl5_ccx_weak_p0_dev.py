"""Development CalculiX deck for the resolved C3D20 BL5 weak-P0 law.

The 20 physical mortar rows are row-reduced only for CalculiX *EQUATION
elimination. The original rows, their measures, and the continuum bodies
remain unchanged. This bridge does not qualify the native BL5 connection.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

import numpy as np
from scripts import r8_bl5_released_director_reference as solid
from scripts import r8_bl5_weak_continuum_reference as weak

IDENTITY = "R8_BL5_CCX_WEAK_P0_REFERENCE_DEV_V1"
LOADS = {"fy": (100., 0.), "mx": (0., 10.)}  # N, Nm
ABS_ROW_FLOOR = 1e-14


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weak_equations(model):
    """Exact row-space change with unique, non-SPC, beam-side pivot DOFs."""
    c_sparse, measure = weak.constraints(model, "weak")
    c = c_sparse.toarray()
    order, index, fixed, _, _ = weak.layout(model)
    # Four independent material sections, each with bottom xyz and top xy.
    # The x=1 end remains independent so consistent tip loads never act on
    # an eliminated CalculiX variable. This physical block is full rank.
    dependent = np.array([
        index[station[node]]+axis
        for station in model["stations"][:4]
        for node, axes in (("beam_bottom",range(3)),("beam_top",range(2)))
        for axis in axes],dtype=int)
    a = c[:, dependent]
    condition = float(np.linalg.cond(a))
    if (c.shape != (20, 3*len(order)) or measure.shape != (20,) or
            np.any(measure <= 0) or len(set(dependent)) != 20 or
            any(slot in fixed for slot in dependent) or
            not np.isfinite(condition) or condition > 1e10):
        raise ValueError("independent, conditioned, non-SPC weak pivots required")
    equations = np.linalg.solve(a, c)
    equations[:, dependent] = np.eye(20)
    equations[np.abs(equations) < ABS_ROW_FLOOR] = 0.
    # Verify the coefficients CalculiX actually reads, not only the binary64
    # array before decimal serialization. Its first variable is eliminated.
    serialized = np.array([[float(f"{value:.17g}") for value in row]
                           for row in equations])
    retained = a @ serialized
    row_error = float(np.linalg.norm(retained-c,ord=np.inf)/
                      max(np.linalg.norm(c,ord=np.inf),1e-30))
    pivot_error = float(np.max(np.abs(serialized[:, dependent]-np.eye(20))))
    if row_error > 1e-11 or pivot_error != 0.:
        raise ValueError("CalculiX row reduction changed physical weak space")
    return serialized,dependent,dict(condition=condition,row_relative_error=row_error,
        pivot_error=pivot_error,physical_rows=20,dependent_slots=dependent.tolist(),
        physical_pivot_matrix=a.tolist(),
        original_row_measures=measure.tolist(),
        physical_multiplier_from_ccx="lambda_physical=A^{-T} lambda_equation")


def tip_traction(model, case):
    """Consistent surface traction with declared Fy or polar Mx resultant."""
    fy, mx = LOADS[case]
    order, index, _, _, _ = weak.layout(model)
    load = np.zeros(3*len(order))
    points, weights = np.polynomial.legendre.leggauss(3)
    section = model["section"]
    area = float(section["area_m2"])
    polar = float(section["Iy_m4"]+section["Iz_m4"])
    center_z = float(model["geometry_m"]["centroid_z"])
    chosen = []
    for eid in model["beam_elements"]:
        ids, low, high, center, span = solid._brick(
            model["elements"][eid],model["physical_nodes"])
        if abs(high[0]-1.) > 1e-14:
            continue
        chosen.append(eid)
        for iy, iz in itertools.product(range(3),repeat=2):
            eta, zeta = points[iy], points[iz]
            shape, _ = solid._shape((1.,eta,zeta))
            y = center[1]+.5*span[1]*eta
            z = center[2]+.5*span[2]*zeta
            traction = np.array((0., fy/area-mx*(z-center_z)/polar,
                                 mx*y/polar))
            da = .25*span[1]*span[2]*weights[iy]*weights[iz]
            for node, value in zip(ids,shape):
                load[index[node]:index[node]+3] += value*traction*da
    if len(chosen) != 2 or not np.isfinite(load).all():
        raise ValueError("two finite complete tip faces required")
    # Symmetric quadrature leaves roundoff-scale components on the polar
    # traction. CalculiX rejects such near-zero *CLOAD cards outright.
    load[np.abs(load) < 1e-12] = 0.
    tip_nodes = {node for node in model["beam_nodes"]
                 if abs(model["physical_nodes"][node][0]-1.) <= 1e-14}
    outside = [index[node]+axis for node in order if node not in tip_nodes
               for axis in range(3)]
    if np.max(abs(load[outside]),initial=0.) > 1e-12:
        raise ValueError("tip traction leaked outside physical end face")
    local_center = np.array((1.,0.,center_z))
    force = np.zeros(3)
    moment = np.zeros(3)
    for node in tip_nodes:
        vector = load[index[node]:index[node]+3]
        force += vector
        moment += np.cross(np.asarray(model["physical_nodes"][node])-local_center,
                           vector)
    target = np.array((0.,fy,0.,mx,0.,0.))
    wrench = np.r_[force,moment]
    if np.max(abs(wrench-target)) > 1e-10*max(abs(fy),abs(mx),1.):
        raise ValueError("tip traction resultant differs from declared action")
    return load,dict(case=case,force_N=force.tolist(),
                     moment_about_beam_tip_Nm=moment.tolist(),
                     selected_faces=chosen,load_nnz=int(np.count_nonzero(load)))


def deck(case):
    if case not in LOADS:
        raise ValueError("admitted Fy or Mx action required")
    _, model = solid.build_reference()
    equations, dependent, map_check = weak_equations(model)
    load, load_check = tip_traction(model,case)
    order, index, fixed, _, _ = weak.layout(model)
    lines = ["*HEADING",IDENTITY+" "+case+"; development only","*NODE"]
    lines += [str(node)+","+",".join(format(v,".17g") for v in xyz)
              for node,xyz in model["physical_nodes"].items()]
    lines += ["*ELEMENT,TYPE=C3D20,ELSET=BODY"]
    for eid,ids in model["elements"].items():
        lines += [str(eid)+","+",".join(map(str,ids[:15])),
                  ",".join(map(str,ids[15:]))]
    for name,nodes in (("ALL",sorted(model["physical_nodes"])),
                       ("ROOT",model["root_nodes"])):
        lines.append("*NSET,NSET="+name)
        lines += [",".join(map(str,nodes[j:j+16]))
                  for j in range(0,len(nodes),16)]
    lines += ["*MATERIAL,NAME=ELASTIC","*ELASTIC",
              f"{solid.E:.17g},{solid.NU:.17g}",
              "*SOLID SECTION,ELSET=BODY,MATERIAL=ELASTIC",
              "*BOUNDARY","ROOT,1,3,0."]
    for row, pivot in zip(equations,dependent):
        slots = [int(pivot)]+[j for j,value in enumerate(row)
                              if j != pivot and value != 0.]
        terms = [f"{order[slot//3]},{slot%3+1},{row[slot]:.17g}"
                 for slot in slots]
        lines += ["*EQUATION",str(len(terms))]
        lines += [",".join(terms[j:j+3]) for j in range(0,len(terms),3)]
    lines += ["*STEP","*STATIC","1.,1.","*CLOAD"]
    lines += [f"{order[slot//3]},{slot%3+1},{value:.17g}"
              for slot,value in enumerate(load) if value != 0.]
    lines += ["*NODE OUTPUT,DOUBLE,NSET=ALL","U",
              "*NODE OUTPUT,DOUBLE,NSET=ROOT","RF","*END STEP"]
    output = "\n".join(lines)+"\n"
    meta = dict(identity=IDENTITY,status="PREPARED_NOT_EXECUTED",
        case=case,model_sha256=model["model_sha256"],
        source_sha256={"solid":sha(solid.__file__),"weak":sha(weak.__file__)},
        physical_nodes=model["physical_nodes"],elements=model["elements"],
        root_nodes=model["root_nodes"],beam_nodes=model["beam_nodes"],
        beam_elements=model["beam_elements"],dependent_pivots=[
            (int(order[slot//3]),int(slot%3+1)) for slot in dependent],
        equation_check=map_check,tip_load_check=load_check,
        physical_tip_load_N=load.tolist(),
        deck_sha256=hashlib.sha256(output.encode("ascii")).hexdigest(),
        interpretation="same resolved C3D20 bodies and original 20 weak P0 rows; row-reduced equation representation; not native accuracy")
    return output.encode("ascii"),meta


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",choices=sorted(LOADS),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    data,metadata=deck(args.case)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"weak.inp").write_bytes(data)
    (args.output/"metadata.json").write_text(
        json.dumps(metadata,indent=2,allow_nan=False)+"\n",encoding="utf-8")
