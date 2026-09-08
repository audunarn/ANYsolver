"""Successor original-factor partition; unchanged historical partition remains.

Only exact structural zeros admit separation; each independent audit still has
at most256 coordinates. No rounded Gram matrix is used to identify a family.
"""
import numpy as np


def partition(packet,nodal_count,check=lambda:None):
    check();left,right,g,b=packet.left,packet.right,packet.geometric,packet.kinetic
    size=right.shape[1]
    if type(nodal_count) is not int or nodal_count%6 or not 6<=nodal_count<=size<=512 or (size-nodal_count)%6:
        raise ValueError('complete bounded nodal/cell layout')
    planar=[start+j for start in range(0,nodal_count,6) for j in (0,1,5)]
    planar+=list(range(nodal_count+2,size,3))
    groups=dict(planar=tuple(sorted(planar)),lateral=tuple(i for i in range(size) if i not in planar))
    if any(len(c)>256 for c in groups.values()):raise ValueError('independent family capacity')
    support=np.array([np.any(right[:,c]!=0.,axis=1) for c in groups.values()],dtype=np.int64).T
    if np.any(np.count_nonzero((left!=0.).astype(np.int64)@support,axis=1)>1):
        raise ValueError('material factors couple planar/lateral families')
    if np.any(np.count_nonzero(np.array([np.any(b[:,c]!=0.,axis=1) for c in groups.values()]),axis=0)>1):
        raise ValueError('kinetic factors couple planar/lateral families')
    if np.any(g[np.ix_(groups['planar'],groups['lateral'])]!=0.) or np.any(g[np.ix_(groups['lateral'],groups['planar'])]!=0.):
        raise ValueError('geometric factor couples planar/lateral families')
    made={}
    for name,c in groups.items():
        rows=np.flatnonzero(np.any(right[:,c]!=0.,axis=1));outputs=np.flatnonzero(np.any(left[:,rows]!=0.,axis=1))
        velocities=np.flatnonzero(np.any(b[:,c]!=0.,axis=1));index={j:i for i,j in enumerate(c)}
        made[name]=dict(columns=c,left=left[np.ix_(outputs,rows)],right=right[np.ix_(rows,c)],
            geometric=g[np.ix_(c,c)],kinetic=b[np.ix_(velocities,c)],
            free=tuple(index[j] for j in packet.free_dofs if j in index),
            algebraic=tuple(index[j] for j in packet.algebraic_dofs if j in index))
    check();return made
