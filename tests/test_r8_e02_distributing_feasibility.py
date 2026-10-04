"""Deck/action and strict output controls, without launching CalculiX."""
import json

import numpy as np
import pytest

from scripts.r8_e02_distributing_feasibility import LOADS, PORT, build_case, parse_result
from scripts.r8_e02_rigid_tip_reference import ReferenceParseError


@pytest.fixture(scope="module")
def cases():
    return {name: build_case(name) for name in LOADS}


def _synthetic(metadata):
    text = " displacements (vx,vy,vz) for set ALL and time 1.0000000E+00\n\n"
    text += "".join(f"{n} 0.0000000E+00 0.0000000E+00 0.0000000E+00\n"
                    for n in metadata["physical_nodes"])
    text += "\n forces (fx,fy,fz) for set ROOT and time 1.0000000E+00\n\n"
    text += "".join(f"{n} 0.0000000E+00 0.0000000E+00 0.0000000E+00\n"
                    for n in metadata["root_nodes"])
    stdout = "CalculiX Version 2.23,\n Using up to 1 cpu(s)\n Job finished\n"
    return text, stdout


@pytest.mark.parametrize("name", tuple(LOADS))
def test_deck_has_common_action_without_rigid_patch_or_extra_port_nodes(cases, name):
    deck, metadata, area = cases[name]
    assert "*RIGID BODY" not in deck and "*EQUATION" not in deck
    assert "ROOT,1,3,0." in deck
    node_section = deck.split("*NODE\n", 1)[1].split("*ELEMENT", 1)[0]
    assert len(node_section.splitlines()) == len(metadata["physical_nodes"])
    loads = deck.split("*CLOAD\n", 1)[1].split("*NODE PRINT", 1)[0]
    actual = {}
    for row in loads.splitlines():
        n, j, v = row.split(",")
        actual.setdefault(int(n), np.zeros(3))[int(j)-1] = float(v)
    action = area.action(LOADS[name][:3], LOADS[name][3:])
    for n, f in zip(action.node_ids, action.forces_n):
        np.testing.assert_array_equal(actual.get(n, np.zeros(3)), f)
    force, moment = action.resultant()
    np.testing.assert_allclose(force, LOADS[name][:3], atol=2e-12, rtol=0)
    np.testing.assert_allclose(moment,
        np.array(LOADS[name][3:])+np.cross(PORT, LOADS[name][:3]), atol=2e-12, rtol=0)


@pytest.mark.parametrize("nx,ny", ((20,8),(40,16)))
def test_reference_refinement_keeps_physical_area_wrench_and_complete_trace(nx,ny):
    deck, metadata, area = build_case("Mx",nx,ny)
    assert metadata["nx"]==nx and metadata["ny"]==ny
    assert len(metadata["elements"])==2*nx*ny
    np.testing.assert_allclose(area.centroid_m,(.9,-.025,0.),atol=1e-16,rtol=0)
    assert area.area_m2 == pytest.approx(.01,abs=1e-17)
    assert "*RIGID BODY" not in deck
    action = area.action((0.,10.,0.),(0.,0.,0.))
    np.testing.assert_allclose(action.resultant()[0],(0.,10.,0.),atol=2e-12,rtol=0)
    np.testing.assert_allclose(action.resultant()[1],(-.5,0.,9.),atol=2e-12,rtol=0)


def test_parser_metadata_roundtrip_and_no_acceptance_inference(cases):
    _, metadata, _ = cases["Mx"]
    dat, stdout = _synthetic(metadata)
    result = parse_result(dat, stdout, json.loads(json.dumps(metadata)))
    assert result["status"] == "PARSED_DEVELOPMENT_ONLY"
    assert result["root_wrench_error"][3] == 1.  # Fake zero reactions are not accepted.
    assert result["pairing_print_bound_J"] > 0
    assert result["external_final_pairing_J"] == 0


def test_nonzero_parsed_rigid_field_work_and_root_couple(cases):
    _, metadata, _ = cases["Mx"]
    translation, spin = np.array((1e-6,-2e-6,3e-6)), np.array((1e-5,-2e-5,3e-5))
    fields = {n:translation+np.cross(spin,p) for n,p in metadata["physical_nodes"].items()}
    forces = {n:np.zeros(3) for n in metadata["root_nodes"]}
    for z, fy in ((.01,50.),(-.01,-50.)):
        node, = [n for n in forces if metadata["physical_nodes"][n]==(0.,0.,z)]
        forces[node][1] = fy  # Unit negative root Mx, zero force.
    def section(name, field, vectors):
        return (f" {field} (x,y,z) for set {name} and time 1.0000000E+00\n\n"+
                "".join(str(n)+" "+" ".join(f"{v:.7E}" for v in xyz)+"\n"
                        for n,xyz in vectors.items()))
    dat = section("ALL","displacements",fields)+section("ROOT","forces",forces)
    _, stdout = _synthetic(metadata)
    result = parse_result(dat,stdout,metadata)
    observed = result["observable"]
    np.testing.assert_allclose(observed["rotation_components_rad"],spin,atol=2e-12,rtol=0)
    np.testing.assert_allclose(observed["port_translation_m"],
        translation+np.cross(spin,PORT),atol=2e-12,rtol=0)
    assert abs(result["external_final_pairing_J"]-spin[0]) <= result["pairing_print_bound_J"]+1e-18
    np.testing.assert_allclose(result["root_wrench_error"],np.zeros(6),atol=1e-13,rtol=0)
    assert all(v>0 for v in result["root_wrench_print_bounds"])


@pytest.mark.parametrize("defect", ("metadata", "duplicate", "missing", "nan", "unfinished", "threads", "version", "warning"))
def test_parser_rejects_unbound_or_incomplete_outputs(cases, defect):
    _, original, _ = cases["Mx"]
    metadata = json.loads(json.dumps(original))
    dat, stdout = _synthetic(original)
    if defect == "metadata":
        metadata["port_m"][2] += .01
    elif defect == "duplicate":
        first = dat.splitlines()[2]
        dat = dat.replace(first, first+"\n"+first, 1)
    elif defect == "missing":
        dat = dat.replace(dat.splitlines()[2]+"\n", "", 1)
    elif defect == "nan":
        dat = dat.replace("0.0000000E+00", "nan", 1)
    elif defect == "unfinished":
        stdout = stdout.replace("Job finished", "")
    elif defect == "threads":
        stdout = stdout.replace("1 cpu", "2 cpu")
    elif defect == "version":
        stdout = stdout.replace("2.23", "2.22")
    else:
        stdout += "WARNING\n"
    with pytest.raises(ReferenceParseError):
        parse_result(dat, stdout, metadata)
