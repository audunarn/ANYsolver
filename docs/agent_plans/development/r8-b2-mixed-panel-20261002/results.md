# Experimental B2 mixed Q4/S3 static panels — 2 October 2026

The public facade now admits `B2MixedPanelDefinition` with explicit native
`S3V2DPanelShell` facets alongside Q4 shells. Multiple physical B2 members and
finite-vertex points reuse the existing sparse owner, static batch, factorization,
selected recovery and closure services. The historical Q4 definition remains
on its original route. No element equation, tolerance, default or version changed.

All facets are registered before native S3 evaluation. Local shell operators
scatter 18 or 24 DOFs; point capabilities report the actual formulation and
three/four-vertex law identities. Any S3 facet explicitly excludes mass, modes
and nodal footprints. These remain mandatory future programme work.

## Verification

- Final changed source module: **28/28 passed** through
  `scripts/run_portable_ci.py --development`.
- Fresh installed wheel: **180/180 passed** across the new mixed-panel module,
  historical Q4 panel, rigid footprint, numerical resolution, private Q4/S3
  point, reference-mode and footprint-mode checks.
- Installed public examples completed for mixed and all-S3 meshes, each solving
  1/10/100 compatible cases with one eligible factorization and selected outputs.
- The historical installed B2 footprint/mode example and unchanged ANYfem
  construction → native Project save/reopen → static/modal workflow passed.
  This preserves the existing consumer; it does not add S3 consumer persistence.

The new numerical checks compare independent dense scatter/KKT solves using the
admitted native local operators: displacements, multipliers, reactions, energy,
gaps, reversed connectivity, normalized normals and nonzero prescribed motion
through a nonselector reduced basis. Ownership, mutation, cancellation prefixes,
one-factor batches, failed-backend results and unsupported requests are exercised.
They establish assembly and execution behavior, not independent physical accuracy.
Development comparisons retain their explicit `1e-8` response tolerance; they
do not discharge the programme's tighter formal parity requirement.

## Artifact and runtime identity

Solver wheel SHA256:
`fb12ac6637098f32477616a402ed3cae79ae28c49edb81ff30d35d57087d75fd`.
All **391** solver module bytes match source/wheel/site; **210** actual canonical
imports come from the isolated installed site. Unchanged consumer wheel
`11728ab84a2c2b290d37651c455d9f6b7d63110e4804cb9263686c37511fa56e`
matches all **98** consumer modules and the current consumer source.

Windows/Python 3.14; numpy 2.4.6, scipy 1.17.1, numba 0.65.1.
Effective BLAS and Numba threads: **1**, JIT disabled. Serial processes were
supervised at 180 seconds and 1 GiB. Installed checks took 18.28 seconds including
startup, sampled peak 198,369,280 bytes; both new examples took under 2 seconds.
These are execution records, not a performance comparison or speedup claim.

## Preserved failures and review

The initial source campaign retained 161 passes and 11 failures: a shared
connectivity helper incorrectly required four nodes. Its exact S3 three-node
admission was repaired without changing old Q4 admission. A subsequent run
retained 59 passes and one incorrect test expectation: native S3 normalizes
finite nonzero normals, so `(0,0,2)` is valid. The corrected test rejects zero
and verifies normalization equivalence. No numerical tolerance was relaxed.

An earlier nonexistent target failed before execution. An archive helper first
expected the solver identity schema for the separate consumer identity; the
failed helper is retained and its schema check corrected, with no numerical rerun.
Initial source stdout was tool output; its complete per-case/runtime/resource
records are preserved. Subsequent stdout logs are retained in full.

[Independent Read review](review.md) found no remaining actionable defect after
the reversed-facet and prescribed-motion coverage additions. The reviewer did
not implement or run the code. No different-model-family or formal mechanics
acceptance is claimed.

Raw wheel, frozen fixtures/runners, imports, identities, failures, inventories
and logs: [archive](raw-v1.zip), [hash inventory](raw-v1.json).
Archive SHA256: `fc930d6cfa6ef2c25db5c4c5b2dfd136fe7e7cc53777e2d26290a022dd88704e`
(62 members; 2,410,275 bytes), all reread and compared byte-for-byte.
Execution directory: `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-b2-mixed-panel-installed-v1`.

M3/F10/F11/F13 and aggregate gates remain open. The wider B2 attachment,
immutable-definition, consumer, spectral, scale and external-accuracy obligations
are not closed by this static slice. BL5 mechanics and formal F03 authority are
unchanged; nothing was merged to main or published.
