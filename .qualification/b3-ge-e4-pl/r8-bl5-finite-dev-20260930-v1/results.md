# Finite BL5 nonmatching elastic integration — development results

Classification: experimental Level-A vertical slice, not F03/G2 acceptance.
Parent source `e64db0e512297d6cc62b24d3657d335487d8f712`; final product commit
is recorded in `source.json`. No legacy default, section equation, material
tolerance, multiplier policy, package version or release decision changes.

## Decision and delivered behavior

Carry the existing BL5 physical top-surface position/director bond, with free
normal spin and native retained half-cell work, through the existing persistent
finite owner. Compile multiplier sample maps once and keep the existing sparse
scatter and atomic accepted boundary. This enables finite load/unload, physical
station-wrench recovery, rejection/cancellation, chart rebasing and restart on
small nonmatching elastic generalized-beam/shell panels.

The spatial adapter differentiates actual physical shell frames and native beam
cell rotations. It includes rotational gauge correction and the additive-shell
column map; it does not symmetrize the matrix. Reference correspondence and
quadrature remain fixed. A narrow typed BL5 chart failure can reject a candidate;
ordinary validation/programming/backend failures propagate. Generalized yielding,
shell J2 and physical fibres are explicitly outside this finite BL5 slice.

V11 and anchored V11 are separate checkpoint identities. Existing V7 and point
policies are preserved; V10 may wrap the V11 snapshot for optional adaptive
control. Recovery retains owned integer gather indices, station density, local
gap and integrated spatial port work. Raw multipliers are not display moments.

## Verification and interpretation

Source v5 passed 55/55 in 50.51 s. Earlier v1–v4 failures remain raw evidence:
collection import, test helper/method errors, a finite-difference subtraction
floor, outdated capability expectation and changed legacy error wording.
The nonzero-multiplier derivative check uses a synthetic 50000-scale virtual
multiplier to isolate curvature above cancellation from element forces, with
the same 1e-6 derivative limit. It is not an equilibrium or altered load fixture.

Preparation v1 failed on Windows default text decoding before a wheel or run
was produced; its partial files are preserved. Preparation v2 explicitly reads
UTF-8. The example output label was corrected to `tip_position_m` before the
first installed execution, and its frozen input hash updated. No runtime source
changed after the wheel was built.

The installed runner verifies all 516 copied inputs, exact source/wheel/site
module bytes, effective one-thread BLAS/Numba and disabled JIT, legacy V7 byte
identity and original unloading failure, and P0/coarse-continuous-P1 examples
through the public facade. V2 completed 140 passes and three failures in 521.08 s; its guard observed
527.810 s / 279171072 bytes. The three failures were solely changed legacy JSON
error wording, after successful solves and exact restarts. A narrow repair
restores the historical message and splits the new BL5 message. V3 rebuilds
the wheel and reruns complete affected cases and framing/BL5 checks; v2
passes remain relevant through the independently reviewed exception-only
impact record. Complete observed outcomes are recorded in
`installed-v2/execution.json`, `inventory.xml`, `identity.json`, `imports.json`,
`compatibility.json` and `examples.json`. The suite covers affected existing
point/material routes as well as new finite BL5 checks.

Initial v2 solver wheel SHA-256:
`879c3166a2d01226283c1e2f768b245453b249b3775419c49d1db5fccdb3754a`.
Unchanged consumer wheel SHA-256:
`ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.
386 solver and 97 consumer Python modules are byte-bound. Hashing/importing the
unchanged consumer is compatibility provenance, not new consumer acceptance.
The immutable installed runtime and 516-file closure are archived separately
for both v2 and v3. Their exact one-module, exception-message-only delta is
retained in `runtime-delta.json` and `runtime-v2-v3.patch`.

Corrected v3 wheel SHA-256:
`82ea8d422879559dd8482bdbb8d1c589d62fe28883e9ffdf3646573164599b39`.
V3 passed 16/16 in 37.50 s; guard 55.201 s / 235401216 bytes, 270 onsite
imports. Both public examples completed (.5,1,.75,.9), with exact restart
bytes, 12 physical station records and a 3488-byte snapshot. Final equilibrium
ratios are 2.16178e-9 / 3.55643e-9 and weak gaps 1.54386e-17 / 1.99985e-17
for P0 / coarse continuous P1. Legacy V7 retains original bytes and failure.
These are combined v2/v3 checks, not a full 143-case v3 rerun.

## Boundaries and resulting action

This slice does not select P0/P1/dual, prove mesh-uniform stability, establish
physical torque/shear agreement, admit yielded lines, or close M2/G2/F03.
The E01 normal-spin discrepancy remains distinct from BL5 free-spin semantics.
No scientific authority was consumed or renewed, and no foreign process was
interrupted. The separately owned F03 script remains untouched.

Retain the finite vertical slice if installed verification and independent
artifact review pass. The same explicit definition now runs through ANYfem save/reopen, separate
checkpoint restore and exact continuation. Continue M2 physical work and
growing-space assessment under a decision-oriented contract; do not launch an
automatic multiplier/refinement campaign from these successful software checks.

## Complete experimental consumer slice

ANYfem product7cf1fd7ecec14ab16dab3ffb26bf4182c807af0c adds a separate
ExperimentalGEBL5Panel and anyfem.experimental-ge-bl5-panel-v1 schema, preserving
historical point/J2/Q4 schemas. Native beam bytes/hashes, all public BL5 controls,
frames/arms/supports/actions roundtrip. Admission is pure-Q4 elastic shell and
generalized native sections; topology and finite mechanics remain solver-owned.
Atomic bounded input persistence remains distinct from native-project support
and solver checkpoints. No public default, version or release changes.

Installed consumer21/21 in170.75s: seven new BL5 and fourteen historical cases.
Guard175.702s /232476672bytes; four frozen inputs, 271onsite imports, actual
one-thread/JIT off. Solver82ea8d42... unchanged; consumer wheel
e3f755fe24f67b99f3e353b5f05461f607d5e9c8feb12d5fb6025689b7bfe49e.
All386solver/97consumer modules match source/wheel/site. Independent source
and artifact reviews have no consequential finding. Consumer runtime source,
full test, docs, manifest and execution are preserved.

Decision: retain this complete experimental finite/consumer vertical slice.
Physical line transfer, growing-space policy/stability, material extensions and
full M2 acceptance remain open. No performance improvement is claimed from
these functional test durations.
