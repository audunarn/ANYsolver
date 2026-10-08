# Free-target mixed tangent v2: selected direction

The [v2 registration](general_contact_d1_free_target_tangent_v2.json)
(SHA256 `97aaadcad12a6e2e95514ed70fa77fbb22781f35b600cb76924a9a2684a91b93`)
was committed before one run. It fixes source commit `a32c1e47`, the saved
accepted 24-Q4 pose, a left-edge clamp on S3 target nodes 51 and 54, the
mixed source/target direction, a second-order negative one-sided stencil,
two step sizes and separate force and moment limits. The changed support
admits the saved geometry but does not make it an established equilibrium
of the free-target model.

The [raw report](../../reports/general_contact_d1_free_target_tangent_v2_formal_20260927.json)
(SHA256 `9137d3140a1d4fcb8c6e6fb5f0270aa0174363c5c3965386bb85eb3651420a03`)
ran once in 78.440 s. The [verdict](../../reports/general_contact_d1_free_target_tangent_v2_verdict_20260927.json)
(SHA256 `677e3a0e799e041a258350bbe37c0e505dac5c7a48f28d0b19831d4addfb71e0`)
passes every frozen predicate. At h=8e−7 and 4e−7 m, both negative
perturbations preserve the active-pressure and support masks, overlap
signature and all 48 pair derivative signatures. All 110 reduced rows are
classified into 104 force rows and six moment rows. Every coupled and
mapped-contact component error is below 1e−5. The largest mapped-contact
moment relative error is 2.932e−10, falling to 6.591e−11, on a nonzero
0.000318640 Nm/m action.

Independent read-only review verified registration, saved-pose, development
diagnostic, raw and source blob hashes. It checked the stencil
`[3F(0)−4F(−h)+F(−2h)]/(2h)`, contact-on/off subtraction, fixed
multipliers, trial discard, both negative-pose branch checks and separate
force/moment scales. The adjudicator checks numerical predicates and the
saved-pose hash; the other source identities were checked in this review.

The reviewer **accepted only this selected mixed source/target directional
tangent gate**. The [v1 moment-gate failure](general_contact_d1_free_target_tangent_v1_failure.md)
remains failed and preserved. V2 does not establish a re-equilibrated
free-target contact solution, complete tangent, other formulations or
general C1 acceptance.
