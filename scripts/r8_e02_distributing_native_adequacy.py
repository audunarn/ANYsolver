"""ONE new native80x32 adequacy model; historical geometry admission unchanged.

The 40x16 form exists only to prove exact fixture parity before the new solve.
No general refinement sequence, solid refinement or asymptotic certificate.
"""
from .r8_e02_distributing_feasibility import _native_load_cases


def geometry(nx,ny):
    if (nx,ny) not in ((40,16),(80,32)):
        raise ValueError('only parity40x16 or new bounded80x32 model admitted')
    nodes={1+j*(nx+1)+i:(i/nx,-.1+.2*j/ny,0.)
           for j in range(ny+1) for i in range(nx+1)}
    cells=[];patch=[]
    for j in range(ny):
        for i in range(nx):
            a=1+j*(nx+1)+i;cell=(a,a+1,a+nx+2,a+nx+1)
            cells.append(cell)
            if 5*i>=4*nx:patch.append(cell)
    patch_nodes=tuple(sorted({n for cell in patch for n in cell}))
    root=tuple(1+j*(nx+1) for j in range(ny+1))
    if 6*len(nodes)+42+6>100000:
        raise ValueError('native model row guard exceeded')
    return nodes,tuple(cells),tuple(patch),patch_nodes,root


def native_case():
    return _native_load_cases(80,32,{'Mx':(0.,0.,0.,1.,0.,0.),
        'My':(0.,0.,0.,0.,1.,0.)},geometry_builder=geometry)
