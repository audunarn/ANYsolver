# Combined virgin imperfection/material application — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** A new stress-free +0.1 mm crown reference of the
actual E04 roof completes active shell/generalized-beam plastic continuation,
exact restart and native ANYfem save/reopen/continued history. This provides the
combined application behavior for the third demonstrator at development level;
it does not qualify physical capacity or close aggregate G3/G4C/G4D.

Solver source parent `243c5a62`; unchanged consumer `295f667`. The only runnable
code change adds explicit imperfection reconstruction/provenance to the existing
consumer script. No product operator, constitutive law, tolerance, controller,
default, checkpoint schema or version changes. Exact executed scripts, artifacts,
commands, samples, checkpoints and native Project are retained in
[raw evidence](raw-runs-v1.zip), with [hash manifest](manifest.json).

## Definition and decision

Use the already tested virgin-reference operation, not a loaded-state transport.
The declared smooth downward crown change preserves axial-extruded planar Q4
facets and straight bar reference axes. Physical point offsets/frames are
transported once before compilation. Material strengths, section, supports,
100 N direction, physical metric and all run budgets match the
[nominal material application](../r8-e04-material-roof-20261003/results.md).
No sign/mesh sweep or new external reference was launched.

The operation reports zero scaled initial reference residual and changes identity
from `630de1d2b4e629d8fdcc22bb7fd1d15581a2b783fa19419ab4f48aff08a42c5f`
to `703ae42270233e174fe78b0bba76227af7d9f7201310ce462591a9aead9e424d`.
Its operation policy is `GE_STRESS_FREE_POINT_MATERIAL_REFERENCE_TRANSPORT_V1_DEV`.
Existing actual-assembly virgin material/ownership checks remain applicable to
the unchanged operation; see the
[separate reference foundation slice](../r8-material-reference-20261003/results.md).

The discriminator was coherent changed-reference/history continuation versus
a reference or ownership inconsistency. The completed route supports the former
on this one definition. It does not establish general imperfection admissibility.

## Executed behavior

Installed roof route: 100 N seed and twenty requested radius-0.003 increments,
all accepting that radius. Both material histories become active. Sample maximum
**1338.192 N at 5.953 mm downward displacement**, then twelve descending samples.
Final force/displacement: 723.518 N / 13.588 mm. Final shell alpha maximum:
0.006233026; beam accumulation maximum: 0.001029923.

Maximum accepted equilibrium ratio: 3.612e-9; scaled constraint: 2.466e-15.
Arc work: 111 evaluations, 91 linear solves, zero rejected trials and 284
event-cell evaluations, excluding seed work. Restore from prefix five reproduces
all fifteen remaining checkpoints exactly, including final bytes, history,
displacements/resultants and detailed layer/station material recovery. A fresh
final restoration also matches. Supervised cost: **247.860 s / 170,029,056 sampled
process-tree bytes**.

Installed ANYfem route: reconstruct the same virgin definition; standalone and
native Project save/reopen preserve its exact record and compiled identity.
Restore the yielded final checkpoint; two more descending increments match a
fresh public owner exactly, including every checkpoint, final history and detailed
material recovery. Final force/displacement: 588.205 N / 14.666 mm. Supervised
cost: **28.286 s / 177,418,240 bytes**. The Project stores the changed physical
definition; the separate run record preserves construction amplitude, operation
policy and source/target identities. Construction from a loaded checkpoint is
neither performed nor admitted.

## Identity and remaining boundary

All **413 solver and 98 consumer** source/wheel/site product modules match.
Consumer runtime verifies all 296 imported product modules come from the actual
paired installed sites. Effective pools/Numba use one thread, JIT disabled; both
jobs remain inside 600 s / 1 GiB. Unchanged solver wheel SHA256:
`780e77539f6c511026ff626485af7d583cc5562f7f4c7452e0fbc45222489e34`;
consumer wheel:
`937eb59f99fc72463af3daad8c7363755fb957648f81d7647591305af61d3374`.
Metadata is explicitly whitelisted; full environment maps are excluded.

No failed campaign was replaced or repeated. Nominal-case boolean/strict-record
failures and historical science retain their prior dispositions. Timings are
verification costs, not evidence of speed improvement. This new reference and
its synthetic strengths are not a mesh-converged or independent limit-load model.
Connection/drilling/shear, external capacity, complete materials/attachments,
scale/platform and independent acceptance/release remain open. F03 was not run.

Next implementation target: curved material displacement control with explicit
compatibility and fixed-predecessor recovery, rather than further roof refinement.
