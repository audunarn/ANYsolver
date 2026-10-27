"""Production-derived linear Q4/S3 edge traces for the research connector."""
from __future__ import annotations

import hashlib
import json
import numpy as np
from scipy import sparse

from .e4_pl_element import QualifiedE4PLShellElement
from .e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from .submodel_transfer import element_interpolation_weights
from .solids import SolidModelError


class ShellEdgeTrace:
    """Ordered straight Q4/S3 chain, constant thickness and physical director.

    Offset is the signed reference-surface to solid midsurface distance along
    the physical director. It locates the interface; transport always uses the
    actual target minus the interpolated reference coordinate, exactly once.
    Q4 edges: (0,1),(1,2),(2,3),(3,0); S3: (0,1),(1,2),(2,0).
    S3 uses its production linear MIN3 displacement field, including the
    rotation-dependent quadratic edge term. This is research-only small-linear
    kinematics, not a finite-surface or qualification declaration.
    """
    _edge_nodes = ((0,1),(1,2),(2,3),(3,0))
    _natural = ((-1.,-1.),(1.,-1.),(1.,1.),(-1.,1.))

    @classmethod
    def _layout(cls, element):
        if type(element) is QualifiedE4PLShellElement:
            return cls._edge_nodes, cls._natural
        if type(element) is NativeParityE4PLS3V2DShellElement:
            return ((0,1),(1,2),(2,0)), ((0.,0.),(1.,0.),(0.,1.))
        raise SolidModelError('shell trace admits exact production E4-PL Q4 or S3 V2D only')

    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):
            raise AttributeError('ShellEdgeTrace is immutable; rebuild after changes')
        object.__setattr__(self,name,value)

    def __init__(self, model, edges, *, offset=0.0, tolerance=1e-10):
        self.model = model
        self.edges = tuple((int(e),int(k)) for e,k in edges)
        if len(set(self.edges)) != len(self.edges):
            raise SolidModelError('duplicate shell trace edge')
        self.offset, self.tolerance = float(offset), float(tolerance)
        if not self.edges or not np.isfinite([self.offset,self.tolerance]).all() or tolerance <= 0:
            raise SolidModelError('trace needs edges, a finite offset and positive physical tolerance')
        self.ndof = model.mesh.dof_manager.total_dofs
        vertices=[]
        normals=[]
        thicknesses=[]
        outward=[]
        self._segments=[]
        for eid, edge in self.edges:
            element=model.mesh.elements[eid]
            edge_nodes,_=self._layout(element)
            if edge not in range(len(edge_nodes)):
                raise SolidModelError('invalid production shell edge index')
            coordinates=np.asarray(element.get_node_coordinates(model.mesh),float)
            if not np.isfinite(coordinates).all():
                raise SolidModelError('shell trace geometry must be finite')
            a,b=edge_nodes[edge]
            start,end=coordinates[a],coordinates[b]
            if np.linalg.norm(end-start)<=tolerance:
                raise SolidModelError('degenerate shell edge')
            if vertices and np.linalg.norm(start-vertices[-1])>tolerance:
                raise SolidModelError('edge chain must be ordered, connected and nonduplicated')
            if not vertices:
                vertices.append(start)
            vertices.append(end)
            geometric=np.cross(coordinates[1]-coordinates[0],coordinates[-1]-coordinates[0])
            if np.linalg.norm(geometric) <= np.finfo(float).tiny:
                raise SolidModelError('degenerate shell facet')
            geometric/=np.linalg.norm(geometric)
            director=element.physical_reference_director
            director=geometric if director is None else np.asarray(director,float)
            if director.shape!=(3,) or not np.isfinite(director).all() or np.linalg.norm(director)<=np.finfo(float).tiny:
                raise SolidModelError('physical shell director must be finite and nonzero')
            director=director/np.linalg.norm(director)
            if abs(abs(geometric@director)-1)>1e-10 or np.max(abs((coordinates-start)@director))>tolerance:
                raise SolidModelError('only planar facets with physical normal are supported')
            normals.append(director)
            thickness=float(element.thickness)
            if not np.isfinite(thickness) or thickness<=0:
                raise SolidModelError('each shell thickness must be finite and positive')
            if not np.isfinite(float(getattr(element,'reference_surface_offset',0.0))):
                raise SolidModelError('shell reference-surface offset must be finite')
            thicknesses.append(thickness)
            inward=coordinates.mean(axis=0)-(start+end)/2
            inward-=director*(director@inward)
            tangent=(end-start)/np.linalg.norm(end-start)
            inward-=tangent*(tangent@inward)
            if np.linalg.norm(inward)<=tolerance:
                raise SolidModelError('degenerate shell facet side')
            outward.append(inward/np.linalg.norm(inward))
            self._segments.append((element,edge,
                np.frombuffer(np.ascontiguousarray(start).tobytes(),dtype=float),
                np.frombuffer(np.ascontiguousarray(end).tobytes(),dtype=float)))
        self.reference_start=np.array(vertices[0],float)
        delta=np.array(vertices[-1])-self.reference_start
        self.length=float(np.linalg.norm(delta))
        if self.length<=tolerance:
            raise SolidModelError('zero-length interface')
        self.tangent=delta/self.length
        self.normal=np.array(normals[0])
        self.conormal=np.cross(self.normal,self.tangent)
        self.solid_outward=np.array(outward[0])
        self.thickness=thicknesses[0]
        if self.thickness<=0 or not np.isfinite(self.thickness):
            raise SolidModelError('thickness must be finite and positive')
        coordinates=np.array(vertices)
        self.breakpoints=(coordinates-self.reference_start)@self.tangent
        residual=coordinates-self.reference_start-self.breakpoints[:,None]*self.tangent
        if np.max(np.linalg.norm(residual,axis=1))>tolerance or np.any(np.diff(self.breakpoints)<=tolerance):
            raise SolidModelError('only monotone straight edge chains are supported')
        if any(np.linalg.norm(n-self.normal)>1e-10 for n in normals) or any(abs(t-self.thickness)>tolerance for t in thicknesses) or any(np.linalg.norm(n-self.solid_outward)>1e-10 for n in outward):
            raise SolidModelError('mixed directors, sides or thicknesses require separate qualification')
        for name in ('reference_start','tangent','normal','conormal','solid_outward','breakpoints'):
            value=np.ascontiguousarray(getattr(self,name))
            setattr(self,name,np.frombuffer(value.tobytes(),dtype=value.dtype).reshape(value.shape))
        self._segments=tuple(self._segments)
        self._signature=self.signature()
        self._sealed=True

    def signature(self):
        payload=[]
        for eid,edge in self.edges:
            e=self.model.mesh.elements[eid]
            payload.append((eid,edge,id(e),type(e).__module__,type(e).__qualname__,e.node_ids,
                            np.asarray(e.get_node_coordinates(self.model.mesh)).tolist(),float(e.thickness),
                            None if e.physical_reference_director is None else e.physical_reference_director.tolist(),
                            float(getattr(e,'reference_surface_offset',0.0)),
                            [list(self.model.mesh.dof_manager.get_node_dofs(node)) for node in e.node_ids]))
        return hashlib.sha256(json.dumps((payload,self.offset,self.tolerance,self.model.mesh.dof_manager.total_dofs),sort_keys=True).encode()).hexdigest()

    def validate(self):
        try:
            current=self.signature()
        except (KeyError,ValueError,TypeError,AttributeError) as exc:
            raise SolidModelError('stale shell trace: referenced geometry or layout is unavailable') from exc
        if current!=self._signature:
            raise SolidModelError('stale shell trace: rebuild after geometry/thickness/director/DOF changes')

    def chart(self,points):
        relative=np.asarray(points,float)-self.reference_start
        return np.column_stack((relative@self.tangent,relative@self.normal-self.offset))

    def points(self,chart):
        chart=np.asarray(chart,float)
        return self.reference_start+chart[:,0,None]*self.tangent+(chart[:,1,None]+self.offset)*self.normal

    def displacement_operator(self,points):
        self.validate()
        points=np.asarray(points,float)
        if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():
            raise SolidModelError('trace points must be finite (N,3)')
        chart=self.chart(points)
        plane=(points-self.reference_start)@self.solid_outward
        if np.any(abs(plane)>self.tolerance) or np.any(chart[:,0]<-self.tolerance) or np.any(chart[:,0]>self.length+self.tolerance) or np.any(abs(chart[:,1])>self.thickness/2+self.tolerance):
            raise SolidModelError('points are outside the physical shell-solid interface')
        rows=[]; cols=[]; data=[]
        for p,(s,_) in enumerate(chart):
            segment=min(np.searchsorted(self.breakpoints,s,side='right')-1,len(self._segments)-1)
            segment=max(segment,0)
            element,edge,start,end=self._segments[segment]
            alpha=(s-self.breakpoints[segment])/(self.breakpoints[segment+1]-self.breakpoints[segment])
            edge_nodes,natural_nodes=self._layout(element)
            a,b=edge_nodes[edge]
            natural=(1-alpha)*np.array(natural_nodes[a])+alpha*np.array(natural_nodes[b])
            weights=element_interpolation_weights(element,natural)
            reference=weights@element.get_node_coordinates(self.model.mesh)
            arm=points[p]-reference
            for local_node,(node,weight) in enumerate(zip(element.node_ids,weights)):
                dofs=self.model.mesh.dof_manager.get_node_dofs(node)
                for component in range(3):
                    rows.append(3*p+component); cols.append(dofs[component]); data.append(weight)
                for axis in range(3):
                    vector=weight*np.cross(np.eye(3)[axis],arm)
                    if type(element) is NativeParityE4PLS3V2DShellElement:
                        # Restriction of production w_h=sum(N*w-l*rx+m*ry).
                        # l/m vanish at vertices; retained rotations are linear.
                        sign=1. if local_node==a else -1. if local_node==b else 0.
                        vector=vector+sign*.5*alpha*(1-alpha)*self.normal*np.dot(
                            self.normal,np.cross(np.eye(3)[axis],end-start))
                    for component in range(3):
                        rows.append(3*p+component); cols.append(dofs[3+axis]); data.append(vector[component])
        return sparse.csr_matrix((data,(rows,cols)),shape=(3*len(points),self.ndof))
