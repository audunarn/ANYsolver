"""G0 F03-P-v3: explicit physical support force and moment balance."""

from __future__ import annotations

import json

import numpy as np
from scipy.sparse.linalg import spsolve

import probe_b3_ge_e4_pl_g0_physical_line as prior


def reactions(n, topology, gradient):
    xs, ys, positions, k, _ = prior.mesh_stiffness(n, topology)
    force = np.zeros(2*len(positions))
    roots, quadrature = np.polynomial.legendre.leggauss(4)
    breaks = sorted({-.4,.4} | {float(np.round(x-shift,14))
        for x in xs for shift in (-.2,.2) if -.4 < x-shift < .4})
    for start,end in zip(breaks[:-1],breaks[1:]):
        for root,weight in zip(roots,quadrature):
            s = float((start+end)/2.+(end-start)*root/2.)
            measure = float((end-start)*weight/2.)
            for sample,(dx,y) in enumerate(((-.2,-.25),(.2,-.25),
                                            (.2,.25),(-.2,.25))):
                for node,shape in prior.host_weights(s+dx,y,xs,ys,topology):
                    force[2*node:2*node+2] += measure*shape*gradient[sample,:2]
    fixed = np.array([2*(j*(n+1)+i)+axis for j in range(n+1) for i in range(n+1)
                      if i in (0,n) or j in (0,n) for axis in (0,1)],dtype=int)
    free = np.array(sorted(set(range(len(force)))-set(fixed)),dtype=int)
    displacement = np.zeros_like(force)
    displacement[free] = spsolve(k[free,:][:,free].tocsc(),force[free])
    residual = k@displacement-force
    support = np.zeros_like(force)
    support[fixed] = residual[fixed]
    total_force = float(np.linalg.norm((support+force).reshape(-1,2).sum(axis=0)))
    reaction_moment = float(np.sum(positions[:,0]*support[1::2]-positions[:,1]*support[0::2]))
    applied_moment = float(np.sum(positions[:,0]*force[1::2]-positions[:,1]*force[0::2]))
    free_residual = float(np.linalg.norm(residual[free])/max(1.,np.linalg.norm(force)))
    work = float(force@displacement)
    twice_energy = float(displacement@(k@displacement))
    relative_work = abs(work-twice_energy)/max(abs(work),abs(twice_energy),1e-30)
    assert (total_force<=1e-8 and abs(reaction_moment-.8)<=1e-8
            and abs(reaction_moment+applied_moment)<=1e-8
            and free_residual<=1e-8 and relative_work<=1e-8)
    return dict(support_force_balance=total_force,support_moment=reaction_moment,
                applied_moment=applied_moment,free_residual=free_residual,
                relative_work_error=relative_work,compliance=work)


if __name__ == "__main__":
    gradient = prior.line_samples()
    rows = []
    for topology in ("Q4","S3-V2D"):
        for n in (4,8,16):
            row = prior.specimen(n,topology,gradient)
            checked = reactions(n,topology,gradient)
            assert row["status"] == "diagnostic_pass"
            assert abs(row["compliance"]-checked["compliance"])/checked["compliance"] <= 1e-12
            row.update({k:v for k,v in checked.items() if k!="compliance"})
            rows.append(row)
    print(json.dumps(dict(profile="G0-F03-P-v3",status="diagnostic_pass",results=rows),
                     sort_keys=True))
