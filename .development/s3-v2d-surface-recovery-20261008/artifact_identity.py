"""Compare every Python module in the candidate source, wheel, and site."""

import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile


source = Path(sys.argv[1]).resolve() / "src"
wheel = Path(sys.argv[2]).resolve()
site = Path(sys.argv[3]).resolve()
expected = {
    path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (source / "anysolver").rglob("*.py")
}
with ZipFile(wheel) as archive:
    actual_wheel = {
        name: hashlib.sha256(archive.read(name)).hexdigest()
        for name in archive.namelist()
        if name.startswith("anysolver/") and name.endswith(".py")
    }
actual_site = {
    path.relative_to(site).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (site / "anysolver").rglob("*.py")
}
result = {
    "source_python_files": len(expected),
    "wheel_python_files": len(actual_wheel),
    "site_python_files": len(actual_site),
    "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
    "source_equals_wheel": expected == actual_wheel,
    "wheel_equals_site": actual_wheel == actual_site,
    "source_wheel_mismatches": sorted(set(expected) ^ set(actual_wheel))
    + sorted(name for name in expected.keys() & actual_wheel.keys()
             if expected[name] != actual_wheel[name]),
    "wheel_site_mismatches": sorted(set(actual_wheel) ^ set(actual_site))
    + sorted(name for name in actual_wheel.keys() & actual_site.keys()
             if actual_wheel[name] != actual_site[name]),
}
print(json.dumps(result, indent=2))
assert expected and expected == actual_wheel == actual_site
