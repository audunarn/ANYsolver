# Literal-radius and affine-tool correction — development, 4 October 2026

This is a correction to existing opt-in actual-hemisphere sphere/cylinder owners,
not another geometry profile or general admission. The historical benchmark
assessment at8be4c355 remains source-bound; none of its consumed commands is
replayed or retrospectively regraded. Changed production bytes require the current
affected checks. FullD3/C0–C9, application admission and release remain open.

## Decision and equations

One scale discriminator demonstrated two discrepancies. With obstacle radius1e7m,
line work returned zero where the exact sum of declared binary radii gives
−0.224/−0.447nm gap. At origin1e16m, nominal1m tool translation disappeared in the
rounded pose while reported work still used the prescribed increment.

The existing physical equations are retained. The line envelope radius is
`R = Fraction(beam_radius) + Fraction(obstacle_radius)` for actual-hemisphere
profiles. Activation, integration fronts, gap work and bounds share that sum.
Historical owned-point/literal-projector profiles retain their floating radius law.
The local radial conversion preserves existing Fractions; floating input semantics
are unchanged. No global temporal helper or historical sphere API is changed.

The prescribed cylinder centre is the exact affine expression in the declared
binary origin, continuation factor and translation. Exact subtraction/projection
precedes local floating derivative calculations. Caps, line geometry, swept
interpolation, value-based cache keys and trapezoidal tool work share this path.
Global display coordinates remain floats; exact rational metre coordinates are
also exported as decimal numerator/denominator strings, keeping JSON persistence
inspectable. This does not qualify arbitrary-scale structural position arithmetic
or exact global skin-point output.

Restart binds `exact_literal_sum_activation_and_work_v2` and moving
`exact_literal_axis_translation_affine_static_v2`. Synthetic open checkpoints
with only the old radius or only the old path identity are rejected by the actual
solver. These are compatibility checks, not replay of historical execution.

## Tiny-front correction and explicit limits

Restoring the literal radius exposed a tiny B3 endpoint interval discarded by
relative coefficient trimming in old floating root proposals. Untrimmed normalized
exact polynomial coefficients now propose roots. When a signed exact derivative
Bernstein hull proves monotonicity, an endpoint Newton proposal resolves the
unique tiny front without an ill-conditioned almost-affine companion matrix.
Exact brackets/open-side refinement and panel controls remain authoritative;
proposals never certify inactivity. Integration/subdivision limits are unchanged.

An independent150-step exact scalar bracket verifies the left-end width, line
force and energy. The reversed width2.602085213965211e-17 near parameter1 is below
representable station resolution and returns **explicit non-success**, retaining
the integration-budget failure. An additional station-collapse guard rejects
rounded endpoint quadrature stations. No force is dropped, no tolerance is
relaxed, and no accepted response is claimed for that reversed case.

## Evidence and review

Raw root `C:/ANYworkspaceWork/contact_radial_contract_20261004/candidate02` contains
the current private build/install and installed checks. Wheel SHA256:
`b919d7227943be788bce9ee02ae6a0078edbeaf5c29e72281190c447d36a7c89`.
`installed_contract01` passes63predicates in14.113s, peak191385600B. It includes
expected negative guards, legacy parity, line/cap work and tangents, B2/B3 actual
cycles/restart, incompatible identities, rollback and the existing example.
Negative predicates are not successful engineering trajectories. Import roots,
JIT-off/one-thread runtime and package-byte identity are checked separately.
`installed_fields01` passes10affected axial/control and32/64-cell bending/line-field
checks in143.093s, peak203976704B. Both groups together:73passed predicates,
157.206s; all515package files match. Maximum response error0.08558%, maximum
line-densityL1/L2 error0.02677%; independent penetration4.754→0.993um under stronger
enforcement. Estimated integration error<=1.98e-12normalized. Original tolerances
remain unchanged. [Summary and exact identities](summary.json) binds the raw data.

Read-only independent source scrutiny identified the Fraction conversion,
reporting/JSON and reverse-front risks. The monotone derivative-hull derivation,
curved B3 active-rim scalar formula and physical-radius field recovery were checked
against their mathematics. Direct scalar/virtual-work references provide code
verification; a secondAI alone is not scientific acceptance or human approval.

Failed development records remain under
`C:/ANYworkspaceWork/contact_coupled_tool_staging_20261004`: representation_before01,
representation_after01(timeout), representation_diagnosis01,
representation_after03(JSON failure), representation_fields01(B3 front failure),
representation_front_before01 and representation_front_after01.
representation_after01 is not reused as current candidate
evidence: test additions occurred after launch. Earlier source checks and the
first private build are retained, not relabelled as the final artifact.
No speed claim or new performance campaign follows this correctness repair.
