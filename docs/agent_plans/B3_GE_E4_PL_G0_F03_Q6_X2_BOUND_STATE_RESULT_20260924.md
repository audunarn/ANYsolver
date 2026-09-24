# F03 Q6 X2 certified-candidate state binding rehearsal

**24 September 2026. Unregistered source-process diagnostic. F03/G0B remain
open; G1 remains barred.** This run closes the prior X2 wrapper's specific
candidate-state gap: the physical pilot receives the scaled KKT state used
by the full inverse-column certificate, rather than accepting a separate
solve. It still reassembles the operators for numerical/physical validation.

## Implementation and focused checks

The certificate producer writes `candidate_state.json` with the complete
5,893-coordinate scaled KKT candidate and binds its SHA-256 in its measurement.
The integrated route verifies the saved bytes and passes that state into the
physical pilot. The pilot's existing energy, rank, compatibility, equilibrium,
and work checks run on that candidate. Physical recovery and the spatial audit
then use the saved physical result. The ordinary pilot solve remains unchanged
when no candidate is supplied.

The affected conforming-energy, nested-pilot, sparse-certificate, and wrapper
tests passed **39/39** before the rehearsal. A focused test checks state
recovery, wrong KKT size, and rejection of an incorrect finite candidate.

## Immutable rehearsal record

The [attempt and receipt](B3_GE_E4_PL_G0_F03_Q6_X2_BOUND_STATE_REHEARSAL_20260924/receipt.json)
show process exit 0, **1,426.95 s** supervised elapsed and **691,752,960 B**
sampled peak tree RSS under the predeclared 1,800 s / 2 GiB diagnostic
limits. The [top measurement](B3_GE_E4_PL_G0_F03_Q6_X2_BOUND_STATE_REHEARSAL_20260924/measurement.json)
reports 922.44 s certificate, 307.43 s physical validation/recovery and
196.51 s spatial audit. The complete output root, including the copied
runner-source snapshot, is 278,179,046 B.

The [certificate measurement](B3_GE_E4_PL_G0_F03_Q6_X2_BOUND_STATE_REHEARSAL_20260924/certificate/measurement.json)
reports 5,893 inverse columns in 1,474 blocks, condition upper bound
`716122.4783910362`, amplified backward upper bound
`9.032413569067423e-10`, and `CERTIFIED_WITHIN_LIMIT`. The raw inverse is
277,819,592 B, locally retained outside Git, SHA-256
`0d9dcba2121ec41f21619d0c1b648df9ae17cc74e2e4f7572c3c8b2c32987ada`.
Its recorded candidate-state SHA-256 is
`036ed6d3d28e5ee30c1e35cd319db42e1dfb6e0535102cea91e47913165012ed`.

Recomputed file hashes match the top measurement and the certificate's
candidate hash. The spatial input hash matches the physical JSON hash. The
[spatial record](B3_GE_E4_PL_G0_F03_Q6_X2_BOUND_STATE_REHEARSAL_20260924/spatial.json)
has all eight numerical fields within its diagnostic limits; maximum scaled
spatial-work defect is `9.48427000935226e-10` against `2e-9`.

Compared with the prior separate-solve V2 rehearsal, the physical free-state
SHA-256 is identical (`1ef091d6c13c5d93283af797dfd894f7989f9c0c45b87ccd271c4301f39d592c`).
The free state, root multiplier, eight signed band wrenches, and complete
functional norm (`612881.1715203497 N`) are exactly equal in the stored
float64/JSON records. This is a consistency observation, not an independent
mechanics reference.

## Gate interpretation

This supports source-process **candidate-to-recovery state binding and
resource feasibility** for X2. It does not establish the complete F03
scientific gate. Installed wheel and dependency identities, a frozen one-use
three-case producer, saved-only independent mechanical and arithmetic replay,
primal positivity, cross-grid physical settling, formal resource margin, and
independent mechanics acceptance remain open. No native B3-GE/E4-PL/B2
attachment capability is inferred from this classical-reference diagnostic.

Independent read-only review confirmed the candidate transfer, hashes,
inventory, physical equality, and resource receipt. It identified one narrower
remaining numerical binding: the certificate and physical paths still assemble
their KKT operators and right-hand side independently, without comparing their
identities. Passing the physical residual guard does not alone transfer the
certificate's error enclosure to the reported physical state. Bind canonical
matrix/RHS identities or independently re-enclose the physical reassembly
before claiming that numerical bound for the recovered observables.
