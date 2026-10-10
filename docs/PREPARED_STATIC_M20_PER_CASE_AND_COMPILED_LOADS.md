# M20 — per-case fixes, compiled pressure loads, preparation investigation

2026-10-09. Owner: Claude (Anthropic). User: "Implement items 1, 3, 4 and
Option 1. Investigate if there are defensible possibilities in Preparation."
Contract and frozen criteria (C7, C4') are recorded in the living note before
any M20 measurement. Not merged, committed or published.

## Implementation

- **Item 1, reactions (vectorized route).** `constraint_force_maps` computes the
  three force maps with the same residual and accumulation as
  `constraint_force_diagnostics`; the envelope uses it when selected reactions
  are not requested. Selected reactions keep full diagnostics; their per-case
  metadata copies come from a pickle of the plain snapshot metadata made once
  (`make_metadata_copier`), checked at preparation to be structurally identical
  to `deepcopy` output, else `deepcopy` is kept.
- **Item 3, ANYfem.** `_PreparedLoadContext.capture_geometry_normals` stores the
  centroid and normal of every owned shell element once (read-only arrays,
  copies handed out); per-case cache clearing no longer discards them. Included
  in the application storage accounting.
- **Item 4, response load path.** The per-case native authority check is skipped
  only inside a live owned scope, whose entry and exit perform it for the block;
  outside a scope it still runs.
- **Option 1, compiled pressure loads.** `CompiledPressure` scatters
  activity-scaled verified pressure bases into one sparse operator. It is used
  only for PatternCase samples with an original-time packet, dead pressure, and
  pressure kinds that the preparation check exercised; everything else uses the
  native kernel. At preparation every pressure pattern column is recomputed
  through it and must meet C7, else compiled loads stay disabled. The per-case
  1e-12 source agreement check against the natively assembled pattern columns is
  unchanged, so a wrong basis or phase still falls back.

## Verification

Formal assessment, final source (`m20-claude-08-final`,
`.prepared-static-evidence/m20-assessment-02.json`): **GO**.

| Holdout | Cases | Compiled-load cases | Worst C7 | Worst C4' | Other criteria |
|---|---:|---:|---:|---:|---|
| A1-L supported S3 | 12 | 11 (the empty case has no pressure) | 0.00029 | 0.000064 | pass |
| A2-L rotated S3 | 6 | 6 | 0.00048 | 0.000001 | pass |
| A3-L free-free Q4/beam | 8 | 8 | 0.00043 | 0 | pass |
| A1-A4 vectorized | 30 | none (no packets) | | | pass, C4 bitwise |

The first assessment run (`m20-claude-07-assessment`, preserved with
`m20-assessment-01.json`) passed every frozen criterion but was marked failed by
an extra test condition requiring every A-L case to compile; A1's empty case has
no pressure and is native by design. The condition was corrected.
No holdout has multipoint constraints, so the master-equivalent part of C4' is
covered only by the bitwise force-map equality test.

Other checks: 6 M20 solver tests (force maps bitwise equal to full diagnostics
on a weighted-MPC model, metadata copies identical and independent, authority
check skipped only inside block scopes, compiled loads, follower stays native,
failed C7 disables compiled loads); ANYfem test (centroid table equal to the
builder, zero per-case recomputation, periodic samples compile and reconstruct).
Defects found and fixed during M20: harness local name shadowing its own
`tolerance` function; an impossible tuple-pressure fixture on the qualified S3
(the native kernel correctly refuses it), after which compiled loads were
restricted to preparation-verified pressure kinds; a failed preparation check
not clearing a previously enabled operator; a misleading "enabled" label with
zero verified columns.

Regression: 84 of 87 base solver tests pass and 73 of 75 ANYfem tests pass (the
new ANYfem M20 test first failed on a wrong expectation, a sample outside the
wet-pressure window, and passed after correction). The remaining failures are
pre-existing authority-test failures that reproduce on pre-M17 source: three
solver tests recorded in M16, and two ANYfem tests that patch the solver's
`_release_owned_resources` (`m20-claude-05-baseline-fem`).

## Barge result (300 cases, primary set, matched runs on M20 source)

| Measure | Vectorized | Canonical | M18 vectorized |
|---|---:|---:|---:|
| Built model to consumed output | 185.1 s | 580.5 s | 281.8 s |
| Preparation | 113.5 s | 95.1 s | 111.4 s |
| Case evaluation | 67.9 s | 481.7 s | 166.5 s |
| Load evaluation phase | 25.4 s | 82.1 s | 87.1 s |
| Recovery phase | 31.8 s | 386.0 s | 57.2 s |
| Peak RSS | 1,192 MB | 1,184 MB | 1,192 MB |

**Complete-workload ratio 3.14x** (M18: 2.21x). 299 of 300 samples used compiled
loads (one has no wet pressure); all 60 pressure phase columns met C7 at
preparation (worst 0.0027); no source-agreement fallback (worst 5.1e-15).
Output differences against the canonical route are the same as in M18
(displacement 6.0e-13, selected stresses 1.5e-11, envelope values including
reaction envelopes 7.3e-10 of entity maximum); all 43,518 governing-identity
differences are same-phase exact ties. The selected reactions at the three
chosen nodes are zero in both routes, so that comparison is uninformative;
reaction envelopes carry the reaction check. Evidence: evidence/m20-analysis.json,
m20-primary-identity.json; runs m20-primary-vectorized (187.846 s) and
m20-primary-canonical (583.272 s); epoch m20 771.12/1,200 s. No holdout pair was
run in M20; the M18 holdout remains the holdout evidence.

Remaining recurring cost per vectorized case is about 0.23 s: load evaluation
0.085 s (native non-pressure parts, compiled product, agreement check;
not profiled), selected-reaction full diagnostics about 0.1 s (per-MPC records
for 1,248 couplings plus metadata copies), application setup 0.02 s.

## Preparation investigation (no changes made)

Vectorized barge preparation is about 111 s. Defensible options, ranked:

1. **Redundant native stress warm-up for staged Q4 elements (about 13-16 s).**
   `_capture_owned_local_recovery` calls the native `compute_stresses` at zero
   displacement to warm caches, then `compile_q4_stages` calls it again for the
   constant metadata (6,400 calls for 3,185 Q4 elements). Attempting the stage
   compile first and warming only when it declines removes one call per staged
   element with identical numerics; a snapshot-digest equality test would
   confirm it. Affects every prepared route using envelopes.
2. **Batched unit probes for the vectorized affine maps (about 8-10 s).** The
   24 unit probes per Q4 element go through the per-vector staged kernel. A
   matrix-input evaluation of the same stages gives H in one call; H rounding
   changes slightly and the two canonical verification probes per element stay.
3. **Acceleration mass capture when the source has no acceleration (about 7 s).**
   Already avoidable through the existing `load_families` argument (for the
   barge: nodal, element, pressure). Making it the default for declared sources
   would narrow capability and needs an owner decision.
4. **Snapshot digest (about 4 s).** Per-value hashing of 1.8 million values;
   hashing array bytes changes the provenance digest format. Low value.

Not recommended: dropping pressure recipes for beams and couplings (they back
the native load fallback and existing capability); lazy capture (would need the
live model after preparation, which the contract forbids); weakening the
canonical full-load oracle verification (now more important because compiled
loads rely on the bases); the qualified stiffness assembly and its guards
(pinned code). Items 1-3 together could take preparation to roughly 80-85 s.

## M21 — preparation items 1 and 2 implemented (2026-10-09)

1. Recipe capture compiles Q4 stages first and runs the native zero-displacement
   warm-up only when no staged kernel results. Cross-version probe on three
   fixtures (mixed Q4/beam, supported S3, beam): snapshot content digests,
   snapshot bytes, per-recipe retained bytes, staged flags and owned recovery
   outputs are byte-identical to the pre-M21 source
   (`../evidence/m21-digest-baseline.json` vs `m21-digest-new.json`).
2. The vectorized build probes staged Q4 recipes with one column-batched pass
   of the same stage operations (`recover_q4_stage_columns`); other recipes keep
   per-vector probes; the two canonical verification probes per element remain.
   Batched maps match per-vector unit probes to 1e-13 of the largest entry.

Verification: M21 formal assessment GO (`m21-assessment-01.json`; worst ratios
unchanged from M20); M21, M20, M17 and base suites pass except the known
pre-existing envelope authority test. One defect found and fixed: the batched
path touched a recipe before checking for a staged kernel. Checks 59.97/120 s.

Barge (epoch m21, 259.07/500 s):

| Preparation | M20 | M21 |
|---|---:|---:|
| Vectorized, total | 113.5 s | 89.3 s |
| Envelope recipe capture | 42.3 s | 28.6 s |
| Pattern library and probe build | 29.3 s | 20.0 s |
| Canonical route, total | 95.0 s | 79.9 s |
| Probe recoveries (vectorized) | 101,895 | 28,640 |

300-case vectorized workload 162.3 s (M20 185.1 s). Against M20 vectorized
outputs: displacements identical, selected stresses within 2.2e-14 of element
maximum, envelope values within 5.3e-16; 18 governing identities changed, all
same-phase near ties (gap at most 2.9e-16 of entity maximum). Against the
canonical route the differences are unchanged. Composed (not matched) complete
workload ratio with M21 canonical preparation plus the M20 canonical history:
about 3.5x. The snapshot digest is not logged by the barge harness, so the
byte-identity evidence for item 1 is the small-fixture probe.
