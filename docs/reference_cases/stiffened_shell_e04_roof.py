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


def crown_reference_perturbations(case, amplitude_m):
    """Smooth axial-extruded crown change with transported physical ports.

    This bounded field preserves planar Q4 facets and straight axial bars.
    It is a new virgin reference, not a displacement of a loaded roof.
    The amplitude sign follows downward global z at the crown.
    """
    from anysolver import stiffened_shell as ss
    amplitude=float(amplitude_m)
    if not np.isfinite(amplitude):
        raise ValueError('finite crown imperfection amplitude required')
    theta=np.arctan2(case.shell_directors[:,1],case.shell_directors[:,2])
    shape=np.cos(np.pi*theta/(2*case.half_angle))**2
    dz=amplitude*np.pi/(2*case.half_angle)*np.sin(np.pi*theta/case.half_angle)
    angle=np.arctan2(case.radius*np.sin(theta)-dz,case.radius*np.cos(theta))
    return tuple(ss.ReferencePosePerturbation('shell',i+1,
        (0.,0.,-float(amplitude*shape[i])),(float(theta[i]-angle[i]),0.,0.))
        for i in range(len(theta)))


def definition(case, *, density_kg_m3):
    """Adapt declared geometry through the experimental public definition API.

    Density is an explicit caller input, not inferred from stiffness. This
    curved profile admits static operations only. Rectangle properties are
    centroidal; the point law supplies the geometric eccentricity once.
    Local beam axes are (longitudinal, circumferential, outward).
    """
    from anysolver import b3_ge, stiffened_shell as ss
    density=float(density_kg_m3)
    if not np.isfinite(density) or density<=0.:
        raise ValueError('explicit positive density required')
    b,h=case.bar_width,case.bar_height
    area=b*h;iy=b*h**3/12.;iz=h*b**3/12.
    odd=np.arange(1,512,2,dtype=float)
    torsion=h*b**3/3.*(1.-192.*b/(np.pi**5*h)*
        np.sum(np.tanh(odd*np.pi*h/(2*b))/odd**5))
    shear=case.young/(2*(1+case.poisson))
    stiffness=np.diag((case.young*area,5/6*shear*area,5/6*shear*area,
                       shear*torsion,case.young*iy,case.young*iz))
    section=b3_ge.EllipsoidalGeneralizedSection(stiffness,np.eye(6),1e20,1e9)
    inertia=np.diag(density*np.array((area,area,area,iy+iz,iy,iz)))
    shell_ids=tuple(range(1,len(case.shell_positions)+1))
    beam_ids=tuple(range(100001,100001+len(case.beam_positions)))
    beams=tuple(b3_ge.define_beam('b3-ge',i+1,
        tuple(beam_ids[j] for j in cell),case.beam_positions[cell],
        case.beam_frames[cell],section,inertia) for i,cell in enumerate(case.beam_cells))
    # The consumer's strict native input record uses builtin JSON numerics.
    shell=ss.ShellPanel(shell_ids,tuple(tuple(float(v) for v in row) for row in case.shell_positions),
        tuple(tuple(shell_ids[j] for j in cell) for cell in case.quads),
        case.thickness,case.young,case.poisson,density)
    points=tuple(ss.PointConnection(shell_ids[s],beam_ids[b]) for s,b in case.point_pairs)
    fixed=tuple(ss.FixedCoordinate('shell',shell_ids[s],axis)
        for s in case.fixed_shell_translations for axis in range(3))
    return ss.LinearDefinition(ss.B3_GE_E4_PL_STIFFENED_SHELL_V1,shell,beams,points,fixed,
        q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1,
        shell_reference_policy=ss.CURVED_Q4_POINT_REFERENCE_V1)


def material_definition(case, *, density_kg_m3, shell_curve,
                        beam_yield_limits, beam_hardening_n):
    """Declare a material development case without inferring rectangle strength.

    Limits are positive reference resultants in (N,N,N,Nm,Nm,Nm), respectively
    axial, the two shears, torque and the two bending moments. The associated
    ellipsoid is a declared generalized law, not physical fibre plasticity.
    Geometry, centroidal elastic stiffness, inertia and point offsets come from
    the existing reference adapter. Caller-supplied strength is not calibration.
    """
    from dataclasses import replace
    from numbers import Real
    from anymaterial import DNVC208MaterialCurve
    from anysolver import b3_ge, stiffened_shell as ss
    limits=np.asarray(beam_yield_limits,dtype=object)
    if (limits.shape!=(6,) or any(isinstance(v,(bool,np.bool_)) or
            not isinstance(v,Real) for v in limits) or
            not np.isfinite(limits.astype(float)).all() or np.any(limits.astype(float)<=0.) or
            isinstance(beam_hardening_n,(bool,np.bool_)) or not isinstance(beam_hardening_n,Real) or
            not np.isfinite(beam_hardening_n) or beam_hardening_n<=0.):
        raise ValueError('six positive finite native resultant limits and hardening force required')
    if shell_curve is not None and type(shell_curve) is not DNVC208MaterialCurve:
        raise ValueError('explicit admitted isotropic shell J2 curve or elastic shell required')
    base=definition(case,density_kg_m3=density_kg_m3)
    limits=limits.astype(float);yield_force=float(limits[0]);beams=[]
    for stored in base.beams:
        element,inertia=stored.instantiate()
        section=b3_ge.EllipsoidalGeneralizedSection(element.section.elastic,
            np.diag((yield_force/limits)**2),yield_force,float(beam_hardening_n))
        candidate=type(element)(element.element_id,element.node_ids,
            element.operator.reference,section,order=element.operator.order,
            arithmetic_policy=element.operator.arithmetic_policy)
        beams.append(type(stored).capture(candidate,inertia))
    return replace(base,shell=replace(base.shell,j2_curve=shell_curve),beams=tuple(beams),
        shell_reference_policy=ss.CURVED_Q4_POINT_MATERIAL_REFERENCE_V1,
        retained_scale_policy='native_force_moment_roles_v1')
