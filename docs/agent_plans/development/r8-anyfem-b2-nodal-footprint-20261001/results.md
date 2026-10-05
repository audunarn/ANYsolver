# Installed experimental B2 nodal-footprint consumer — 1 October 2026

ANYfem commit `cc9a490` adds `ExperimentalB2NodalRigidFootprintPanel`, a distinct
strict reference-linear B2 input schema and nested Project dispatch. The legacy
point factory now rejects nonempty footprint definitions instead of discarding
them. Definition-only save/reopen does not assemble a solver. Selected batches,
ordered case identities, complete-case cancellation and cleanup use the existing
public owner. Ordinary Project selectors and format remain unchanged.

Solver parent `a9277078`, wheel SHA256
`ee6f70a28a19a245251e452602ff68fde5a72bdcebb831c6f7dd82742caf2973`, is paired
with ANYfem wheel SHA256
`c07432fb50c8e7e25159cf5982490e454ffb41d10178c34324f37c3e3c12e8ec`.
All390 solver and98 consumer modules match source/wheel/installed bytes.
Python3.14.2/Windows, effective BLAS/OpenMP and Numba threads1, JIT disabled.

Installed checks:37/37 new and112/112 affected legacy checks, no failures/errors/
skips;273/277 imported modules originate in the frozen installed site. Supervised
wall times4.691s/175.198s and peak process-tree memory176832512/205996032 bytes.
The installed public example completes1/10/100 ordered cases with selected
recovery, standalone input and Project save/reopen, one factorization each.
These three serial routes share one process:2.086s/150863872 bytes,273 onsite
imports. These measurements are evidence of execution, not a speedup claim.

Previous/current legacy payload and ten-case observations are byte-identical:
payload SHA256 `99b4bf401a596d19bebfbc6d5c7f6f3debe3b2791f6972632df6d4c851727758`;
observations `406b29c9fc8f53883aa5a2d9cb2d756ac868b21913676bf24b04e853bcbc3cbe`.
The first old recorder failed by attempting to JSON-encode owned payload bytes.
Only its UTF8 output representation was repaired; the failed source/log remains.

[Independent review](independent-review.md) has no blocking scoped finding.
[Raw evidence](raw-v1.zip) contains119 files,4035970 raw bytes and an internal
per-file SHA inventory; every archived file was reread. Archive SHA256
`4c0ebc3b96b8a977d9f704fd922b598bf2547974f1ba8e283fa9049fa9f4aa93`.
[Identity](raw-v1-identity.json) binds sizes. Full original commands, sources,
fixtures, wheels, runtime/import checks, XML and failures remain available.

This is experimental reference-linear selected-node rigid coupling, normal spin
locked. No continuous-area/distributing/weld/drilling-independent physical torque,
finite/history/checkpoint, mass/prestress or modal admission follows. Unsupported
requests reject explicitly. The [solver mechanics evidence](../r8-b2-nodal-rigid-footprint-20261001/results.md)
and all F04/F10/F11/M4, complete consumer/external/scale/aggregate obligations
remain separate and open. No main merge, publication or formal F03 execution.
