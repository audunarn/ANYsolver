# Stock CalculiX 3D footprint canary: one executed case

22 September 2026. A **single source-frozen exploratory compatibility
canary** ran on stock CalculiX 2.23. It is not E01/E02, not an executed
matched native reference, and not G0B/F03 qualification. Its exact model is
the strong finite rigid-footprint B31/S4 comparator documented in
`B3_GE_E4_PL_G0_CCX_3D_FOOTPRINT_DECK_FEASIBILITY.md`.

The source HEAD was `4535450cd3a95292301205ef30188cba5eb73a3f`.
Registration is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/ccx-3d-footprint-canary-registration-v1/registration.json`
(SHA-256 `9e44810aab77448bb8638459b83d14bb568261a32decc025a49a6303f5d98b53`).
The exact `+0.1 m` offset, `+1000 N` global-y tip-force deck has LF SHA-256
`38c32e157741d1f6b6fdfcd25f434b013a2ead4ede8ac8f1997e5a5f39f32f61`.
The pinned executable SHA-256 is
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
The one-shot run used one OpenMP thread and a 120 s process timeout.

Raw stdout, stderr, deck, status, displacement/force DAT, FRD, and solver
files are preserved at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/ccx-3d-footprint-canary-cases-v1/`.
Its result JSON SHA-256 is
`76432222d23b77d5376ace948cf5e57a39f96caafe245d46987ab32bc4c8bf00`.
An independent read-only review matched all ten pre-result raw file hashes
and the registered identities, and accepted only the narrow compatibility
terminal. Its record is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/ccx-3d-footprint-canary-adjudication-v1/adjudication.json`.
(SHA-256 `6bb1a468f269060904067fdf5a018a3f363d6363a247c3755c254c2f7cda0f19`).
CalculiX exited zero, printed `Job finished`, and recorded one full accepted
linear increment with 564 equations. The bounded parser found finite
translations for all 48 declared nodes and a beam-tip translation of
`(4.963084e-24, 1.903859e-7, 2.065770e-19) m`. No beam rotations were
printed in the selected DAT block. Wall time reported by the runner was
`0.0354 s`; this is a single compatibility observation, not a performance
claim.
The FRD contains the expanded mesh without a displacement result block;
the parsed DAT is the response evidence.

`RF` is printed for all nodes, including tied and expanded nodes. Its
physical support/multiplier interpretation has not been independently
validated, so this canary makes no force or moment-balance claim. The
seven-digit DAT output cannot establish the required connection-gap
tolerance. No energy, torque, thickness/refinement, section-idealization,
native B3-GE/B2/E4-PL agreement, or nonlinear result has been accepted.

Next, derive and test support/interface wrench recovery for this external
idealization, then register three or more refined E01/E02 comparisons with
matched native sections and connection meaning. If those idealizations
cannot be matched, record the difference instead of labeling the model an
executed numerical reference to the native workflow.
