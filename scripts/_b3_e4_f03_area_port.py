"""Small, independent finite-area shell pose for F03 mechanics preflight.

Four equal square material pads replace the existing four *point* samples.
This defines a different physical connection, not a repair or qualification
of the four-point reference. Its size must be declared in physical metres,
independently of mesh density and observed response.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import sparse

import _b3_e4_f03_independent_shell as shell


def _clip(polygon: list[tuple[float,float]], axis: int,
          bound: float, direction: int) -> list[tuple[float,float]]:
    """Clip a convex CCW host polygon against direction*(x_axis-bound)>=0."""
    result=[]
    previous=polygon[-1]
    old=direction*(previous[axis]-bound)
    for current in polygon:
        new=direction*(current[axis]-bound)
        if (old>=0)!=(new>=0):
            ratio=old/(old-new)
            result.append(tuple(previous[k]+ratio*(current[k]-previous[k])
                                for k in range(2)))
        if new>=0:
            result.append(current)
        previous,old=current,new
    return result


def _pad_host(model: shell.Panel, element: tuple[int,...],
              bounds: tuple[float,float,float,float]
              ) -> list[tuple[float,float]]:
    polygon=[tuple(map(float,model.nodes[index])) for index in element]
    x0,x1,y0,y1=bounds
    for axis,bound,direction in ((0,x0,1),(0,x1,-1),(1,y0,1),(1,y1,-1)):
        if not polygon:
            break
        polygon=_clip(polygon,axis,bound,direction)
    return polygon


def _quadrature(polygon: list[tuple[float,float]]):
    """Degree-three exact integration on a clipped convex polygon."""
    for index in range(1,len(polygon)-1):
        a,b,c=(np.asarray(polygon[k],dtype=float)
               for k in (0,index,index+1))
        area=abs(float(np.linalg.det(np.column_stack((b-a,c-a)))))/2
        if area==0:
            continue
        barycentric=((-27/48,(1/3,1/3,1/3)),
                     (25/48,(3/5,1/5,1/5)),
                     (25/48,(1/5,3/5,1/5)),
                     (25/48,(1/5,1/5,3/5)))
        for factor,weights in barycentric:
            yield area*factor,weights[0]*a+weights[1]*b+weights[2]*c


def pose(model: shell.Panel, station: float, halfwidth: float
         ) -> sparse.csr_matrix:
    """Centroid translations and physical proper-fit yaw at one station.

    Each pad has area ``4*halfwidth**2`` and contributes one quarter of
    the total average. Q4 bilinear and CST affine shapes multiplied by
    first-order moment arms are integrated exactly on clipped hosts.
    """
    # This *preflight* uses float clipping and 1e-12 line-knot merging.
    # A physical pad smaller than 0.1 mm halfwidth needs another numerical
    # representation; do not silently turn it into a point attachment.
    if (not math.isfinite(station) or not 0<=station<=1 or
            not math.isfinite(halfwidth) or not 1e-4<=halfwidth<=.2):
        raise ValueError("finite material station and fixed physical pad required")
    nx=2*model.n_s
    pad_area=4*halfwidth**2
    inertia=shell.YAW_DENOMINATOR/4+2*halfwidth**2/3
    rows=[]; columns=[]; data=[]
    for dx,dy in shell.OFFSETS:
        x0,x1=station+dx-halfwidth,station+dx+halfwidth
        y0,y1=dy-halfwidth,dy+halfwidth
        if x0<-.5 or x1>1.5 or y0<-.5 or y1>.5:
            raise ValueError("pad crosses outside the selected panel")
        imin=max(0,int(math.floor((x0+.5)*model.n_s)))
        imax=min(nx-1,int(math.floor((x1+.5)*model.n_s)))
        jmin=max(0,int(math.floor((y0+.5)*model.n_y)))
        jmax=min(model.n_y-1,int(math.floor((y1+.5)*model.n_y)))
        covered=0.
        for j in range(jmin,jmax+1):
            for i in range(imin,imax+1):
                cell=j*nx+i
                elements=(model.elements[cell:cell+1] if model.topology=='Q4'
                          else model.elements[2*cell:2*cell+2])
                for element in elements:
                    polygon=_pad_host(model,element,(x0,x1,y0,y1))
                    if len(polygon)<3:
                        continue
                    for area_weight,xy in _quadrature(polygon):
                        covered+=area_weight
                        values,_,_=shell.shape(model.nodes[list(element)],
                                               model.topology,tuple(xy))
                        factor=area_weight/(4*pad_area)
                        rx,ry=xy[0]-station,xy[1]
                        for node,value in zip(element,values):
                            rows.extend((0,1,2,2))
                            columns.extend((2*node,2*node+1,2*node,2*node+1))
                            data.extend((factor*value,factor*value,
                                         -factor*ry*value/inertia,
                                         factor*rx*value/inertia))
        if abs(covered-pad_area)>2e-10*pad_area:
            raise ValueError("pad host coverage incomplete or overlapping")
    result=sparse.coo_matrix((data,(rows,columns)),
                             shape=(3,model.dof_count)).tocsr()
    result.sum_duplicates()
    return result
