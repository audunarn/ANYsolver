# Curved material staged dead forces — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** Explicit curved-Q4/full-pose-point models now
accept the existing immutable `StagedDeadLoadProgramme` through the public
force-control solve, with generalized native B3 material histories and optional
shell J2. Source parent `2653b6d5`; consumer parent `295f667`, delivered consumer
commit `c78b55c`. Exact product bytes are bound by the installed artifact manifest.

## Delivered slice

The existing owner already evaluated piecewise-affine nodal force vectors from
fixed accepted material predecessors. This change admits the explicit curved
material profile at solve/restore and advertises that operation. It does not
change element work, constitutive updates, equations, numerical methods,
tolerances, defaults, trial budgets, release versions or historical identities.
The older curved-elastic profile remains fixed-action only; body, pressure and
distributed wrappers remain excluded. A staged descriptor is not a displacement
control direction.

Positive programme positions advance through absolute spatial translation-force
endpoints and must include crossed integer boundaries. Compile-time vector
ownership, augmented programme/model identity, applied-force validation and
accepted/predecessor arrays use the existing staged envelope and distinct curved
material mechanical kinds. Exact restart, adaptive accepted-prefix cancellation
and chart transport reuse the persistent owner. The focused checks establish one
compilation per unchanged owner through fixed/adaptive steps and restart.

ANYfem's separate
`anyfem.experimental-ge-curved-q4-point-panel-material-staged-v1` record nests
only the existing material-v2 or native-scale-v3 input. Old staged schemas retain
their accepted child records. Standalone and native Project persistence retain
optional J2, section bytes, reference/scaling policy and owned programme identity.

## Executed evidence

- Source v1: **three passed, one fixture failure** (wrong capabilities accessor).
  Source v2 repeats only the corrected negative case, with valid-digest load and
  predecessor corruption added: **one passed**, 18.456 s / 182,444,032 sampled bytes.
- Installed initial collection: missing copied roof fixture, exit 4, no numerical
  test executed. After adding that fixture, **eight passed**, 173.715 s /
  190,640,128 sampled process-tree bytes. These cover optional J2, fixed/adaptive
  progress, first-stage exact force-control parity, changed force direction,
  unloading, checkpoint/recovery, compile reuse, cancellation, chart transport,
  wrong profiles/programmes/boundaries, valid-digest load/predecessor corruption,
  stripped wrapper rejection and affected old force/staged admission.
- Paired installed consumer: **eight passed**, 43.323 s / 202,600,448 sampled bytes.
  Includes strict new records, legacy wrapper regression, both material layouts,
  native Project save/reopen, interior-stage restoration and exact continued
  material/physical results and final checkpoint bytes.
- Additional installed signed cycle: **one passed**, 54.177 s / 176,152,576 bytes.
  Actual loads **+1000 N -> -1000 N -> +1000 N** at accepted positions
  `(0.5, 1, 2, 3)`, using existing adaptive control (four cutbacks/64 attempts).
  No zero-force accepted endpoint is requested. Fresh restoration from the
  yielded positive prefix reproduces the negative and reloaded endpoints exactly;
  final restoration reproduces material records and bytes. Final equilibrium
  ratio `9.402188736183358e-11`, scaled constraint `7.794056555028567e-18`.
  Shell alpha maximum grows from `1.2142370279167977e-6` to
  `3.260729029291896e-6`; native generalized station high/low accumulation sum
  maximum grows from `1.0435483775149288e-5` to `3.8162920852510115e-5`.
  These are different material measures, not interchangeable plastic strains.

Thus **nine distinct installed solver and eight consumer checks passed**.
All **413 solver + 98 consumer modules** match source/wheel/site. Actual imports,
one-thread numerical pools and Numba, and disabled JIT were checked. Serial jobs
stayed within 600 s / 1 GiB. Costs are verification observations, not speedup claims.

Final solver wheel SHA256:
`c795a5da5476313a58463f36e84e05aecfa4930e6d338e7597bd97a40c3bcc7d`.
Consumer wheel SHA256:
`36ba604318ddd17b0d7f2b44130472727dd8bd57b92d70242d5ef69ab6df9adc`.
The solver was rebuilt after the review's label correction, before numerical
verification; the unchanged consumer artifact was reused after identity checks.
The preliminary build received no numerical verification or acceptance claim.

## Review, failures and qualification boundary

An independent OpenAI development reviewer found one public-label error:
"nodal translations" could imply prescribed displacement; it now says "nodal
translation forces". No other concrete solver/consumer defect was found in
admission, force work maps, checkpoint identity/layout, predecessor replay,
atomic publication/restore or schema nesting. The integration owner inspected
the complete worker diff, actual checks and source/artifact correspondence.
The signed-cycle test was added, inspected and executed by the integration owner
after that review. This is not cross-family scientific acceptance.

The failed source assertion and installed collection are retained. Passed
campaigns were not repeated to repair them. Existing whole-path replay,
zero-load acceptance concerns, pressure assessment, line/footprint mechanics,
physical fibres, curved S3, full units/mesh/material/scale/external/platform and
release obligations remain open. The bounded synthetic panel is not a calibrated
engineering cyclic benchmark. Checkpoint consistency does not authenticate an
arbitrary historical path. No aggregate gate, F03 authority, external execution,
main merge, push or release is accepted by this slice.

## Evidence

[Execution and physical summary](summary-v1.json),
[fresh runners, manifests, imported sites, fixtures, source/collection failures,
signed-cycle prefix/results and review](raw-evidence-v1.zip).
Archive SHA256:
`cfd4c2f2ca9f7b16904ebf0231f41efbd791ece62b278515b356f689e2ac38d8`.
Only whitelisted execution metadata is retained; no inherited environment map
or protected historical archive was read or copied.
