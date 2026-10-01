# B2 nodal rigid footprints — experimental static delivery

1 October 2026. Base solver commit a1f16198; unchanged package version0.4.7.
The existing public B2/Q4 panel facade now accepts explicit immutable
`B2NodalRigidFootprint` groups at physical B2 endpoint nodes. Complete selected
Q4 patches require every vertex and actual cell-edge connectivity. Shell normal
spin is intentionally locked. This is not the historical translation-only
least-squares finite-vertex point law, distributing coupling, a continuous-area
weld, finite B2, or drilling-independent physical transfer qualification.

For d=Xb-Xs, the separately identified reference-linear law is
g=(ub-us+[d]x theta_s,theta_b-theta_s). Global six-coordinate endpoint and shell
increments give the actual constraint and dual work. Physical exerted actions
are minus-transpose multiplier actions, with direct couples and compensated
lever arms about one beam origin. Requested groups alone materialize recovery.
The existing affine plan, sparse scaled KKT, factor and complete-case batch
controller are reused. No GE histories, interior beam interpolation, penalties,
new material law, factor-per-case or replacement framework is introduced.

Distinct conditional result/capability types preserve the empty-footprint
schemas. New modes/prestress requests reject explicitly; no finite/checkpoint
operation is added. Overlapping point-host/footprint incidence, unknown IDs,
incomplete/disconnected patches, collinearity and supported row dependence reject
with provenance. Area admission is not a general rank or rigidity proof.

## Installed observations

Wheel SHA256 `ee6f70a28a19a245251e452602ff68fde5a72bdcebb831c6f7dd82742caf2973`:
390 Python modules byte-match source/wheel/site; actual209 onsite imports.
Child NumPy/SciPy pools1, Numba1 and JIT disabled are explicitly verified.
All numerical jobs run serially within600s/8GiB; these are bounded development
observations, not practical-scale/platform qualification.

| Run | Actual outcome | Supervisor time / observed tree peak |
|---|---|---|
| New predicates V1 | 35 pass / 1 fixture failure | 5.2123615s / 170360832B |
| Affected predicate V2 | 1 pass, zero errors/skips | 2.0837624s / 160632832B |
| Existing B2 panel | 38 pass, zero errors/skips | 6.9781779s / 169492480B |
| Prior empty-profile oracle | Completed on wheel5d4d8602 | 2.0881305s / 151818240B |
| Current empty-profile oracle | Completed | 2.0887208s / 152535040B |
| Public headless example | Completed, one factor | 1.5709048s / 132354048B |

The original positive group B=(3,5,6) had collinear coordinates x+y=2. Product
correctly rejected it. Only the intended-success groups changed to disjoint
noncollinear A=(1,2,3)/B=(4,5,6); geometry, the diagonal-edge negative, law,
admission and tolerances stayed fixed. Original test d50f884b… and failed XML
remain; final test c22faf56… is copied under a V2 filename and only the affected
predicate reran. Reuse35 unchanged passes explicitly; no fresh all-green36 run
is claimed. Product bytes/wheel did not change.

Checks cover independently derived rigid fields/virgin derivatives, endpoint
trace and reversal, nonaxis frames, equivalent work units, eccentric transpose
work, supported affine equilibrium/prescribed work, sparse/dense agreement,
group incidence negatives, mutation isolation, selected recovery, 1/10/100 cases
with factor1, complete-case cancellation, callback close and failed-prefix status.
The artificial sub-ulp arm test reports shell moment-1Nm/beam moment0 after
highly cancelled rounded-C actions. It demonstrates compensated recovery, not
exact rigid-work balance at arbitrary extreme scales.

Old/current controls compare13 sparse/operator arrays exactly, plus byte-identical
capabilities/default result and selected10-case batch JSON (SHA256
`2e2c0796a0ceb481f4c25176812b7957ad8b94e6aa730fe81fb93c612bb219a9`).
The example uses the installed public facade, selected physical group wrenches
and factor1 with recorded209 onsite imports and effective pool settings.

Preparation failures remain visible: first build lacked cache-directory access;
`--no-cache-dir` repaired it without global configuration or source changes.
The old oracle's first fixture tree omitted an imported relative script and
failed before the oracle. V2 preserves all three dependency files unchanged;
the imported probe's main is not executed. No frozen run authority was consumed.

[Complete independent review](independent-review.md) finds no blocking issue
within this declared static scope. [Raw inventory](raw-v1.zip) preserves63 files,
including the original fixture failure, build/preparation failures, exact wheel,
source/fixture snapshots, command runners, observations and review. Every archived
file was reread against its SHA256; archive SHA256
`d4f5f53c0d6371aabb768bf0291dccb1023fdc2b6447f915ed1299c51adfb676`.
[Identity](raw-v1-identity.json) binds counts/sizes. Prior wheel5d4d8602 and its
full source remain protected in the preceding nodal-footprint delivery archive.

At this core delivery, the legacy ANYfem B2 from_definition factory could discard
new footprint fields. The subsequent [consumer delivery](../r8-anyfem-b2-nodal-footprint-20261001/results.md)
adds its rejection guard and a separate explicit schema, with new installed
evidence. This core report does not relabel its original artifact or evidence.

Full F04/F10/F11/M4, broader attachments, B2/S3/finite/spectral,
consumer persistence, external references and practical scale remain open.
No aggregate acceptance, release or measured overall speedup is claimed.
