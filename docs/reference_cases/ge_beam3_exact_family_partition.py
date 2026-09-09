"""Research-only structural-zero partition of an original signed factor chain.

No small-entry threshold, matrix expansion, mechanics change or general coupled
beam claim. Reject any original material/kinetic/geometric cross-family support.
"""
import numpy as np


def partition(packet,nodal_count,check=lambda:None):
    check();left,right,g,b=packet.left,packet.right,packet.geometric,packet.kinetic
    size=right.shape[1]
    if (type(nodal_count) is not int or nodal_count%6 or not 6<=nodal_count<=size<=256
            or (size-nodal_count)%6 or g.shape!=(size,size) or b.shape[1]!=size
            or left.shape[1]!=right.shape[0]
            or not all(np.isfinite(x).all() for x in (left,right,g,b))):
        raise ValueError('bounded complete nodal/cell factor layout required')
    groups={'axial':[],'torsion':[],'bend-y':[],'bend-z':[]}
    for start in range(0,nodal_count,6):
        groups['axial'].append(start);groups['torsion'].append(start+3)
        groups['bend-y'].extend((start+1,start+5));groups['bend-z'].extend((start+2,start+4))
    for start in range(nodal_count,size,3):
        groups['torsion'].append(start);groups['bend-y'].append(start+2);groups['bend-z'].append(start+1)
    ownership=np.empty(size,dtype=int);indicators=[]
    for index,columns in enumerate(groups.values()):
        ownership[columns]=index;indicators.append(np.any(right[:,columns]!=0.,axis=1))
    right_support=np.array(indicators,dtype=np.int64).T
    material_support=(left!=0.).astype(np.int64)@right_support
    if np.any(np.count_nonzero(material_support,axis=1)>1):
        raise ValueError('material factors couple coordinate families')
    kinetic_support=np.array([np.any(b[:,columns]!=0.,axis=1) for columns in groups.values()]).T
    if np.any(np.count_nonzero(kinetic_support,axis=1)>1):
        raise ValueError('kinetic factors couple coordinate families')
    if np.any(g[ownership[:,None]!=ownership[None,:]]!=0.):
        raise ValueError('geometric factor couples coordinate families')
    result={}
    for name,columns in groups.items():
        columns=tuple(sorted(columns));index={col:i for i,col in enumerate(columns)}
        rows=np.flatnonzero(np.any(right[:,columns]!=0.,axis=1))
        outputs=np.flatnonzero(np.any(left[:,rows]!=0.,axis=1))
        velocities=np.flatnonzero(np.any(b[:,columns]!=0.,axis=1))
        if not len(rows) or not len(outputs) or not len(velocities):raise ValueError('empty physical factor family')
        result[name]=dict(columns=columns,left_rows=tuple(map(int,outputs)),right_rows=tuple(map(int,rows)),
            kinetic_rows=tuple(map(int,velocities)),left=left[np.ix_(outputs,rows)],right=right[np.ix_(rows,columns)],
            geometric=g[np.ix_(columns,columns)],kinetic=b[np.ix_(velocities,columns)],
            free=tuple(index[i] for i in packet.free_dofs if i in index),
            algebraic=tuple(index[i] for i in packet.algebraic_dofs if i in index))
    check();return result
