"""E04 development geometry, not an executed or accepted capacity reference.

SI shallow cylindrical roof with two eccentric longitudinal rectangular bars.
The bare-roof dimensions follow the Kratos hinged-roof example (Sze et al. 2004):
https://kratosmultiphysics.github.io/Kratos/pages/Applications/Structural_Mechanics_Application/Examples/Hinged-cylindrical-roof-snapthrough.html
Adding stiffeners and the explicit supports below defines a NEW comparison case.
No published roof load is asserted to be its limit load. No solver is launched.
"""
from dataclasses import dataclass
import numpy as np


def owned(value,dtype=float):
    a=np.asarray(value,dtype=dtype)
    return np.frombuffer(a.tobytes(),dtype=a.dtype).reshape(a.shape)


@dataclass(frozen=True)
class RoofCase:
    shell_positions: np.ndarray
    shell_directors: np.ndarray
    quads: np.ndarray
    beam_positions: np.ndarray
    beam_frames: np.ndarray
    beam_cells: np.ndarray
    point_pairs: np.ndarray
    fixed_shell_translations: np.ndarray
    loaded_shell_node: int
    metric_weights: np.ndarray
    shell_area: float
    beam_length: float
    length: float = .508
    radius: float = 2.540
    half_angle: float = .1
    thickness: float = .0127
    bar_width: float = .00635
    bar_height: float = .0254
    young: float = 3.10275e9
    poisson: float = .3
    production_qualified: bool = False


def build(nx=8,ny=8):
    """Zero-based fixture rows; model IDs must be assigned explicitly by adapters.

    x is the cylinder axis, theta the circumferential parameter. All translations
    on the two straight side edges are fixed, rotations free; curved ends free.
    A downward dead force acts at the center shell node. Both bars lie at
    theta=+/-0.05 and have centroid offset (shell thickness+bar height)/2 along
    the outward director. Point pairs declare full relative-pose bonds at each
    B3 node, not BL5 five-channel lines. No connection equations are implemented
    here. There is no initial material stress or additional imperfection.
    """
    if type(nx) is not int or type(ny) is not int or not 4<=nx<=64 or nx%2 or not 4<=ny<=64 or ny%4:
        raise ValueError('even axial and multiple-of-four transverse divisions in [4,64] required')
    x=np.linspace(-.254,.254,nx+1);theta=np.linspace(-.1,.1,ny+1)
    positions=np.array([(v,2.540*np.sin(t),2.540*(np.cos(t)-np.cos(.1))) for v in x for t in theta])
    directors=np.array([(0.,np.sin(t),np.cos(t)) for v in x for t in theta])
    node=lambda i,j:i*(ny+1)+j
    quads=np.array([(node(i,j),node(i+1,j),node(i+1,j+1),node(i,j+1))
                    for i in range(nx) for j in range(ny)])
    shell_weights=np.zeros(len(positions))
    for q in quads:
        p=positions[q]
        area=.5*(np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))+
                  np.linalg.norm(np.cross(p[2]-p[0],p[3]-p[0])))
        shell_weights[q]+=area/4.
    beam=[];frames=[];pairs=[];cells=[]
    for j in (ny//4,3*ny//4):
        start=len(beam)
        for i in range(nx+1):
            s=node(i,j);n=directors[s];axis=np.array([1.,0.,0.])
            pairs.append((s,len(beam)))
            beam.append(positions[s]+(.0127+.0254)/2*n)
            frames.append(np.column_stack((axis,np.cross(n,axis),n)))
        cells.extend((start+i,start+i+1,start+i+2) for i in range(0,nx,2))
    beam=np.asarray(beam);beam_weights=np.zeros(len(beam))
    for a,b,c in cells:
        measure=np.linalg.norm(beam[c]-beam[a])
        beam_weights[[a,b,c]]+=measure*np.array([1.,4.,1.])/6.
    area=float(shell_weights.sum());length=float(beam_weights.sum())
    # Declared continuation metric, not physical inertia: equal total weight for
    # each domain, lumped reference-area and quadratic reference-length measures.
    weights=np.r_[.5*shell_weights/area,.5*beam_weights/length]
    fixed=np.array([node(i,j) for i in range(nx+1) for j in (0,ny)])
    return RoofCase(owned(positions),owned(directors),owned(quads,int),owned(beam),
        owned(frames),owned(cells,int),owned(pairs,int),owned(fixed,int),
        node(nx//2,ny//2),owned(weights),area,length)
