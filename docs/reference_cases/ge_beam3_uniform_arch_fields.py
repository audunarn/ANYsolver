"""Continuum section fields in the fixed physical axis-2/global-z convention.

No producer import. Samples are exact requested BVP evaluation sites, not an
interpolation of saved output. Reflection is across the crown plane.
"""
import numpy as np
from .ge_beam3_uniform_arch_reference import Reference,AXIAL,SHEAR,BENDING,primitive


def fields(reference,parameters):
    if type(reference) is not Reference:raise ValueError('exact resolved continuum record')
    x=np.asarray(parameters,dtype=float)
    if x.ndim!=1 or not np.isfinite(x).all() or np.any(np.abs(x)>1.):raise ValueError('arch station domain')
    selected=[]
    for value in -np.abs(x):
        matches=np.flatnonzero(reference.sites==value)
        if len(matches)!=1:raise ValueError('continuum station was not sampled exactly')
        selected.append(int(matches[0]))
    y=reference.fields[:,selected];side=np.where(x<=0.,1.,-1.);theta=side*y[2]
    c,s=np.cos(theta),np.sin(theta);nx=AXIAL*reference.parameters[0];ny=reference.density*primitive(x)
    n,v=nx*c+ny*s,-nx*s+ny*c;m=AXIAL*y[3]
    resultants=np.column_stack((n,np.zeros_like(x),-v,np.zeros_like(x),m,np.zeros_like(x)))
    strain=resultants/np.array([AXIAL,SHEAR,SHEAR,1.,BENDING,BENDING])
    frame=np.zeros((len(x),3,3));frame[:,0,0]=c;frame[:,1,0]=s;frame[:,2,1]=1.;frame[:,0,2]=s;frame[:,1,2]=-c
    position=np.column_stack((side*y[0],y[1],np.zeros_like(x)))
    global_resultants=np.column_stack((np.einsum('nij,nj->ni',frame,resultants[:,:3]),np.einsum('nij,nj->ni',frame,resultants[:,3:])))
    return dict(parameters=x,position=position,frame=frame,strain=strain,resultants=resultants,global_resultants=global_resultants,
        production_qualified=False)
