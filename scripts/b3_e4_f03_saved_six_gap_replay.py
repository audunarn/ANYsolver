"""Project one saved C1 solid field onto the *native* six weak line rows.

This is a development comparison, not a reconstruction of an E4 state or
proof of bond slip. The solid bond has shared nodes. The beam port is a
fitted rigid section; the shell director is inferred from solid thickness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u, project


GRID = np.linspace(.9, 1., 6)
CUTS = np.sort(np.r_[GRID, .95])
YCUTS = np.linspace(-.05, .05, 11)
KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")
MODES = ("actual_solid_face", "solid_cell_Q4_proxy", "native_host_Q4_proxy")
NATIVE_X = np.array((.9,.95,1.))
NATIVE_Y = np.linspace(-.05,.05,5)
Y_INTEGRATION_CUTS = np.unique(np.r_[YCUTS,NATIVE_Y])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lookup(coords: dict[int, np.ndarray]):
    table = {tuple(np.round(point, 9)): node for node, point in coords.items()}
    if len(table) != len(coords):
        raise ValueError("duplicate solid node coordinates")

    def node(x: float, y: float, z: float) -> int:
        key = tuple(np.round((x, y, z), 9))
        if key not in table:
            raise ValueError(f"missing solid node at {key}")
        return table[key]

    return node


def _ports(coords: dict[int, np.ndarray], u: dict[int, np.ndarray],
           elements: dict[str, np.ndarray], *, method: str):
    reference = np.array([[x, 0., .0675] for x in GRID])
    if method == "area":
        fits = [project(coords, u, section_x=float(x),
                        patch_grid=tuple(GRID), transverse_cells=10)
                for x in GRID]
        translation = np.array([fit["beam_center_m"] for fit in fits])-reference
        rotation = np.array([fit["beam_rotation_vector_rad"] for fit in fits])
        rms = np.array([fit["beam_section_rms_fit_residual_m"] for fit in fits])
        return translation, rotation, rms
    if method != "nonbond":
        raise ValueError(method)
    bar = set(np.asarray(elements["Stiffener"]).ravel())
    seam = {n for n in bar if abs(coords[n][2]-.0175)<1e-12
            and .9-1e-12 <= coords[n][0] <= 1.+1e-12
            and -.05-1e-12 <= coords[n][1] <= .05+1e-12}
    translation, rotation, rms = [], [], []
    for x in GRID:
        selected = sorted(n for n in bar-seam if abs(coords[n][0]-x) < 1e-12)
        if len(selected) < 12:
            raise ValueError("insufficient nonbond section nodes")
        design = np.zeros((3*len(selected), 6))
        values = np.array([u[n] for n in selected]).ravel()
        for i, n in enumerate(selected):
            xx, yy, zz = coords[n]-np.array((x, 0., .0675))
            design[3*i:3*i+3, :3] = np.eye(3)
            design[3*i:3*i+3, 3:] = ((0., zz, -yy),
                                     (-zz, 0., xx), (yy, -xx, 0.))
        motion, _, rank, _ = np.linalg.lstsq(design, values, rcond=None)
        if rank != 6:
            raise ValueError("nonbond section fit rank deficiency")
        translation.append(motion[:3])
        rotation.append(motion[3:])
        rms.append(float(np.sqrt(np.mean((design@motion-values)**2))*np.sqrt(3)))
    return np.array(translation), np.array(rotation), np.array(rms)


def _face_nodes(node, u, x0: float, x1: float, y0: float, y1: float,
                z: float) -> np.ndarray:
    xm, ym = (x0+x1)/2, (y0+y1)/2
    xy = ((x0,y0),(x1,y0),(x1,y1),(x0,y1),
          (xm,y0),(x1,ym),(xm,y1),(x0,ym))
    return np.array([u[node(float(x),float(y),z)] for x,y in xy])


def _director(v: np.ndarray) -> np.ndarray:
    length = np.linalg.norm(v)
    if length < .02 or not np.isfinite(length):
        raise ValueError("solid-inferred shell director is invalid")
    return v/length


def _solid_face_sample(node, u, x: float, y: float, z: float) -> np.ndarray:
    """Interpolate a solid F5 face at an arbitrary native Q4 host node."""
    ix = min(len(GRID)-2, max(0, int(np.searchsorted(GRID,x,side="right")-1)))
    iy = min(len(YCUTS)-2, max(0, int(np.searchsorted(YCUTS,y,side="right")-1)))
    x0,x1 = GRID[ix:ix+2]
    y0,y1 = YCUTS[iy:iy+2]
    xi,eta = 2*(x-x0)/(x1-x0)-1,2*(y-y0)/(y1-y0)-1
    face = _face_nodes(node,u,float(x0),float(x1),float(y0),float(y1),z)
    return _quad8_shape(float(xi),float(eta))@face


def _native_host(node,u,x: float,y: float):
    mid = _solid_face_sample(node,u,x,y,0.)
    top = _solid_face_sample(node,u,x,y,.0175)
    bottom = _solid_face_sample(node,u,x,y,-.0175)
    return mid,_director(np.array((0.,0.,.035))+top-bottom)


def _integrate(coords: dict[int, np.ndarray], u: dict[int, np.ndarray],
               translation: np.ndarray, rotation: np.ndarray) -> dict:
    node = _lookup(coords)
    roots, weights = np.polynomial.legendre.leggauss(3)
    spaces = {kind: LineMultiplierSpace(kind, (0., .5, 1.)) for kind in KINDS}
    sums = {kind: {mode: np.zeros((space.count, 6)) for mode in MODES}
            for kind, space in spaces.items()}
    masses = {kind: np.zeros(space.count) for kind, space in spaces.items()}
    inertias = {kind: np.zeros(space.count) for kind, space in spaces.items()}
    longitudinal_moment = {mode: np.zeros(2) for mode in MODES}
    longitudinal_inertia = np.zeros(2)
    shell_approx_sq = {mode:0. for mode in MODES[1:]}
    max_approx = {mode:0. for mode in MODES[1:]}
    area = 0.
    native = {(float(x),float(y)):_native_host(node,u,float(x),float(y))
              for x in NATIVE_X for y in NATIVE_Y}
    center_rot = .5*(rotation[2]+rotation[3])
    center_frame = Rotation.from_rotvec(center_rot).as_matrix()
    # The multiplier basis changes at .95 m. Segment there exactly as the
    # native line assembler does, while retaining the enclosing Q20 cell
    # for interpolation of the saved solid field.
    for sx0, sx1 in zip(CUTS[:-1], CUTS[1:]):
        ix = min(len(GRID)-2, int(np.searchsorted(GRID, (sx0+sx1)/2.)-1))
        x0, x1 = GRID[ix:ix+2]
        for sy0, sy1 in zip(Y_INTEGRATION_CUTS[:-1],
                            Y_INTEGRATION_CUTS[1:]):
            iy = min(len(YCUTS)-2,
                     int(np.searchsorted(YCUTS,(sy0+sy1)/2.)-1))
            y0,y1 = YCUTS[iy:iy+2]
            top = _face_nodes(node, u, float(x0), float(x1),
                              float(y0), float(y1), .0175)
            middle = _face_nodes(node, u, float(x0), float(x1),
                                 float(y0), float(y1), 0.)
            bottom = _face_nodes(node, u, float(x0), float(x1),
                                 float(y0), float(y1), -.0175)
            # E4 proxy uses only the four nodal midsurface translations and
            # through-thickness directors; the true solid face is quadratic.
            nodal_directors = np.array([
                _director(np.array((0.,0.,.035))+top[k]-bottom[k])
                for k in range(4)])
            for xi, wx in zip(roots, weights):
                x = (sx0+sx1)/2 + float(xi)*(sx1-sx0)/2
                f = (x-x0)/(x1-x0)
                parent_xi = 2.*f-1.
                move = (1-f)*translation[ix]+f*translation[ix+1]
                spin = (1-f)*rotation[ix]+f*rotation[ix+1]
                frame = Rotation.from_rotvec(spin).as_matrix()
                # Native pitch samples the director at y=0, independently
                # of the transverse position quadrature.
                qleft = (np.array((0.,0.,.035))+
                         u[node(float(x0),0.,.0175)]-u[node(float(x0),0.,-.0175)])
                qmid = (np.array((0.,0.,.035))+
                        u[node(float((x0+x1)/2),0.,.0175)]-
                        u[node(float((x0+x1)/2),0.,-.0175)])
                qright = (np.array((0.,0.,.035))+
                          u[node(float(x1),0.,.0175)]-u[node(float(x1),0.,-.0175)])
                axial = np.array((parent_xi*(parent_xi-1.)/2.,
                                  1.-parent_xi*parent_xi,
                                  parent_xi*(parent_xi+1.)/2.))
                direct = _director(axial[0]*qleft+axial[1]*qmid+axial[2]*qright)
                fine_direct = _director((1-f)*qleft+f*qright)
                ni = min(len(NATIVE_X)-2,
                         max(0,int(np.searchsorted(NATIVE_X,x,side="right")-1)))
                nx0,nx1 = NATIVE_X[ni:ni+2]
                nf = (x-nx0)/(nx1-nx0)
                native_direct = _director((1-nf)*native[(float(nx0),0.)][1]+
                                          nf*native[(float(nx1),0.)][1])
                for eta, wy in zip(roots, weights):
                    y = (sy0+sy1)/2 + float(eta)*(sy1-sy0)/2
                    parent_eta = 2.*(y-y0)/(y1-y0)-1.
                    shape = _quad8_shape(float(parent_xi),float(parent_eta))
                    true_u = shape@top
                    n4 = np.array(((1-parent_xi)*(1-parent_eta),
                                   (1+parent_xi)*(1-parent_eta),
                                   (1+parent_xi)*(1+parent_eta),
                                   (1-parent_xi)*(1+parent_eta)))/4.
                    fine_u = n4@(middle[:4]+.0175*(nodal_directors-np.array((0.,0.,1.))))
                    nj = min(len(NATIVE_Y)-2,
                             max(0,int(np.searchsorted(NATIVE_Y,y,side="right")-1)))
                    ny0,ny1 = NATIVE_Y[nj:nj+2]
                    nxi,neta = 2*nf-1,2*(y-ny0)/(ny1-ny0)-1
                    coarse_shape = np.array(((1-nxi)*(1-neta),(1+nxi)*(1-neta),
                                             (1+nxi)*(1+neta),(1-nxi)*(1+neta)))/4.
                    coarse_nodes = (native[(float(nx0),float(ny0))],
                                    native[(float(nx1),float(ny0))],
                                    native[(float(nx1),float(ny1))],
                                    native[(float(nx0),float(ny1))])
                    coarse_u = coarse_shape@np.array([
                        mid+.0175*(director-np.array((0.,0.,1.)))
                        for mid,director in coarse_nodes])
                    w = float(wx*wy*(sx1-sx0)*(sy1-sy0)/4.)
                    for mode,proxy in (("solid_cell_Q4_proxy",fine_u),
                                       ("native_host_Q4_proxy",coarse_u)):
                        delta = true_u-proxy
                        shell_approx_sq[mode] += w*float(delta@delta)
                        max_approx[mode] = max(max_approx[mode],
                                               float(np.linalg.norm(delta)))
                    area += w
                    beam_u = move+np.cross(spin, (0., y, -.05))
                    pitch = {
                        "actual_solid_face": float(np.arctan2(frame[:,0]@direct,
                                                               frame[:,2]@direct)),
                        "solid_cell_Q4_proxy": float(np.arctan2(frame[:,0]@fine_direct,
                                                                 frame[:,2]@fine_direct)),
                        "native_host_Q4_proxy": float(np.arctan2(frame[:,0]@native_direct,
                                                                  frame[:,2]@native_direct))}
                    for mode, shell_u in (("actual_solid_face",true_u),
                                          ("solid_cell_Q4_proxy",fine_u),
                                          ("native_host_Q4_proxy",coarse_u)):
                        gap = frame.T@(shell_u-beam_u)
                        segment = 0 if x < .95 else 1
                        arm_x = x-(.925 if segment == 0 else .975)
                        longitudinal_moment[mode][segment] -= w*arm_x*gap[2]
                        if mode == "actual_solid_face":
                            longitudinal_inertia[segment] += w*arm_x*arm_x
                        vals = np.r_[gap, y*gap[2], pitch[mode], -y*gap[0]]
                        for kind, space in spaces.items():
                            basis = space.values((x-.9)/.1)
                            for row, phi in enumerate(basis):
                                if phi == 0.: continue
                                sums[kind][mode][row] += w*phi*vals
                                if mode == "actual_solid_face":
                                    masses[kind][row] += w*phi
                                    inertias[kind][row] += w*phi*y*y
    if abs(area-.01)>1e-12:
        raise ArithmeticError("bond area differs from declared 0.01 m2")
    if not np.allclose(longitudinal_inertia,
                       np.full(2,.1*.05**3/12.),rtol=0.,atol=1e-12):
        raise ArithmeticError("longitudinal moment lost physical interval")
    out = {}
    for kind, space in spaces.items():
        if np.any(masses[kind] <= 0.) or np.any(inertias[kind] <= 0.):
            raise ArithmeticError("invalid native line normalization")
        entry = {"basis_integrals_m":(.1*masses[kind]/.01).tolist()}
        expected = ([.05,.05] if kind == "piecewise_constant"
                    else [.025,.05,.025])
        if not np.allclose(entry["basis_integrals_m"], expected,
                           rtol=0., atol=1e-12):
            raise ArithmeticError("line basis integration missed a knot")
        for mode in MODES:
            rows = sums[kind][mode]/masses[kind][:,None]
            rows[:,3] *= masses[kind]/inertias[kind]
            rows[:,5] *= masses[kind]/inertias[kind]
            entry[mode] = rows.tolist()
        out[kind] = entry
    return {"rows_by_space":out,
            "p0_longitudinal_position_My_probe_rad":{
                mode:(value/longitudinal_inertia).tolist()
                for mode,value in longitudinal_moment.items()},
            "p0_longitudinal_inertia_m4":longitudinal_inertia.tolist(),
            "solid_to_Q4_proxy_top_face_rms_m":{mode:float(np.sqrt(v/area))
                                                 for mode,v in shell_approx_sq.items()},
            "solid_to_Q4_proxy_top_face_max_m":max_approx,"area_m2":area,
            "quadrature_points":6*12*3*3,
            "meaning":"Each six-vector is the basis-weighted mean [Fx,Fy,Fz,Mx,My,Mz] gap under the native hybrid law; positions in m and pitch/moments in rad-like units. These are kinematic gaps, not force residuals or physical bond slip."}


def _native_longitudinal_rank() -> dict:
    """Check one P0 substitution against the actual supported native trace."""
    from scripts._b3_e4_f03_native_fixture import build
    from scripts.b3_e4_f03_distributed_surface_finite import (
        c1_hybrid_line_space, skew)
    from scripts.b3_e4_f03_plate_patch_work import local_grid
    from scripts.b3_e4_f03_square_section_control import square_torsion_constant

    xs,ys = local_grid(2,transverse_cells=4)
    beam = build(12,z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    original,_,patches = c1_hybrid_line_space(
        xs,ys,beam,kind="piecewise_constant")
    alternative = original.copy()
    shell_size = patches[0].shell_size
    for index,patch in enumerate(patches):
        state = beam.context.initial.mechanical
        center = sum(p.weight*p.x for p in patch.points)
        inertia = sum(p.weight*(p.x-center)**2 for p in patch.points)
        row = np.zeros(alternative.shape[1])
        for point in patch.points:
            _,_,frame = point.port.pose_pair(state)
            port = point.port.tangent(state)
            gap = np.zeros((3,alternative.shape[1]))
            for node,shape in zip(point.nodes,point.shape):
                j = 6*int(node)
                gap[:,j:j+3] += shape*np.eye(3)
                gap[:,j+3:j+6] -= shape*skew(
                    np.array((0.,0.,patch.top)))
            gap[:,shell_size:] -= np.column_stack((
                np.eye(3),-skew(frame@np.array((0.,point.y,-.05)))))@port
            row -= point.weight*(point.x-center)*(frame.T@gap)[2]/inertia
        alternative[6*index+4] = row
    fixed_shell = {6*j*len(xs)+a for j in range(len(ys)) for a in range(6)}
    fixed_beam = {shell_size+i for i in beam.context.fixed}
    free = [j for j in range(original.shape[1])
            if j not in fixed_shell and j not in fixed_beam]
    result = {}
    for name,matrix in (("original_director_pitch",original),
                        ("longitudinal_position_substitution",alternative)):
        supported = matrix[:,free]
        normalized = supported/np.linalg.norm(supported,axis=1)[:,None]
        left,singular,_ = np.linalg.svd(normalized,full_matrices=False)
        result[name] = {"full_row_rank":int(np.linalg.matrix_rank(matrix)),
                        "supported_row_rank":int(np.linalg.matrix_rank(supported)),
                        "row_normalized_singular_min":float(singular[-1]),
                        "row_normalized_singular_max":float(singular[0]),
                        "smallest_left_mode":left[:,-1].tolist(),
                        "smallest_left_mode_residual":float(np.linalg.norm(
                            left[:,-1]@normalized))}
    if (result["original_director_pitch"]["supported_row_rank"] != 12 or
            result["longitudinal_position_substitution"]["supported_row_rank"] != 11 or
            result["longitudinal_position_substitution"]["smallest_left_mode_residual"]>1e-12):
        raise ArithmeticError("unexpected bounded native row dependence")
    return {"fixture":"C1 B3-12, Q4 bond x2/y4, fixed left shell edge and native beam root, P0 two intervals",
            "row_order":"[Fx,Fy,Fz,Mx,My,Mz] per interval; only My is replaced",
            "result":result,
            "interpretation":"The direct longitudinal-position My substitution is algebraically dependent on existing Fz rows in this native fixture. Row normalization tests dependence only; it is not a physically normed inf-sup measure or stability qualification.",
            "disposition":"REJECT_DIRECT_SUBSTITUTION"}


def _influence_split(base: Path, combined_x: np.ndarray,
                     combined_elements: dict, combined_u: dict,
                     combined_model: dict, combined_rows: dict) -> dict:
    """Attribute corrected rows to the two saved *linear* load influences."""
    stems = {
        "torque":base/"f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/solid-5-tip_mx/solid-5-tip_mx",
        "opening":base/"f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz/solid-5-tip_fz",
    }
    load_flags = {"applied_nodal_forces_N", "reverse_tip_fz", "shear",
                  "tip_mx_gap_audit", "torque_with_opening_fz"}
    def structure(model):
        return {k:v for k,v in model.items() if k not in load_flags}
    def loads(model):
        return {int(k):np.array(v) for k,v in
                model["applied_nodal_forces_N"].items()}
    if set(combined_u) != set(range(1,len(combined_x))):
        raise ValueError("combined displacement inventory incomplete")
    cases = {}
    fields = {}
    models = {}
    for label,stem in stems.items():
        inp,frd,metadata = (stem.with_suffix(".inp"),
                            stem.with_suffix(".frd"),
                            stem.parent/"model.json")
        xyz,elements = read_deck(inp)
        if not np.array_equal(xyz,combined_x) or any(
                not np.array_equal(elements[k],combined_elements[k])
                for k in combined_elements):
            raise ValueError("load influences do not share solid geometry")
        model = json.loads(metadata.read_text())
        if structure(model) != structure(combined_model):
            raise ValueError("load influences differ in support or model definition")
        u = _read_frd_u(frd)
        if set(u) != set(combined_u):
            raise ValueError("load influence displacement inventory differs")
        coords = {i:xyz[i] for i in range(1,len(xyz))}
        move,spin,fit_rms = _ports(coords,u,elements,method="area")
        report = _integrate(coords,u,move,spin)
        cases[label] = {
            "p0_rows_by_surface":{
                mode:report["rows_by_space"]["piecewise_constant"][mode]
                for mode in MODES},
            "fit_vector_rms_m":fit_rms.tolist(),
            "source_sha256":{str(p.relative_to(base)):_sha(p)
                             for p in (inp,frd,metadata)},
            "interpretation":("pure torque is a linear influence only; "
                              "its zero-preload gap closes" if label=="torque"
                              else "pure opening is the admissible load influence")}
        fields[label],models[label] = u,model
    all_nodes = set().union(*(loads(model) for model in
                              (models["torque"],models["opening"],combined_model)))
    force_difference = max(float(np.linalg.norm(
        loads(models["torque"]).get(n,np.zeros(3))+
        loads(models["opening"]).get(n,np.zeros(3))-
        loads(combined_model).get(n,np.zeros(3)))) for n in all_nodes)
    if force_difference > 1e-10:
        raise ArithmeticError("declared combined loads do not superpose")
    field_difference = max(float(np.linalg.norm(
        fields["torque"][n]+fields["opening"][n]-combined_u[n]))
        for n in combined_u)
    field_scale = max(float(np.linalg.norm(u)) for u in combined_u.values())
    if field_difference > 2e-5*field_scale+5e-10:
        raise ArithmeticError("saved linear fields do not superpose")
    row_differences = {}
    for mode in MODES:
        torque = np.array(cases["torque"]["p0_rows_by_surface"][mode])
        opening = np.array(cases["opening"]["p0_rows_by_surface"][mode])
        combined = np.array(combined_rows["piecewise_constant"][mode])
        row_differences[mode] = float(np.max(np.abs(torque+opening-combined)))
    return {"same_structure_and_support":True,
            "max_declared_nodal_load_sum_difference_N":force_difference,
            "max_saved_displacement_superposition_difference_m":field_difference,
            "displacement_superposition_bound_m":2e-5*field_scale+5e-10,
            "max_P0_weak_row_superposition_difference_by_surface":row_differences,
            "cases":cases,
            "interpretation":"This attributes saved linear influences under identical geometry, support and load maps. Pure torque remains contact-inadmissible without pre-opening; only the combined field carries the archived opposed-face admissibility screen."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    base = root.parent
    replay = base/"f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1"
    paths = [replay/"solid-5-tip_mx.inp", replay/"solid-5-tip_mx.frd",
             base/"f03-c1-factor5-stress-force-recovery-dev-20260926-v1/result.json",
             base/"f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx/model.json"]
    accepted = json.loads(paths[2].read_text())
    if accepted["validation"]["status"] != "PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS":
        raise ValueError("validated saved solid predecessor required")
    xyz, elements = read_deck(paths[0])
    coords = {i:xyz[i] for i in range(1,len(xyz))}
    u = _read_frd_u(paths[1])
    if set(coords)!=set(u):
        raise ValueError("incomplete saved displacement field")
    reports = {}
    for fit in ("area", "nonbond"):
        translation, rotation, rms = _ports(coords,u,elements,method=fit)
        reports[fit] = _integrate(coords,u,translation,rotation)
        reports[fit]["section_vector_rms_fit_m"] = rms.tolist()
    zero = {n:np.zeros(3) for n in coords}
    reference = _integrate(coords,zero,np.zeros((6,3)),np.zeros((6,3)))
    max_ref = max(abs(v) for entry in reference["rows_by_space"].values()
                  for mode in MODES
                  for row in entry[mode] for v in row)
    if max_ref > 1e-12:
        raise ArithmeticError("nonzero native reference gap")
    rank = _native_longitudinal_rank()
    split = _influence_split(base,xyz,elements,u,
                             json.loads(paths[3].read_text()),
                             reports["area"]["rows_by_space"])
    result = {"classification":"bounded saved-field native six-gap projection and P0 substitution rank; no G0B acceptance",
              "question":"Does the native six-channel line law fit this physically bonded 3D field within section-port and E4-reduction uncertainty?",
              "outcome_rule":"Compare the director-pitch My row with a separate longitudinal-position moment on the same saved bond. If the latter is small and independently rank-valid on the native fixture, derive and test its full finite work law before any basis ranking; if it is large or dependent, prioritize section/end-load idealization. Neither result qualifies a law by itself.",
              "geometry":"F5 35 mm C1 plate, 100 mm square bar, terminal x=.9–1.0 m shared-node bond, +100 Nm/−1000 N pre-opened combined load; no new external solve",
              "fit_assumptions":"linear interpolation of six rigid solid-section fits at .02 m stations; inferred director is the deformed top-bottom thickness chord; Q4 proxies use solid-cell or actual native 0.05 by 0.025 m hosts with inferred nodal directors; actual solid face uses Q20 interpolation; integration splits at native x=.95 m and y=±.025 m host cuts",
              "reference_max_abs_gap":max_ref,"results":reports,
              "longitudinal_substitution_rank":rank,
              "saved_linear_influence_split":split,
              "limits":["3D-to-E4 director is inferred, not an independent E4 state",
                        "linear rigid-section interpolation is not a native B3 interpolation",
                        "the six weak rows can vanish despite local nonzero gap",
                        "the P0 longitudinal moment is a diagnostic only: no finite law, rank, or stability qualification is implied",
                        "combined load alone does not isolate pure torque",
                        "positive gap audit covers only declared opposed faces"],
              "inputs_sha256":{str(p.relative_to(base)):_sha(p) for p in paths},
              "runner_sha256":_sha(Path(__file__))}
    root.mkdir(parents=True)
    (root/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"reference_max_abs_gap":max_ref,
                      "area_p0":reports["area"]["rows_by_space"]["piecewise_constant"]["native_host_Q4_proxy"],
                      "nonbond_p0":reports["nonbond"]["rows_by_space"]["piecewise_constant"]["native_host_Q4_proxy"]},indent=2))


if __name__ == "__main__":
    main()
