# Distributed 24-Q4/S3 coupled tangent: selected smooth direction

The [registration](general_contact_d1_distributed_coupled_tangent_v1.json)
(SHA256 `11428e031b9a1942eb8dd076e64071ca428df19625a4ca377ccad1bd4b7dd011`)
was committed as `71c73add` before its one execution. It fixes the accepted
24-Q4 pose, source nodes 18 and 43, ux/uz weights, two difference steps,
branch requirements and the original 1e−5 directional target. The contact
solver source has not changed from the accepted saved-pose run.

The [raw report](../../reports/general_contact_d1_distributed_coupled_tangent_v1_formal_20260927.json)
(SHA256 `08a6a41d814bb2e0c72cfa5012d8fbfcca473b771d24572288ebf1b8d7a87997`)
completed in 35.215 s. The [frozen-criteria verdict](../../reports/general_contact_d1_distributed_coupled_tangent_v1_verdict_20260927.json)
(SHA256 `90a044434dfc2110c82ee3ac3a8749e0eb87dfab17036357219f1cd4b53e50c5`)
passes every predicate. The saved 50 multipliers reproduce all pressures
exactly, with 18 active modes and zero pose-constraint error. At h=1e−6 and
5e−7 m, all active/support/overlap and four touched-pair derivative branches
remain fixed. The 98-free-DOF assembled tangent relative errors are
6.928e−11 and 1.794e−11. Subtracting structural-only assemblies isolates
the mapped contact action (78.8628 N/m), whose relative errors are
2.882e−10 and 7.171e−11. This denominator excludes the much stiffer
structural action (~118968 N/m).

Independent read-only review verified the source and saved-pose hashes,
the active supported nodes, independent DOFs, fixed multipliers, trial
discard, contact on/off subtraction and perturbation branches. It also
verified the imported case-builder blob `e70097501c4b9407b777601aa4a68459237fd2c4`
and branch-helper blob `8e21292ae13f8eac1ed3414ab88b5a22add43245`,
which the registration did not list. The adjudicator checks the saved-pose
hash and numerical predicates; source blob identities were checked in the
independent review.

The reviewer **accepted only the registered selected smooth-direction
tangent result** at this constrained, fixed-target elastic pose. It is a
directional derivative of the implemented residual with fixed multipliers,
not an independent mechanics oracle, full matrix qualification, deformable
target response, finite-rotation tangent or general C1 acceptance.
