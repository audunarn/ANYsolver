# Four-macro uniform arch refinement closeout

Implementation: `8b8edf5d5549723c4aeb95b5ea5808dd6fbf6d6f`.
Tree: `9fb95090099cd34ceb8d4109468983facbc56e92`.
Base: `43d2dd9369eb73422c4daa783edb43548d351f91`.

Outcome: `DEVELOPMENT_REFINEMENT_IMPROVES_BUT_ENGINEERING_ACCURACY_OPEN`.

The four-element native model completed the same three prescribed crown drops
as the accepted prefix of the failed two-element arc smoke. This was a distinct
displacement-controlled programme, not a restart or retry of that failed run.
Geometry, section, load, quadrature and native mechanics remained fixed.
The result demonstrates a refinement trend but does not qualify the beam.

## Separate inventories

| Inventory | Passed tests | Scientific JSON files | Supervisor seconds |
| --- | ---: | ---: | ---: |
| Sampling/field-map rehearsal | 11 | 0 | 1.811 |
| Four-macro native rehearsal | 1 | 6 | 75.586 |
| Cycle A sampling/field maps | 11 | 0 | 1.811 |
| Cycle A native | 1 | 6 | 76.984 |
| Cycle B sampling/field maps | 11 | 0 | 1.812 |
| Cycle B native | 1 | 6 | 76.583 |

All three native scientific file sets are byte-identical. Each native test
includes all three accepted targets, strict full-checkpoint decode/re-encode,
elastic-history checks, native recovery, and direct continuum evaluation at
32 stations per target. Unit inventories cover strict sample admission,
default-site identity, owned samples, reflection, proper frames and work maps.
No failed inventory or post-rehearsal correction occurred in this gate.

## Accuracy evidence

| Crown drop | Two-macro load error | Four-macro load error | Four-macro resultant-compliance norm error |
| --- | ---: | ---: | ---: |
| .0009924835187201996 | .00960674226119762 | .0029447622797034168 | .010181307217611436 |
| .002196594350540417 | .055571954902937426 | .02307843104662788 | .026300379160405955 |
| .004368321784681136 | .16235703661970802 | .08744905893537802 | .09180322379036505 |

The four-macro load densities are .019860142066031823, .03875171857243657 and
.056097340966693346. The corresponding continuum densities are
.019801830382851316, .03787756382743095 and .05158617822669609.
The later two load errors still exceed 2%. No threshold has been relaxed.

Maximum station position errors are 3.374146364483119e-05,
8.368274099558592e-05 and .0003878767802736882. Maximum material-frame
component errors are .0005325373649202048, .0013080336019738773 and
.0039766867965997515. Linear constitutive consistency errors are at most
5.551115123125783e-17 against the unchanged 1e-11 limit.
The reported resultant-compliance norm is not a claim of a complete
displacement energy-norm qualification or a converged rate from two meshes.

The BVP solver change adds requested evaluation sites only. Its equations
and analytic derivative ASTs are exactly unchanged. Default sampling remains
129 sites. Collocation equations, tolerances, profiles, load measure and
residual checks are not changed. New results evaluate the resolved BVP
polynomial at the native stations; no saved-field interpolation is used.
The requested union retains all original sites for subsequent reference seeds.

The separate field map reconstructs reflected position/rotation, physical
axis-2/global-z frames, section forces [N,0,-V,0,M,0], strains and global
resultants without importing producer mechanics. This remains a same-author
continuum reconstruction, not independent review. Full spatial branch
uniqueness and stability are not established by these comparisons.

## Audit and preservation

The read-only audit checks separate XML inventories, strict JSON, process
bounds, native A/B/rehearsal identity, checkpoint hash, the preserved coarse
input hash and exact five-path Git extent. It recomputes expected fields,
constitutive checks, load errors, compliance-norm errors and frame/position
differences from the raw saved station arrays. No solve is launched by the audit.

Every child used one numerical thread, a 24-GiB process-tree limit,
600-second wall bound and 120-second CPU-inactivity cutoff. At most three
children ran concurrently. Longest child: 76.9835305000015 seconds.
Maximum recorded tree memory: 319164416 bytes. Observed frozen-wave span:
76.983531 seconds. All child descendants reached terminal state; no retries.

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-uniform-arch-refinement-8b8edf5-20260908`.

54 data files (2526275 bytes) plus the manifest preserve six commands,
all raw test outputs, scientific records, supervisor observations, source
snapshots, the coarse input, and the audit. Byte counts and SHA-256 were
verified for every copied file. Original runs and historical archives remain.

Manifest: 7842 bytes, SHA-256
`12289DAF9F2AF68432AB2D6257DEC343B53B32AACBE3195C8A7857B4A2FB5262`.
Audit SHA-256:
`073C961D3B45F0F3DA3F5A2D768E0026CEC1B5212AB291440D369D8F70CE5FC2`.

The freeze changes five research/test/documentation paths: one sampling-only
reference modification and four added paths. No src/ path, shared solver,
B2/B3/Q4/S3 mechanics, public route, package metadata, default or historical
evidence changed. No push, merge or release is authorized by this result.
Independent review is PENDING; the full goal remains active.

## Next gate

Run an eight-macro diagnostic at the same three drops, with identical mechanics
and tolerances, before selecting an adequately resolved arch mesh. Keep actual
raw field comparisons, not only a favourable summary load. Respect the current
checkpoint and replay bounds; do not launch an oversized campaign speculatively.

Then develop bounded objective arc cutback/step selection with accepted-prefix
rollback and authenticated predictor orientation, and demonstrate a resolved
native limit point/postbuckling branch against independent engineering evidence.
Do not replace the failed two-macro smoke or tune beam coefficients.

Practical-scale performance, broader loading/support/material/state parity,
physical mass/modal/prestress/buckling, slenderness, independent review,
installed-package/public integration and objective beam-shell connections
remain required. This diagnostic does not narrow the full objective.
