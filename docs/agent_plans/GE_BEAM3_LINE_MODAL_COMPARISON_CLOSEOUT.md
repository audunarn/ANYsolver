# GE-B3 saved line-load modal comparison — development closeout

Frozen implementation `bc0ec7a9295a680563e67f363aeb451042840c49`, tree
`c7273c06a47ca3f5f794119adf0c7c6a96f04496`, follows the preserved native
line-load spectral closeout `f19d7d40e46f1c8bdb641de40d972e0cebb53d70`.

The one frozen external comparison completed with exit 0 in 2.598233 seconds.
It reused all native checkpoints and spectra unchanged: zero native nonlinear
solves and zero native eigensolves. New reference work was one BVP9 equilibrium
at 874 explicit samples and two continuum Ritz spectra (14/64 and 18/80).

| Curved macrocells | Worst of six frequency errors | Minimum diagonal material-frame MAC |
| --- | ---: | ---: |
| 1 | 14.4321% | 0.882398 |
| 2 | 5.1026% | 0.983333 |
| 4 | 1.3244% | 0.996625 |

All six compared roots are positive. The two reference polynomial profiles
agree to 2.3998557852019e-10 normalized eigenvalue difference. Reference Ritz
residual is 4.328055463766184e-10. The finest case is below 2% frequency error
for this fixture only; it is not a qualification decision, clustered-MAC proof,
critical buckling calculation or general nonlinear-dynamics result.

The zero continuum dead-force Hessian and nonzero native lifted-centerline
dead-force Hessian are consistent with their different variation coordinates.
Neither has been removed from or inserted into the wrong formulation. Q4,
S3, existing beams, defaults and all production source files are unchanged.

Separate inventories, not a combined pass count:

- Initial reference preparation: 19 passed, one failed, 0.943 pytest seconds.
- Balanced-prestress reference preparation: 21 passed, 0.773 seconds.
- First full rehearsal: 26 passed, nine shared-fixture errors, 1.591 seconds.
- Canonical-layout full rehearsal: 35 passed, 2.343 seconds.
- Read-only frozen-result inspection: five passed, 0.693 seconds; no solves.

The two unfrozen failures and their corrections are disclosed in the plan and
execution status. No failed request was retried, no canonical failure was
reclassified, and no mechanics or tolerance was altered. The corrected
rehearsal and frozen wave have byte-identical values for all twelve artifacts;
this is not represented as two formal qualification cycles.

Canonical comparison: 5,432 bytes, SHA-256
`3598e9192722c5a1da21eb2e20d8a49e36d37b9f1e0767c0ae01359e794602eb`.
Exact source identities, input/output hashes, separate test inventories,
transcript and all forty archived preparation-file hashes are recorded in
`docs/reference_cases/ge_beam3_line_modal_development_status.json`.

External result directory:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-line-modal-20260907-bc0ec7a`.
Preparation/failure archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-line-modal-preparation-20260907`.
All process trees have exited. Original temporary evidence remains preserved.

## Restart and next work

Do not rerun the completed native line-load histories or spectra. Use the
canonical comparison and immutable external packets for review. This closes a
development accuracy comparison, not the full GE-B3 goal. Independent review,
broader modal/buckling coverage, general six-resultant nonlinear section parity,
native public solver/package integration, and the separately qualified objective
beam-shell connection remain outstanding. Any further experiment must have a
specific unresolved question and a bounded fresh output directory.
