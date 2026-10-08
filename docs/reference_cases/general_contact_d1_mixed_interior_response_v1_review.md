# D1 interior Q4/S3 press-force refinement: independent disposition

**Disposition:** independently accepted for the registered narrow press-force
refinement claim only. Full-cycle response, complete tangent, C1, installed
packages and release remain open.

The candidate source was `f03ac6c9dc779d7b0381c369b1aa14c416693589`
(tree `774c340e060897238e1724055f68b89b8858f4de`). The registration was
committed before execution in `63d0b9f0`; its SHA256 is
`b4bdfbd28c1753e3bb2a8324daac8e9ce4136f59398f2b3c438c7da025327f2d`.
The formal command was run once, starting at 16:33 UTC on 27 September 2026,
with the registered 1200 s limit and completed in 249.114 s:

```text
PYTHONPATH=C:\ANYworkspaceWork\ANYsolver-general-contact\src;C:\ANYworkspaceWork\ANYsolver-general-contact
python scripts/general_contact_d1_mixed_mesh_jet2_schur_press.py 32 reports/general_contact_d1_mixed_interior_response_v1_formal_20260927.json --pressure-cap-pa 250 --schur-step-cap-pa 200 --target-right-x-m 1.3
```

The [raw report](../../reports/general_contact_d1_mixed_interior_response_v1_formal_20260927.json)
has SHA256 `2843d7b7cc18557be8074fc8b6ae0e612606c30665533407189131a6e1cfcb1e`.
The [frozen adjudicator verdict](../../reports/general_contact_d1_mixed_interior_response_v1_verdict_20260927.json)
has SHA256 `c2ff4fdd8ffc810761ad1cb0f17ae5e19040cf8ef82cf856f61cc95e71ae19f3`;
all its predicates passed. Its `independent_review: pending` field records the
state at automatic adjudication; this document records the later review without
altering that verdict.

An independent read-only reviewer checked the registration, seven source/runner
blob identities, three frozen development-report hashes, raw result and verdict.
The reviewer independently recomputed the 32-Q4 normal force as
0.03547159554163 N, the prediction error as 0.03847%, the 24-to-32 change
as 0.40965%, and the 16/24/32 extrapolated limit as 0.035913873965482 N.
The 24-Q4 force differs from that limit by 1.63611%. The accepted second step
carried two −0.05 N nodal loads; it had 66/66 supported pressure rank, two
active modes, 4 augmentations, pressure change 9.99e−12 Pa and independent
minimum gap −0.496 µm. Equilibrium, paired wrench, support balance and the
registered integration indicator passed their frozen limits.

The predicted force comes from earlier development runs, not an independent
analytical oracle. The raw runner records Python and module paths; package
versions and source bindings were checked by the preflight and adjudicator,
but the raw JSON alone does not cryptographically attest the invocation or
process environment. This review does not promote a full-cycle or C1 row.
