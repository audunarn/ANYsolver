"""Exact rectangular topology and conservative incidence for the F03 reference.

No element operator or equilibrium is evaluated here. Pattern counts are
structural upper envelopes: fixed physical footprints can make them grow
much faster than the shell's local incidence under refinement.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import sys

import numpy as np

from scripts import _b3_e4_f03_spatial_contract as c
from scripts import _b3_e4_f03_local_moments as moments


def _cuts(values,lower,upper):
    if (type(values) not in (tuple,list) or len(values)<2 or len(values)>257 or
            any(not moments._coordinate(v) for v in values) or
            values[0]!=lower or values[-1]!=upper or
            any(a>=b for a,b in zip(values,values[1:]))):
        raise ValueError('invalid bounded exact panel partition')
    return tuple(values)


def _readonly_int(value):
    array=np.asarray(value,dtype=np.int64)
    return np.frombuffer(array.tobytes(),dtype=np.int64).reshape(array.shape)


def _axis_nodes(cuts,p):
    nodes=tuple(left+(right-left)*Fraction(k,p)
                 for left,right in zip(cuts,cuts[1:]) for k in range(p))+ (cuts[-1],)
    if any(not moments._coordinate(v) for v in nodes):
        raise ValueError('derived exact node exceeds coordinate bit bound')
    return nodes


@dataclass(frozen=True,init=False,slots=True)
class CompiledGrid:
    x_cuts: tuple[Fraction,...]
    y_cuts: tuple[Fraction,...]
    p: int
    x_nodes: tuple[Fraction,...]
    y_nodes: tuple[Fraction,...]
    rectangles: tuple[moments.Rectangle,...]
    free_to_full: np.ndarray
    full_to_free: np.ndarray
    full_gathers: np.ndarray
    free_gathers: np.ndarray
    station_cuts: tuple[Fraction,...]
    trace_incidence: tuple[np.ndarray,...]
    root_incidence: np.ndarray

    def __init__(self,*args,**kwargs):
        raise TypeError('CompiledGrid requires the validated compile_grid factory')

    @property
    def full_dofs(self): return 2*len(self.x_nodes)*len(self.y_nodes)

    @property
    def free_dofs(self): return len(self.free_to_full)


def compile_grid(x_cuts,y_cuts,p,*,max_incidence_entries=1000000):
    """Compile shared Qp nodes with exactly zero displacement on both x edges.

    Cell and global scalar-node numbering is y-major then x-major. Full
    DOFs are component-major. Local gathers are component/y-node/x-node.
    No coincident numerical coordinate merges distinct exact model nodes.
    """
    if type(p) is not int or p not in (1,2,3):
        raise ValueError('local proof degree must be 1,2 or3')
    if type(max_incidence_entries) is not int or max_incidence_entries<=0:
        raise ValueError('positive trace-incidence entry budget required')
    xs=_cuts(x_cuts,Fraction(-1,2),Fraction(3,2))
    ys=_cuts(y_cuts,Fraction(-1,2),Fraction(1,2))
    xn=_axis_nodes(xs,p);yn=_axis_nodes(ys,p)
    node_count=len(xn)*len(yn)
    if node_count>100000:
        raise ValueError('bounded reference topology exceeds 100000 nodes')
    free=tuple(component*node_count+j*len(xn)+i
               for component in (0,1) for j in range(len(yn))
               for i in range(1,len(xn)-1))
    reverse=np.full(2*node_count,-1,dtype=np.int64)
    reverse[np.asarray(free,dtype=np.int64)]=np.arange(len(free))
    rects=[];gathers=[]
    for j,(yb,yt) in enumerate(zip(ys,ys[1:])):
        for i,(xl,xr) in enumerate(zip(xs,xs[1:])):
            rects.append(moments.Rectangle(xl,xr,yb,yt))
            gathers.append(tuple(component*node_count+(j*p+lj)*len(xn)+i*p+li
                for component in (0,1) for lj in range(p+1) for li in range(p+1)))
    full_gathers=np.asarray(gathers,dtype=np.int64)
    free_gathers=reverse[full_gathers]
    # Four pads are all combinations of two x and two y offsets. Their
    # y incidence is fixed; the two moving x windows determine intervals.
    yrows=tuple(j for j,(yb,yt) in enumerate(zip(ys,ys[1:]))
               if any(max(yb,pad[2])<min(yt,pad[3]) for pad in c.PADS))
    events={Fraction(0),c.Q_L0}
    for edge in xs:
        for left,right,_,_ in c.PADS:
            for end in (left,right):
                station=edge-end
                if 0<station<c.Q_L0:
                    if not moments._coordinate(station):
                        raise ValueError('derived exact station exceeds coordinate bit bound')
                    events.add(station)
    stations=tuple(sorted(events))
    if len(stations)>4097:
        raise ValueError('bounded reference has too many exact station events')
    def active(station):
        columns=tuple(i for i,(xl,xr) in enumerate(zip(xs,xs[1:]))
            if any(max(xl,station+pad[0])<min(xr,station+pad[1]) for pad in c.PADS))
        rows=(free_gathers[j*(len(xs)-1)+i] for j in yrows for i in columns)
        return _readonly_int(sorted({int(dof) for row in rows for dof in row if dof>=0}))
    root=active(Fraction(0));entries=len(root);incidence=[]
    if entries>max_incidence_entries:
        raise ValueError('root incidence exceeds declared entry budget')
    for a,b in zip(stations,stations[1:]):
        ids=active((a+b)/2);entries+=len(ids)
        if entries>max_incidence_entries:
            raise ValueError('trace incidence exceeds declared entry budget')
        incidence.append(ids)
    # Only this validated factory initializes the record. Ordinary direct
    # construction/dataclasses.replace cannot introduce borrowed arrays.
    result=object.__new__(CompiledGrid)
    values=(xs,ys,p,xn,yn,tuple(rects),_readonly_int(free),
        _readonly_int(reverse),_readonly_int(full_gathers),_readonly_int(free_gathers),
        stations,tuple(incidence),root)
    fields=('x_cuts','y_cuts','p','x_nodes','y_nodes','rectangles',
            'free_to_full','full_to_free','full_gathers','free_gathers',
            'station_cuts','trace_incidence','root_incidence')
    for name,value in zip(fields,values): object.__setattr__(result,name,value)
    return result


def incidence_envelope(grid,*,max_graph_bytes):
    """Exact union of conservative shell/trace/root connectivity envelopes.

    Row bitsets count possible couplings without allocating numeric global
    matrices. Dense-factor entries are an upper bound, not measured LU fill.
    A later resource gate must also enforce actual factor workspace and RSS.
    """
    if not isinstance(grid,CompiledGrid) or type(max_graph_bytes) is not int or max_graph_bytes<=0:
        raise ValueError('grid and positive explicit graph budget required')
    n=grid.free_dofs+3
    digits=(n+sys.int_info.bits_per_digit-1)//sys.int_info.bits_per_digit
    mask_bytes=sys.getsizeof(0)+max(0,digits-1)*sys.int_info.sizeof_digit
    list_bytes=sys.getsizeof([])+n*np.dtype(np.intp).itemsize
    # Two lists of row bitsets, temporary masks and a conservative allowance
    # for temporary integer/tuple/set objects. Include CPython's actual
    # digit storage instead of assuming one byte per eight bits.
    peak_graph_bound=2*(list_bytes+n*mask_bytes)+8*mask_bytes+512*n
    if peak_graph_bound>max_graph_bytes:
        raise ValueError('symbolic graph upper storage exceeds declared budget')
    rows=[0]*n
    def clique(indices):
        ids=tuple(sorted({int(i) for i in indices if i>=0}))
        mask=0
        for i in ids: mask|=1<<i
        for i in ids: rows[i]|=mask
    for gather in grid.free_gathers: clique(gather)
    shell_nnz=sum(row.bit_count() for row in rows)
    trace_only=[0]*grid.free_dofs
    for incidence in grid.trace_incidence:
        mask=0
        for i in incidence: mask|=1<<int(i)
        for i in incidence:
            rows[int(i)]|=mask;trace_only[int(i)]|=mask
    beam_nnz=sum(row.bit_count() for row in trace_only)
    primal_nnz=sum(row.bit_count() for row in rows)
    root_mask=0
    for i in grid.root_incidence: root_mask|=1<<int(i)
    for root in range(grid.free_dofs,n):
        rows[root]=root_mask
        for i in grid.root_incidence: rows[int(i)]|=1<<root
    row_counts=tuple(row.bit_count() for row in rows)
    nnz=sum(row_counts)
    widths=tuple(b-a for a,b in zip(grid.station_cuts,grid.station_cuts[1:]))
    # Two row-bitset arrays exist simultaneously; conservative object/list
    # storage is included, independent of their actual physical fill.
    return {'schema':'f03_local_incidence_envelope_v1',
        'cells':len(grid.rectangles),'p':grid.p,'nodes':grid.full_dofs//2,
        'physical_free_dofs':grid.free_dofs,'root_multipliers':3,
        'station_intervals':len(widths),
        'positive_intervals_with_collapsed_float_endpoints':sum(
            float(a)==float(b) for a,b in zip(grid.station_cuts,grid.station_cuts[1:])),
        'minimum_station_width':[str(min(widths).numerator),str(min(widths).denominator)],
        'max_active_trace_dofs':max(map(len,grid.trace_incidence),default=0),
        'sum_trace_clique_entries':sum(len(v)**2 for v in grid.trace_incidence),
        'shell_nnz_envelope':shell_nnz,'beam_nnz_envelope':beam_nnz,
        'primal_nnz_envelope':primal_nnz,'kkt_nnz_envelope':nnz,
        'row_nnz_envelope':list(row_counts),
        'root_support_dofs':len(grid.root_incidence),
        'graph_storage_bound_bytes':peak_graph_bound,
        'one_csc_int64_values_bound_bytes':16*nnz+8*(n+1),
        'dense_L_plus_U_entries_bound':n*(n+1),
        'dense_L_plus_U_int64_values_bound_bytes':16*n*(n+1)+16*(n+1),
        'claim':'Connectivity/storage envelopes only; no factorization, measured '
                'fill, mechanical assembly, equilibrium, or linear scaling claim.'}
