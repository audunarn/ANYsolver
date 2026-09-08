# Native continuum-frequency gate: failed comparison preserved

Freeze 7a5c50489482399fe1f2ebde5ffc4ca89df6cb8d, tree
5481a6d827e52a107fd5fdca33d8359d0e9ebe37, base
3645e86bf66d249907497eb8649e4a10f92eb3c5. Three research-only additions;
no production source, mechanics, inertia, public route or default changed.

Outcome: NO_GO_GE_BEAM3_MODAL_OR_BUCKLING for this frozen development gate.
This is not a conclusion that the element's physical bending operator is
defective, nor permission to reinterpret the failed test as a pass.
Independent review remains PENDING; full qualification remains incomplete.

## Separate rehearsal inventories

| Inventory | Tests | Scientific files | Result | Elapsed |
|---|---:|---:|---|---:|
| Local reference | 12 | 4 | Passed | 3.48 s |
| Straight diagonal | 1 | 7 | Failed MAC gate | 12.91 s |
| Straight coupled | 1 | 8 | Passed rehearsal | 12.51 s |
| Curved coupled | 1 | 8 | Passed rehearsal | 12.50 s |

No repeats were launched. All process trees terminated cleanly and stayed
within 600 seconds/24 GiB, with at most three workers. The three-case wave
completed in seconds; there was no stall or resource failure.

The separately coded strong ODE and weak Ritz references passed their frozen
agreement checks in all three cases. Finest first-six maximum frequency
errors were approximately 0.8929%, 0.8913%, and 0.9333%, respectively.
The coupled cases' finest minimum MAC values were 0.9862556491697817 and
0.9902266503157073. These are rehearsal observations, not a passed full gate.

The straight-diagonal minimum MAC was 1.4224499317899844e-27 and therefore
failed the preregistered .95 requirement. No assessment file was fabricated
for that case; its seven partial scientific records are preserved.

## Cutoff diagnosis, with explicit limits

Read-only saved-field classification shows the native sixth mode is
torsional, while the continuum sixth is in-plane bending. Their squared
frequencies are 63.90741471713134 and 62.781244924568014. The analytic second
torsional squared frequency is 63.44745686414588, between those values.
This supports a near-cutoff ordering hypothesis. It does not establish the
missing seventh native mode or permit relabeling the six-mode gate.

A separately bounded saved-matrix diagnostic attempted eight eigenpairs
without any mechanical reassembly. It stopped at a first-six eigenvalue
reproduction assertion, before producing seventh-mode evidence. The
discrepancy was not printed, so its magnitude and cause remain unresolved.
This failed auxiliary attempt, its source and complete logs are also
archived. It was not retried. No seventh-mode conclusion is accepted.

## Next safe gate

First diagnose the saved-pencil reproduction discrepancy with explicit
input/layout, residual and conditioning observations. Then preregister a
complete modal-group/cutoff comparison using reference-derived group
membership and enough modes to close every compared group. Preserve the
same 2% frequency and .95 mode-shape requirements; do not tune stiffness,
mass, cases or thresholds to hide the failed comparison. Any subspace
comparison must be independently checked and frozen before execution.

After a complete rehearsal passes, perform two new deterministic cycles.
Do not rerun or reclassify this historical failed freeze.

## Preservation

External archive: 59 data files plus manifest. All original run copies,
byte counts and SHA-256 values were verified. Canonical archive/status
records bind the location, exact manifest/audit hashes, all process
receipts, reference agreements, native observations and both diagnostics.
Only verified duplicate staging may be removed; original runs remain.

The continuum specialization and both implementations remain same-author
research, not independently reviewed production authority. Extreme
slenderness, wider dynamic/support/material parity, installed public
selection and the objective beam-shell connection remain open alongside
this modal-comparison issue. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
