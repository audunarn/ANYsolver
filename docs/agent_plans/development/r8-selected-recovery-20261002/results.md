# Selected finite recovery — development evidence, 2 October 2026

Added explicit ordered node/material selection to the existing recover facade.
The owner reads cached accepted results, returns detached selected arrays, and
performs no element/constitutive evaluation or history replay. Reaction rows are
coordinate covectors, not spatial-wrench claims. Full accepted storage is retained;
no performance saving is claimed. Legacy footprint selector remains unchanged.

Source v1 failed (1failed/4passed): unrebased force results have no cached shell
frames. Corrected by reconstructing only requested physical frames from cached
rotation coordinates, with no mechanics. Independent review also corrected the
test's guard from nonexistent _evaluate to actual _assemble. Source v2:5passed
27.64s; subsequent reaction assertions are covered by the installed run below.
Independent reviewer /root/bl5_shell_contract inspected both fixes and ordered
reaction/load-position semantics; no remaining defect. Reviewer did not run tests.

Installed solver:8passed27.08s, supervised29.00s, peak181358592bytes.
Wheel4143309f3a9c3f7cb3e142b030e20be3195d23caf62a8be4374b0dd8f002b01e,
404Python modules match source/wheel/site. Covers force and displacement state,
restart, no assembly, ownership even after caller reenables writes, ordered IDs,
material output, unavailable IDs and legacy footprint selections.

Installed ANYfem consumer:1complete workflow passed40.86s, supervised43.01s,
peak187314176bytes. Wheel60da1b9d92e7a4f6770353f915ec91b71b60d2284e01db6ab7545d731d70c030,
98modules match. Includes project reopen, yielded seed/rebase/restart, adaptive
displacement cancellation/restart and selected cached recovery. Both runners verify
onsite imports, one-thread numerical pools and JIT disabled. No scientific gate,
full material envelope, storage/scale, capacity or release acceptance follows.

Archive:installed-and-source-v1.zip; SHA256 2fa72e4a2b23e0ece9b7f9a7c97876752419cf781ee5b2be37e273a8211de903.
Includes failure logs, runners, fixtures, artifact hashes, safe execution metadata
and prior active note. Full environment maps deliberately omitted. Prior branch
failure/F03/pressure boundaries are unchanged; no failed branch rerun occurred.
