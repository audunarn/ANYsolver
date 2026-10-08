"""Five-row physical rigid-region reference law; normal spin is independent."""
from dataclasses import dataclass
from math import fsum
import numpy as np
from scipy.spatial.transform import Rotation
from ._stiffened_shell_b2_nodal_footprint import B2NodalRigidFootprint,compile_footprints as _old_compile, _difference

LAW_ID="B2_PHYSICAL_RIGID_FOOTPRINT_DIRECTOR_REFERENCE_V1_EXPERIMENTAL"
BUCKLING_POLICY="B2_PHYSICAL_RIGID_FOOTPRINT_GREEN_BUCKLING_V1_DEV"

def _owned(value,shape):
    a=np.asarray(value,dtype=float)
    if a.shape!=shape or not np.isfinite(a).all(): raise ValueError("finite owned physical footprint coordinates required")
    return np.frombuffer(a.tobytes(),dtype=float).reshape(shape)

def _skew(v):
    return np.array(((0.,-v[2],v[1]),(v[2],0.,-v[0]),(-v[1],v[0],0.)))

@dataclass(frozen=True)
class B2PhysicalRigidFootprint:
    footprint_id: str
    shell_nodes: tuple
    beam_node: int
    reference_director: tuple
    tangent_basis: tuple
    patch_cells: tuple = ()

    def __post_init__(self):
        proxy=B2NodalRigidFootprint(self.footprint_id,self.shell_nodes,self.beam_node,self.patch_cells)
        object.__setattr__(self,"shell_nodes",proxy.shell_nodes);object.__setattr__(self,"patch_cells",proxy.patch_cells)
        if not self.patch_cells: raise ValueError("physical rigid footprint requires complete patch_cells")
        n=_owned(self.reference_director,(3,));e=_owned(self.tangent_basis,(3,2))
        eps=128*np.finfo(float).eps
        if abs(n@n-1.)>eps or np.max(abs(e.T@e-np.eye(2)))>eps or np.max(abs(e.T@n))>eps:
            raise ValueError("unit physical director and orthonormal owned tangent basis required")
        object.__setattr__(self,"reference_director",n);object.__setattr__(self,"tangent_basis",e)

    def descriptor(self):
        return dict(law=LAW_ID,footprint_id=self.footprint_id,shell_nodes=self.shell_nodes,beam_node=self.beam_node,
            patch_cells=self.patch_cells,semantics="complete_selected_cell_patch" if self.patch_cells else "selected_nodes_only",
            configuration="reference_linear_static_with_objective_spectral_continuation",rows_per_node=5,normal_spin="independent",
            director=tuple(self.reference_director),tangent_basis=tuple(tuple(row) for row in self.tangent_basis),production_qualified=False)

@dataclass(frozen=True)
class B2PhysicalRigidFootprintSelection:
    footprint_ids: tuple
    def __post_init__(self):
        if isinstance(self.footprint_ids,(str,bytes)): raise ValueError("explicit physical footprint recovery sequence required")
        values=tuple(self.footprint_ids)
        if not values or any(type(v)is not str or not v for v in values) or len(set(values))!=len(values):
            raise ValueError("distinct physical footprint selection IDs required")
        object.__setattr__(self,"footprint_ids",values)

@dataclass(frozen=True)
class PhysicalFootprintNode:
    footprint_id: str
    shell_node: int
    beam_node: int
    row_start: int
    shell_slots: tuple
    beam_slots: tuple
    shell_position: tuple
    beam_position: tuple
    director: np.ndarray
    tangent_basis: np.ndarray
    constraint: np.ndarray
    constraint_hessians: np.ndarray
    row_count: int = 5

    @property
    def shell_matrix(self): return self.constraint[:,:6]
    @property
    def beam_matrix(self): return self.constraint[:,6:]

    def functional(self,shell_pose,beam_pose):
        shell=_owned(shell_pose,(6,));beam=_owned(beam_pose,(6,))
        qb=Rotation.from_rotvec(beam[3:]).as_matrix();qs=Rotation.from_rotvec(shell[3:]).as_matrix()
        relative=qb.T@qs@self.director
        if self.director@relative<=0.: raise ValueError("physical footprint director left positive hemisphere")
        arm=np.array([fsum(_difference(float(a),float(b))) for a,b in zip(self.shell_position,self.beam_position)])
        return np.r_[qb.T@(arm+shell[:3]-beam[:3])-arm,self.tangent_basis.T@relative]

    def multiplier_hessian(self,multiplier):
        lam=_owned(multiplier,(5,))
        return np.einsum('i,iab->ab',lam,self.constraint_hessians)

def _node(group,item,row_start):
    n=group.reference_director;e=group.tangent_basis
    arm=np.array([fsum(_difference(float(a),float(b))) for a,b in zip(item.shell_position,item.beam_position)])
    c=np.zeros((5,12));c[:3,:3]=np.eye(3);c[:3,6:9]=-np.eye(3);c[:3,9:]=_skew(arm)
    c[3:,3:6]=-e.T@_skew(n);c[3:,9:]=e.T@_skew(n)
    h=np.zeros((5,12,12));eye=np.eye(12)
    for a in range(12):
        for b in range(12):
            sa=eye[3:6,a];sb=eye[3:6,b];ba=eye[9:,a];bb=eye[9:,b]
            da=eye[:3,a]-eye[6:9,a];db=eye[:3,b]-eye[6:9,b]
            h[:3,a,b]=-np.cross(ba,db)-np.cross(bb,da)+.5*(np.cross(ba,np.cross(bb,arm))+np.cross(bb,np.cross(ba,arm)))
            h[3:,a,b]=e.T@(.5*(np.cross(ba,np.cross(bb,n))+np.cross(bb,np.cross(ba,n))+np.cross(sa,np.cross(sb,n))+np.cross(sb,np.cross(sa,n)))-np.cross(ba,np.cross(sb,n))-np.cross(bb,np.cross(sa,n)))
    return PhysicalFootprintNode(group.footprint_id,item.shell_node,item.beam_node,row_start,item.shell_slots,item.beam_slots,
        item.shell_position,item.beam_position,n,e,_owned(c,(5,12)),_owned(h,(5,12,12)))

def compile_physical_footprints(groups,positions,shells,beam_positions,shell_index,beam_index,points):
    groups=tuple(groups)
    if any(type(g)is not B2PhysicalRigidFootprint for g in groups):raise ValueError("typed physical rigid footprints required")
    # Reuse existing geometry/topology/overlap audit, not its six-row law.
    proxies=tuple(B2NodalRigidFootprint(g.footprint_id,g.shell_nodes,g.beam_node,g.patch_cells) for g in groups)
    _,old=_old_compile(proxies,positions,shells,beam_positions,shell_index,beam_index,points)
    by_id={g.footprint_id:g for g in groups};eps=128*np.finfo(float).eps
    for group in groups:
        n=group.reference_director;base=np.asarray(positions[group.shell_nodes[0]])
        for node in group.shell_nodes:
            d=np.asarray(positions[node])-base
            if abs(d@n)>eps*(abs(d)@abs(n)):raise ValueError("physical footprint selected nodes must be coplanar with owned director")
            for shell in shells:
                if node not in shell.node_ids:continue
                if len(shell.node_ids)!=4:raise ValueError("physical rigid footprint currently requires Q4")
                if np.max(abs(np.asarray(shell.reference_normal)-n))>eps:
                    raise ValueError("physical footprint ambiguous director seam")
    made=tuple(_node(by_id[item.footprint_id],item,6*len(points)+5*i) for i,item in enumerate(old))
    return groups,made

def checked_selection(selection,groups):
    if selection is None:return ()
    if type(selection)is not B2PhysicalRigidFootprintSelection:raise ValueError("typed physical footprint selection required")
    if any(name not in {g.footprint_id for g in groups} for name in selection.footprint_ids):raise ValueError("physical footprint selection not compiled")
    return selection.footprint_ids

@dataclass(frozen=True)
class PhysicalFootprintNodeAction:
    shell_node_id: int
    beam_node_id: int
    row_start: int
    shell_force_N: tuple
    shell_direct_couple_Nm: tuple
    beam_force_N: tuple
    beam_direct_couple_Nm: tuple
    gap: tuple

@dataclass(frozen=True)
class B2PhysicalRigidFootprintWrench:
    footprint_id: str
    common_reference_origin_m: tuple
    shell_force_N: tuple
    shell_moment_Nm: tuple
    beam_force_N: tuple
    beam_moment_Nm: tuple
    node_actions: tuple
    law_id: str = LAW_ID
    production_qualified: bool = False

def selected_wrenches(incidences,selected,multipliers,gaps):
    made=[]
    for name in selected:
        sf=[];sm=[];bf=[];bm=[];actions=[];origin=None
        for item in incidences:
            if item.footprint_id!=name:continue
            origin=item.beam_position;lam=np.asarray(multipliers[item.row_start:item.row_start+5])
            actual=-item.constraint.T@lam;s=actual[:6];b=actual[6:]
            arm=[_difference(float(a),float(b)) for a,b in zip(item.shell_position,origin)]
            moment=np.array([fsum((float(s[i+3]),arm[(i+1)%3][0]*s[(i+2)%3],arm[(i+1)%3][1]*s[(i+2)%3],-arm[(i+2)%3][0]*s[(i+1)%3],-arm[(i+2)%3][1]*s[(i+1)%3])) for i in range(3)])
            sf.append(s[:3]);sm.append(moment);bf.append(b[:3]);bm.append(b[3:])
            actions.append(PhysicalFootprintNodeAction(item.shell_node,item.beam_node,item.row_start,
                tuple(s[:3]),tuple(s[3:]),tuple(b[:3]),tuple(b[3:]),tuple(gaps[item.row_start:item.row_start+5])))
        vectors=tuple(tuple(fsum(float(v[i]) for v in rows) for i in range(3)) for rows in (sf,sm,bf,bm))
        if origin is None or not np.isfinite(vectors).all():raise ValueError("finite physical footprint wrench required")
        made.append(B2PhysicalRigidFootprintWrench(name,origin,*vectors,tuple(actions)))
    return tuple(made)


def q4_exp_director_chart_correction(element,mesh,material,displacement):
    """Native physical first-work pullback from linear director to Exp chart.

    PL/drilling fields are excluded by the native stationary physical covector.
    Only the flat, strict-zero-shear new spectral operation calls this helper.
    """
    recovered=element._recover_planar_mixed_fields(mesh,displacement,material,element.gauss_points)
    local_force=recovered["stationary_coupling"]@recovered["stationary_parameters"]
    frame=recovered["frame"];n=frame[:,2]
    correction=np.zeros((24,24));axes=np.eye(3)
    for node in range(4):
        m=frame@local_force[6*node+3:6*node+6]
        for a in range(3):
            for b in range(3):
                second=.5*(np.cross(axes[a],np.cross(axes[b],n))+np.cross(axes[b],np.cross(axes[a],n)))
                correction[6*node+3+a,6*node+3+b]=m@np.cross(n,second)
    if not np.isfinite(correction).all():raise ValueError("physical Q4 Exp-director chart work not representable")
    return correction
