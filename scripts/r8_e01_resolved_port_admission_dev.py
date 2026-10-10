"""Source-only admission of the detached E01 CalculiX port recipe.

This inspects generated text; it neither launches CalculiX nor turns a finite
rigid patch into the native B3/Q4 point law. A positive source check is not E01
accuracy evidence.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import inspect
import json
from math import isclose, pi, tanh
from pathlib import Path

import numpy as np

from scripts import r8_e01_resolved_port_reference_dev as reference
from scripts import b3_e4_e01_native_point_refinement_screen as native


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "scripts/b3_e4_e01_native_point_refinement_screen.py"
RECOVERY = ROOT / "scripts/r8_e01_resolved_port_weak_recovery.py"
STATIONS = (0, 1000, 2000)
NATIVE_AREA = .01
NATIVE_SHEAR_AREA = .008
NATIVE_I = 8.333333333333333e-6
NATIVE_J = 1.6666666666666667e-5


class SourceRefusal(ValueError):
    """The emitted source does not meet its own declared E01 map."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise SourceRefusal(reason)


def _records(deck: str) -> dict:
    """Read the cards on which this admission depends, rejecting ambiguity."""
    lines = [line.strip() for line in deck.splitlines() if line.strip()]
    out = dict(nodes={}, elements={"Plate": {}, "BeamSolid": {}}, sets={},
               rigid={}, equations=[], surfaces={}, boundary=[], loads=[],
               section_print={}, node_print={}, elastic=None, solid_sections={},
               materials=set())
    i = 0
    while i < len(lines):
        head = lines[i]
        if not head.startswith("*"):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("*"):
            j += 1
        body = lines[i + 1:j]
        if head == "*NODE":
            for row in body:
                v = row.split(",")
                require(len(v) == 4, "node record arity")
                n = int(v[0])
                require(n not in out["nodes"], "duplicate node")
                out["nodes"][n] = np.array([float(x) for x in v[1:]])
        elif head.startswith("*ELEMENT,TYPE=C3D20R,ELSET="):
            name = head.split("ELSET=", 1)[1]
            require(name in out["elements"], "unexpected constituent")
            pending = []
            for row in body:
                pending.extend(int(x) for x in row.split(",") if x)
                if len(pending) == 21:
                    n = pending[0]
                    require(n not in out["elements"][name], "duplicate element")
                    out["elements"][name][n] = tuple(pending[1:])
                    pending = []
                else:
                    require(len(pending) < 21, "invalid C3D20R connectivity")
            require(not pending, "incomplete C3D20R connectivity")
        elif head.startswith("*NSET,NSET="):
            name = head.split("NSET=", 1)[1]
            require(name not in out["sets"], "duplicate node set")
            out["sets"][name] = {int(x) for row in body for x in row.split(",") if x}
        elif head.startswith("*RIGID BODY,NSET="):
            fields = dict(part.split("=", 1) for part in head.split(",")[1:])
            name = fields["NSET"]
            require(name not in out["rigid"], "duplicate rigid port")
            out["rigid"][name] = (int(fields["REF NODE"]), int(fields["ROT NODE"]))
        elif head == "*EQUATION":
            require(len(body) == 2, "equation card arity")
            count = int(body[0])
            data = body[1].split(",")
            require(len(data) == 3 * count, "equation term count")
            row = tuple((int(data[3*k]), int(data[3*k+1]), float(data[3*k+2]))
                        for k in range(count))
            out["equations"].append(row)
        elif head.startswith("*SURFACE,NAME="):
            name = head.split("NAME=", 1)[1].split(",", 1)[0]
            require(name not in out["surfaces"], "duplicate cut surface")
            out["surfaces"][name] = tuple((int(v[0]), v[1])
                                           for row in body for v in [row.split(",")])
        elif head == "*BOUNDARY":
            out["boundary"].extend(body)
        elif head == "*CLOAD":
            out["loads"].extend(tuple((int(v[0]), int(v[1]), float(v[2])))
                                for row in body for v in [row.split(",")])
        elif head.startswith("*SECTION PRINT,SURFACE="):
            name = head.split("SURFACE=", 1)[1].split(",", 1)[0]
            out["section_print"][name] = tuple(body)
        elif head.startswith("*NODE PRINT,NSET="):
            name = head.split("NSET=", 1)[1]
            out["node_print"][name] = tuple(body)
        elif head == "*ELASTIC":
            require(out["elastic"] is None and len(body) == 1,
                    "material elasticity card")
            out["elastic"] = tuple(float(x) for x in body[0].split(","))
        elif head.startswith("*SOLID SECTION,ELSET="):
            fields = dict(part.split("=", 1) for part in head.split(",")[1:])
            name = fields["ELSET"]
            require(name not in out["solid_sections"], "duplicate solid section")
            out["solid_sections"][name] = fields.get("MATERIAL")
        elif head.startswith("*MATERIAL,NAME="):
            name = head.split("NAME=", 1)[1]
            require(name not in out["materials"], "duplicate material")
            out["materials"].add(name)
        i = j
    return out


def _cross(r: np.ndarray) -> np.ndarray:
    x, y, z = r
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _rows_for_station(model: dict, station: int) -> np.ndarray:
    start = STATIONS.index(station) * 6
    names = (f"ShellPort{station}", f"BeamPort{station}")
    sr, st = model["rigid"][names[0]]
    br, bt = model["rigid"][names[1]]
    dofs = [(sr, d) for d in (1, 2, 3)] + [(st, d) for d in (1, 2, 3)]
    dofs += [(br, d) for d in (1, 2, 3)] + [(bt, d) for d in (1, 2, 3)]
    columns = {entry: k for k, entry in enumerate(dofs)}
    C = np.zeros((6, 12))
    for i, row in enumerate(model["equations"][start:start+6]):
        for n, d, value in row:
            require((n, d) in columns, "equation refers to wrong port or DOF")
            k = columns[(n, d)]
            require(C[i, k] == 0., "duplicate equation coefficient")
            C[i, k] = value
    return C


def _virtual_work_control(C: np.ndarray, shell_x: np.ndarray,
                          beam_x: np.ndarray) -> None:
    r = beam_x - shell_x
    canonical = np.zeros((6, 12))
    canonical[:3, :3] = -np.eye(3)
    canonical[:3, 3:6] = _cross(r)
    canonical[:3, 6:9] = np.eye(3)
    canonical[3:, 3:6] = -np.eye(3)
    canonical[3:, 9:12] = np.eye(3)
    require(np.max(np.abs(C-canonical)) <= 2e-15, "wrong signed six-row map")
    require(np.linalg.matrix_rank(C) == 6, "six-row map rank")
    # Six global rigid fields and six independent compatible affine port poses.
    for j in range(6):
        t, omega = np.eye(6)[j, :3], np.eye(6)[j, 3:]
        q = np.r_[t+np.cross(omega, shell_x), omega,
                  t+np.cross(omega, beam_x), omega]
        require(np.max(np.abs(C @ q)) <= 2e-15, "global rigid-field gap")
        q = np.r_[t, omega, t+np.cross(omega, r), omega]
        require(np.max(np.abs(C @ q)) <= 2e-15, "compatible affine-port gap")
        # Each row dual must do exactly the work of its signed side forces.
        lam = np.eye(6)[j]
        f = C.T @ lam
        arbitrary = np.array((.2, -.3, .4, -.7, .8, -.9,
                              .11, -.12, .13, .21, -.22, .23))
        require(abs(f @ arbitrary - lam @ (C @ arbitrary)) < 3e-16,
                "signed side transpose work")
        require(np.linalg.norm(f[:3]+f[6:9], np.inf) < 2e-15,
                "side forces do not cancel")
        require(np.linalg.norm(f[3:6]+f[9:12]+np.cross(r, f[6:9]), np.inf) < 2e-15,
                "side moments do not balance at shell station")


def _check_cuts(model: dict) -> None:
    expected = {f"{side}{station}{direction}Cut": (side, station, direction)
                for side in ("Plate", "Beam")
                for station, direction in ((0, "Right"), (1000, "Left"),
                                           (1000, "Right"), (2000, "Left"))}
    require(set(model["surfaces"]) == set(expected), "missing/extra sided cut")
    require(set(model["section_print"]) == set(expected), "missing cut output")
    for name, (side, station, direction) in expected.items():
        require(model["section_print"][name] == ("SOF",), "cut output is not SOF")
        entries = model["surfaces"][name]
        require(len(entries) == (10 if side == "Plate" else 4),
                "incomplete cut element coverage")
        face = "S4" if direction == "Left" else "S6"
        domain = model["elements"]["Plate" if side == "Plate" else "BeamSolid"]
        rectangles = set()
        area = 0.
        for element, actual_face in entries:
            require(actual_face == face and element in domain, "wrong cut side or domain")
            xyz = np.array([model["nodes"][n] for n in domain[element][:8]])
            pts = xyz[[1, 2, 6, 5] if face == "S4" else [0, 3, 7, 4]]
            require(np.max(np.abs(pts[:, 0]-station/1000.)) <= 1e-15,
                    "cut is at wrong station")
            require(np.sign(pts[:, 0].mean()-xyz[:, 0].mean()) ==
                    (1 if face == "S4" else -1), "wrong cut normal")
            rect = tuple(float(v) for v in (pts[:, 1].min(), pts[:, 1].max(),
                                            pts[:, 2].min(), pts[:, 2].max()))
            require(rect not in rectangles, "duplicate cut patch")
            rectangles.add(rect)
            area += (rect[1]-rect[0])*(rect[3]-rect[2])
        require(isclose(area, .07 if side == "Plate" else .01,
                        rel_tol=0., abs_tol=1e-14), "cut area is incomplete")


def source_controls(deck: str, info: dict, sign: int, load: str) -> dict:
    """Check a candidate independently of the generator's metadata assertions."""
    require(sign in (-1, 1) and load in ("fy", "mx"), "undeclared case")
    m = _records(deck)
    require(info["sign"] == sign and info["load"] == load and
            info["identity"] == "R8_E01_RESOLVED_PORT_INERT_V1", "case identity mismatch")
    require(len(m["equations"]) == 18 and len(m["rigid"]) == 6,
            "wrong port/equation count")
    require(m["elastic"] == (reference.E, reference.NU) and
            m["materials"] == {"Isotropic"} and
            m["solid_sections"] == {"Plate": "Isotropic", "BeamSolid": "Isotropic"},
            "material or solid-section assignment mismatch")
    require(len(m["elements"]["Plate"]) == 120 and
            len(m["elements"]["BeamSolid"]) == 48, "wrong constituent mesh")
    nodes = m["nodes"]
    plate_ids = {n for cell in m["elements"]["Plate"].values() for n in cell}
    beam_ids = {n for cell in m["elements"]["BeamSolid"].values() for n in cell}
    require(not plate_ids & beam_ids, "merged shell/beam node ownership")
    require(len(plate_ids) == info["plate_nodes"] and
            len(beam_ids) == info["beam_nodes"], "constituent node inventory")
    for ids, lo, hi in ((plate_ids, (0., -.5, -.035), (2., .5, .035)),
                        (beam_ids, (0., -.55, sign*.1-.05),
                         (2., -.45, sign*.1+.05))):
        ext = np.array([nodes[n] for n in ids])
        require(np.max(np.abs(ext.min(axis=0)-lo)) <= 1e-15 and
                np.max(np.abs(ext.max(axis=0)-hi)) <= 1e-15,
                "constituent geometry/frame mismatch")
    port_names = {f"{side}Port{station}" for side in ("Shell", "Beam")
                  for station in STATIONS}
    require(set(m["rigid"]) == port_names, "missing or extra rigid station")
    patches = []
    for station in STATIONS:
        sr, st = m["rigid"][f"ShellPort{station}"]
        br, bt = m["rigid"][f"BeamPort{station}"]
        x = station/1000.
        for n, target in ((sr, (x, -.5, 0.)), (st, (x, -.5, 0.)),
                          (br, (x, -.5, sign*.1)), (bt, (x, -.5, sign*.1))):
            require(n in nodes and np.max(np.abs(nodes[n]-target)) <= 1e-15,
                    "port station/frame mismatch")
        sp, bp = m["sets"][f"ShellPort{station}"], m["sets"][f"BeamPort{station}"]
        require(len(sp) == 13 and len(bp) == 21 and
                sp <= plate_ids and bp <= beam_ids, "wrong finite port patch")
        require(all(abs(nodes[n][1]+.5) <= 1e-15 for n in sp) and
                all(abs(nodes[n][0]-x) <= 1e-15 for n in bp),
                "wrong patch location")
        patches.append((sp, bp))
        _virtual_work_control(_rows_for_station(m, station), nodes[sr], nodes[br])
    require(all(not patches[i][side] & patches[j][side]
                for side in (0, 1) for i in range(3) for j in range(i+1, 3)),
            "overlapping port patches")
    root = {n for n in plate_ids if abs(nodes[n][0]) <= 1e-15}
    root_free = m["sets"]["PlateRootFree"]
    require(root_free | (patches[0][0] & root) == root and
            not root_free & patches[0][0], "root shell support coverage")
    sr, st = m["rigid"]["ShellPort0"]
    require(set(m["boundary"]) == {"PlateRootFree,1,3", f"{sr},1,3", f"{st},1,3"},
            "root constraint differs from declared continuum root")
    br, bt = m["rigid"]["BeamPort2000"]
    expect_load = (br, 2, 1000.) if load == "fy" else (bt, 1, 100.)
    require(m["loads"] == [expect_load], "tip load/rotation measure mismatch")
    require(m["node_print"].get("AllPorts") == ("U", "RF") and
            m["node_print"].get("PlateRootFree") == ("RF",),
            "missing declared port/root printed fields")
    _check_cuts(m)
    return dict(sign=sign, load=load, deck_sha256=sha256(deck.encode("ascii")).hexdigest(),
                stations_m=[0., 1., 2.], equations=18, port_patches=6,
                complete_oriented_cuts=8, rigid_and_affine_fields_per_station=12,
                six_dual_work_rows_per_station=6, status="SOURCE_CONTROLS_PASS")


def square_st_venant_j(side: float, terms: int = 101) -> float:
    """Prismatic square elastic-torsion constant, not polar area moment."""
    require(side > 0 and terms >= 31, "torsion series parameters")
    series = sum(tanh(n*pi/2)/n**5 for n in range(1, 2*terms, 2))
    return side**4/3 * (1 - 192/pi**5 * series)


def native_definition_controls(sign: int) -> dict:
    """Inspect current native construction and retained section without a solve."""
    model, tip = native.definition(2, sign)
    shell = model.shell
    require(len(shell.q4_elements) == 2 and shell.thickness_m == .07 and
            shell.young_pa == reference.E and shell.poisson == reference.NU,
            "native shell geometry/material drift")
    xyz = np.asarray(shell.coordinates_m)
    require(np.max(np.abs(xyz.min(axis=0)-(0., -.5, 0.))) <= 1e-15 and
            np.max(np.abs(xyz.max(axis=0)-(2., .5, 0.))) <= 1e-15,
            "native shell extent drift")
    require(len(model.points) == 3 and len(model.beams) == 2 and tip == 105 and
            tuple((p.shell_node, p.beam_node) for p in model.points) ==
            ((1, 101), (2, 103), (3, 105)),
            "native station/beam count drift")
    require(len(model.fixed) == 12 and
            {(v.domain, v.node, v.component) for v in model.fixed} ==
            {("shell", node, c) for node in (1, 4) for c in range(6)},
            "native root support map drift")
    for i, beam in enumerate(model.beams):
        data = json.loads(beam.raw)
        expected_x = (float(i), float(i)+.5, float(i)+1.)
        coords = np.asarray(data["reference"]["coordinates"])
        require(np.max(np.abs(coords[:, 0]-expected_x)) <= 1e-15 and
                np.max(np.abs(coords[:, 1]+.5)) <= 1e-15 and
                np.max(np.abs(coords[:, 2]-sign*.1)) <= 1e-15,
                "native beam centroid/frame drift")
        require(np.max(np.abs(np.asarray(data["reference"]["nodal_triads"])-np.eye(3))) <= 1e-15,
                "native beam triad drift")
        elastic = np.asarray(data["section"]["elastic"])
        G = reference.E/(2*(1+reference.NU))
        expected = reference.E*np.array((NATIVE_AREA, 0., 0., 0., NATIVE_I, NATIVE_I))
        expected[1:4] = G*np.array((NATIVE_SHEAR_AREA, NATIVE_SHEAR_AREA, NATIVE_J))
        require(elastic.shape == (6, 6) and
                np.max(np.abs(elastic-np.diag(np.diag(elastic)))) == 0. and
                np.allclose(np.diag(elastic), expected, rtol=1e-14, atol=0.),
                "native six-resultant section drift")
    return dict(sign=sign, shell_cells=2, stations=[0., 1., 2.],
                shell_root_nodes=[1, 4], beam_tip_node=tip,
                section_diag=list(expected), native_load=_native_declared_tip_load())


def _native_declared_tip_load() -> tuple[float, ...]:
    """Bind the source-level NodalAction without calling native.solve()."""
    tree = ast.parse(inspect.getsource(native.solve))
    actions = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Name) and node.func.id == "NodalAction"]
    require(len(actions) == 1 and len(actions[0].args) == 3,
            "native tip action source changed")
    action = actions[0]
    require(ast.literal_eval(action.args[0]) == "beam" and
            isinstance(action.args[1], ast.Name) and action.args[1].id == "tip_node",
            "native tip action owner changed")
    load = tuple(float(v) for v in ast.literal_eval(action.args[2]))
    require(load == (1000., 0., 0., 0., 0., 0.),
            "native tip action measure changed")
    return load


def section_and_output_decision() -> dict:
    side = reference.BEAM_SIDE_M
    E = reference.E
    G = E/(2*(1+reference.NU))
    area, inertia = side**2, side**4/12
    j_sv = square_st_venant_j(side)
    j_polar = 2*inertia
    require(isclose(area, NATIVE_AREA, rel_tol=1e-13) and
            isclose(inertia, NATIVE_I, rel_tol=1e-13), "EA/EI geometric mismatch")
    require(isclose(j_polar, NATIVE_J, rel_tol=1e-13),
            "native GJ identity changed; re-evaluate declared section")
    blockers = [
        "Solid square Saint-Venant GJ differs from native G times its polar-area J; no section-equivalent torsion calibration.",
        "Native GAy/GAz use 0.008 m2; solid effective shear compliance is unmeasured and cannot be inferred from area alone.",
        "25 mm rigid shell patches and solid clamped root are not the native zero-footprint Q4/B3 point/support idealization.",
        "The generator has Fy and Mx controls, but no native beam-tip Fx load case.",
        "SOF adjacent cut pairs and RF inventory do not establish separately measured six-channel constraint duals; rounded-FRD weak reconstruction is not an independent sided-action output.",
    ]
    return dict(native=dict(EA_N=E*NATIVE_AREA, GAy_N=G*NATIVE_SHEAR_AREA,
                            GAz_N=G*NATIVE_SHEAR_AREA, GJ_Nm2=G*NATIVE_J,
                            EIy_Nm2=E*NATIVE_I, EIz_Nm2=E*NATIVE_I),
                solid_geometry=dict(area_m2=area, Iy_m4=inertia, Iz_m4=inertia,
                                    polar_J_m4=j_polar, Saint_Venant_J_m4=j_sv,
                                    Saint_Venant_to_native_J_ratio=j_sv/NATIVE_J,
                                    effective_shear_area_m2="unverified"),
                physical_admission=False, sided_action_admission=False,
                blockers=blockers)


def refuse_sided_claim(basis: str) -> None:
    """No source-only self-reported or cancelling-only basis is an action oracle."""
    raise SourceRefusal(f"independent sided six-wrench/work absent: {basis}")


def audit() -> dict:
    cases = []
    for sign in (1, -1):
        native_definition_controls(sign)
        for load in ("fy", "mx"):
            deck, info = reference.build(sign, load)
            cases.append(source_controls(deck, info, sign, load))
    dependencies = {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                    for path in (Path(reference.__file__).resolve(), NATIVE, RECOVERY)}
    return dict(identity="R8_E01_RESOLVED_PORT_ADMISSION_SOURCE_V1",
                source_controls="PASS", cases=cases,
                native_source_controls=[native_definition_controls(s) for s in (1, -1)],
                section_and_output=section_and_output_decision(),
                source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                dependencies_sha256=dependencies,
                numerical_children=0, E01_accuracy_acceptance=False)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve existing E01 admission evidence")
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(identity=result["identity"], source_controls="PASS",
                          physical_admission=False, blockers=len(result["section_and_output"]["blockers"]))))


if __name__ == "__main__":
    main()
