# Installed curved-reference ANYfem workflow

2 October 2026. ANYfem local commit 8a6e677 on
codex/experimental-ge-panel-consumer; solver current 2b5afc1a, product unchanged.
IMPLEMENTED_NOT_QUALIFIED. No aggregate gate closes.

The existing ExperimentalGEPointPanel now carries an explicit keyword-only
shell_reference_policy. The new anyfem.experimental-ge-curved-q4-point-panel-v1
schema preserves CURVED_Q4_POINT_REFERENCE_V1 through standalone input files,
ordinary native Project persistence and fresh solver creation. Unused options
preserve old flat schemas. Unknown/missing installed policy, S3/J2, staged or
external load wrappers, moment actions and modal/footprint conversions fail
explicitly. Solver-owned beam/geometry/state admission remains authoritative.
No beam equations, default selector, physical tolerance or release version changes.

Installed ANYfem wheel SHA256:
e1bd72d76d6c13873b47194ecabe0210bef3f2d252abac3644898e9455c9ef94.
All 98 product modules matched wheel and installed site. Unchanged installed
ANYsolver wheel SHA256:
6086fd4edb4246ab77a2c67fb898965e4e71d8020d4c0494b59bbbcb5dbe70b0.
All 412 solver product modules matched. Actual import locations, one numerical
thread and disabled JIT are checked and retained in runtime.json.

Ten focused installed tests pass, including curved native roundtrip/restart,
strict policy/format rejection, unsupported combinations and old flat/v3 controls.
The installed actual E04 4x4 roof then completes standalone save/reopen, native
Project save/reopen, 10N finite seed, one arc step, fresh checkpoint restore and
one exactly reproduced continuation step. Final 12.156395 N / 0.027135246 mm
central downward motion matches the earlier 4x4 direct-solver screen exactly.
Final equilibrium 3.9510e-12 and compatibility 7.0666e-18 meet unchanged criteria.
Full run: 20.41s / 218492928 bytes
sampled tree peak, inside 600s/1GiB. No timing improvement is claimed.

Initial source failures were fixture mistakes (NumPy primitives in strict JSON
framing, an invalid historical-policy test string, and using a capability key
in preflight). The source runner also had one pre-launch syntax error. All are
preserved; they are not physical solver failures. Corrected affected source check
passes. Independent source review found no implementation blocker and identified
missing exclusion checks; these were added before installed execution.

runs-v1.zip preserves input/project/checkpoint files, original commands, successful
and failed logs, installed wheel, identities, captured fixtures and whitelisted
execution metadata. SHA256: 3d0d85436cfaa908b94ec07e226002b1dc30ea9d59e4fe9d74a7fbcae72d45fe. Full environment maps and installed-site
caches are excluded. This is one usable consumer slice, not curved capacity,
external-reference, spectral, scale or production acceptance. Full G0–G6 and
milestone obligations remain open; no push, main merge or publication occurred.
