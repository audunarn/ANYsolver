# Actual E04 material roof and native consumer — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** The installed 4×4 material roof carries active
shell and generalized-beam histories through a sampled turning point and
descending branch. Exact continued restart and native ANYfem persistence pass.
This is synthetic development evidence, not a calibrated or converged capacity
prediction. No aggregate gate or release obligation closes.

## Definition and implementation

Source parent: solver `4f9abaa9`, consumer `295f667`. Only the solver reference
fixture, runnable scripts, focused tests and development records change. Product
modules, constitutive integration, tolerances, defaults and versions are unchanged.
Exact executed fixture bytes and installed-module identities are in
[manifest](manifest.json) and [raw evidence](raw-runs-v1.zip).

The existing roof has 16 Q4 facets, four native B3 cells and ten full-pose nodal
point bonds. Geometry, support translations, centroidal rectangular section,
material frames, eccentric offsets and central downward dead force are preserved.
These points are not a qualified bonded line. Young's modulus is 3.10275 GPa;
density 1 kg/m³ is explicit static bookkeeping, with spectra excluded.

The new `material_definition` requires declared strengths: shell proportional
stress 3.10275 MPa, existing DNV development curve shape, generalized beam
resultant limits `(500, 300, 300, 1, 2, 0.5)` in `(N,N,N,Nm,Nm,Nm)` and hardening
25,000 N. The associated ellipsoid is not physical fibre plasticity or inferred
rectangle strength. Explicit native force/moment scaling is preserved.

`r8_e04_native_roof.py` now accepts these optional material arguments while
keeping its elastic route. It checks actual layer/station material recovery at
restart. The new `r8_e04_material_consumer.py` saves/reopens the same definition,
restores a supplied accepted checkpoint and compares additional continued steps
against a fresh public owner. It uses existing public factories and schemas.

## Observed route

The seed is 100 N. Twenty requested arc increments use the existing frozen
area/length metric, radius 0.003 and downward orientation. All twenty accepted
the requested radius. Arc work: 115 evaluations, 95 linear solves, zero rejected
trials and 300 event-cell evaluations. Seed work is not included in those counts.

First sampled nonzero shell history: 918.919 N; first sampled nonzero beam
history: 1194.760 N. These are sampled history observations, not exact yield loads.
The largest sampled force is **1348.518 N at 5.949 mm downward displacement**,
followed by twelve descending samples. Final force/displacement: 739.599 N /
13.627 mm. Final shell alpha maximum is 0.00631358; beam accumulation maximum is
0.001096505. Maximum accepted equilibrium ratio is 4.097e-9; maximum scaled
constraint is 2.537e-15. Full samples and work are retained in
[observations](observations.json).

Fresh restoration after arc prefix five reproduces all fifteen remaining
checkpoints exactly. Final bytes, accepted history, displacement/resultants and
detailed shell/beam material records match. Final fresh restoration also matches.
Supervised installed route: **260.260 s / 167,358,464 sampled process-tree bytes**.

Native ANYfem save/reopen preserves the explicit native-scale-v3 schema and
compiled identity. Its final-checkpoint restore and two additional descending
increments match a fresh solver owner exactly, including all checkpoint bytes,
history and detailed material recovery. Final force/displacement: 603.248 N /
14.704 mm. The continued shell history is active; beam accumulated history is
preserved. Consumer route: **28.502 s / 176,828,416 bytes**.

## Verification and retained failures

- Source input checks: ten passes and a failed mixed-boolean input guard. Repair
  validates the object-typed input before numeric coercion; only that check was
  rerun, and passed. The original failure remains retained.
- Installed input suite: eleven passes, including the old elastic geometry/
  centroidal-section control and both optional-shell branches.
- First consumer attempt failed before numerical continuation: the fixture
  emitted NumPy scalar coordinates, rejected by the strict consumer record.
  The fixture now emits builtin floats with identical values. No parser guard
  was disabled and the failed attempt remains retained.
- Final installed input repeat: three affected checks passed, covering both
  material branches and the unchanged elastic geometry with canonical numerics.
  Its supervisor observed 3.628 s / 177,156,096 bytes.

All **413 solver and 98 consumer** source/wheel/site modules match. Actual imports
are exclusively from the respective installed sites. Effective numerical pools
and Numba use one thread; JIT is disabled. Each run stayed within 600 s / 1 GiB.
Solver wheel SHA256:
`780e77539f6c511026ff626485af7d583cc5562f7f4c7452e0fbc45222489e34`.
Consumer wheel SHA256:
`937eb59f99fc72463af3daad8c7363755fb957648f81d7647591305af61d3374`.
Whitelisted execution metadata, post-run dependencies, commands, fixture hashes,
logs, results, snapshots and native project are retained. Full environment maps
and unrelated historical archives are excluded.

Timings are verification costs, not optimization claims. Independent scientific
review, calibrated strengths, mesh convergence, physically matched external
capacity, full attachment qualification, scale/platform and release remain open.
There was no new external solve, formal F03 execution or scientific amendment.
