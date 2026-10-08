"""Element energy is parsed as a domain partition, not interface work."""

from hashlib import sha256
import json
import sys

import pytest

from scripts import b3_e4_f03_ccx_energy_partition as energy
from scripts.b3_e4_f03_ccx_energy_partition import parse_partition
from scripts.b3_e4_f03_ccx_matched_t_reference import build_bundle


def _dat():
    return ("internal energy (element, energy) for set PLATE and time  1E+00\n"
            "\n  1  2E-01\n  2  3E-01\n\n"
            "internal energy (element, energy) for set WEB and time  1E+00\n"
            "\n  3  5E-01\n\n")


def test_partition_and_applied_work_balance():
    result = parse_partition(_dat(), 2, 1, 2.)
    assert result["plate_energy_j"] == pytest.approx(.5)
    assert result["web_energy_j"] == pytest.approx(.5)
    assert result["energy_balance_relative"] < 1e-14
    assert result["plate_fraction"] == pytest.approx(.5)


def test_duplicate_missing_and_nonfinite_energy_rejected():
    with pytest.raises(ValueError, match="repeated"):
        parse_partition(_dat()+_dat(), 2, 1, 2.)
    with pytest.raises(ValueError, match="incomplete"):
        parse_partition(_dat().replace("  3  5E-01\n", ""), 2, 1, 2.)
    with pytest.raises(ValueError, match="invalid"):
        parse_partition(_dat().replace("2E-01", "NaN"), 2, 1, 2.)


def test_cli_binds_deck_manifest_frd_and_work(tmp_path, monkeypatch, capsys):
    original, manifest = build_bundle("flat", "plate_fy", 4, "clamped",
                                      "native_line_geometry")
    changed = original.replace(
        "*END STEP\n", "*EL PRINT,ELSET=Plate\nELSE\n"
        "*EL PRINT,ELSET=Web\nELSE\n*END STEP\n")
    paths = {name: tmp_path/name for name in
             ("manifest.json", "energy.inp", "solution.frd", "solution.dat")}
    paths["manifest.json"].write_text(json.dumps(manifest))
    paths["energy.inp"].write_bytes(changed.encode("ascii"))
    paths["solution.frd"].write_bytes(b"bounded synthetic FRD")
    lines = []
    for name, ids in (("PLATE", range(1, 17)), ("WEB", range(17, 33))):
        lines.append(f"internal energy (element, energy) for set {name} "
                     "and time 1E+00\n")
        lines += [f" {i} 1E+00\n" for i in ids]
        lines.append("\n")
    paths["solution.dat"].write_text("".join(lines))
    monkeypatch.setattr(energy, "parse_outputs",
                        lambda *args: {"action_work_j": {"plate_fy": 64.}})
    args = ["energy", "--manifest", str(paths["manifest.json"]),
            "--deck", str(paths["energy.inp"]),
            "--frd", str(paths["solution.frd"]),
            "--dat", str(paths["solution.dat"]),
            "--expected-frd-sha256",
            sha256(paths["solution.frd"].read_bytes()).hexdigest()]
    monkeypatch.setattr(sys, "argv", args)
    energy.main()
    result = json.loads(capsys.readouterr().out)
    assert result["case"] == "plate_fy"
    assert result["energy_balance_relative"] == 0.
    paths["energy.inp"].write_bytes(changed.replace("ELSET=Web", "ELSET=Plate")
                                    .encode("ascii"))
    with pytest.raises(ValueError, match="differs beyond"):
        energy.main()
