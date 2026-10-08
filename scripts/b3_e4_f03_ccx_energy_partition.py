"""Read bounded CalculiX plate/web elastic energies for reference design.

The element-energy split is a strain-energy partition, not a sided interface
traction or a same-law F03 comparison.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

from scripts.b3_e4_f03_ccx_matched_t_reference import build_bundle, parse_outputs


_HEADER = re.compile(
    r"^\s*internal energy \(element, energy\) for set (PLATE|WEB) "
    r"and time\s+([0-9.E+-]+)\s*$", re.I)


def parse_partition(dat: str, plate_count: int, web_count: int,
                    applied_work_j: float) -> dict:
    if (type(dat) is not str or len(dat) > 8*1024*1024 or
            type(plate_count) is not int or plate_count < 1 or
            type(web_count) is not int or web_count < 1 or
            not isfinite(applied_work_j) or applied_work_j <= 0.):
        raise ValueError("bounded positive elastic-energy case required")
    lines = dat.splitlines()
    blocks = {}
    times = {}
    for index, line in enumerate(lines):
        match = _HEADER.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in blocks:
            raise ValueError("repeated element-energy block")
        time = float(match.group(2))
        if not isfinite(time):
            raise ValueError("nonfinite output time")
        rows = {}
        for row in lines[index+1:]:
            parts = row.split()
            if len(parts) == 2 and parts[0].isdigit():
                element = int(parts[0])
                value = float(parts[1].replace("D", "E"))
                if element in rows or not isfinite(value) or value < 0.:
                    raise ValueError("invalid element energy")
                rows[element] = value
            elif rows:
                break
        blocks[name] = rows
        times[name] = time
    expected = {"plate": set(range(1, plate_count+1)),
                "web": set(range(plate_count+1,
                                 plate_count+web_count+1))}
    if (set(blocks) != set(expected) or
            any(set(blocks[name]) != ids for name, ids in expected.items()) or
            times["plate"] != times["web"]):
        raise ValueError("incomplete or mismatched plate/web energy inventory")
    energies = {name: sum(blocks[name].values()) for name in expected}
    total = energies["plate"]+energies["web"]
    if not isfinite(total) or total <= 0.:
        raise ValueError("invalid total element energy")
    half_work = applied_work_j/2
    return {
        "classification": "external_elastic_energy_partition_not_sided_work",
        "plate_energy_j": energies["plate"],
        "web_energy_j": energies["web"],
        "total_energy_j": total,
        "applied_half_work_j": half_work,
        "energy_balance_relative": abs(total-half_work)/half_work,
        "plate_fraction": energies["plate"]/total,
        "web_fraction": energies["web"]/total,
        "element_counts": {"plate": plate_count, "web": web_count},
        "output_time": times["plate"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--frd", type=Path, required=True)
    parser.add_argument("--dat", type=Path, required=True)
    parser.add_argument("--expected-frd-sha256", required=True)
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    original_deck, expected = build_bundle(
        manifest["variant"], manifest["case"], manifest["nx"],
        manifest["root"], manifest["profile"],
        manifest.get("domain", "coupled"))
    if manifest != expected or manifest.get("domain", "coupled") != "coupled":
        raise ValueError("coupled reference manifest identity changed")
    if original_deck.count("*END STEP\n") != 1:
        raise ValueError("one original deck terminator required")
    energy_deck = original_deck.replace(
        "*END STEP\n", "*EL PRINT,ELSET=Plate\nELSE\n"
        "*EL PRINT,ELSET=Web\nELSE\n*END STEP\n")
    deck_bytes = args.deck.read_bytes()
    if deck_bytes != energy_deck.encode("ascii"):
        raise ValueError("energy deck differs beyond the two output requests")
    frd_bytes = args.frd.read_bytes()
    frd_hash = sha256(frd_bytes).hexdigest()
    if frd_hash != args.expected_frd_sha256.lower():
        raise ValueError("FRD identity does not match the expected case output")
    dat_bytes = args.dat.read_bytes()
    parsed = parse_outputs(manifest, frd_bytes.decode("ascii"),
                           dat_bytes.decode("ascii"))
    result = parse_partition(
        dat_bytes.decode("ascii"), manifest["shell_elements"]["plate"],
        manifest["shell_elements"]["web"],
        parsed["action_work_j"][manifest["case"]])
    result.update({
        "case": manifest["case"],
        "original_deck_sha256": manifest["deck_sha256"],
        "energy_deck_sha256": sha256(deck_bytes).hexdigest(),
        "manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "frd_sha256": frd_hash,
        "dat_sha256": sha256(dat_bytes).hexdigest(),
    })
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
