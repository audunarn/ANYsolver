# Declared automatic shell/rigid domains (development)

`anysolver.general_contact.automatic_domain` compiles an explicit declaration
once into an ordinary `ContactDefinition`. It does not infer physical bodies
from coordinates or rediscover contacts during a solve. Existing static
validators/managers own executable geometry, mechanics and material admission.

Declare `AutomaticContactParticipant(ContactSurface(...), body_id)` or the
corresponding exact `RigidContactBody`, dimensioned `AutomaticContactDefaults`
(normal stiffness N/m³, physical gap tolerance m), and one named
`AutomaticContactDomain`. Body and participant IDs are persistent caller IDs.
An optional explicit pair cap refuses complete surviving sets exceeding it.

Call `resolve_automatic_contact_domain(model, domain, settings,
explicit_pairs=...)` once. Call `verify_automatic_contact_resolution` immediately
before each ordinary solve/restart and pass its returned definition plus the
same settings. See `examples/general_contact_automatic_domain.py` for actual
static and restart integration. Verification rejects changed domain/reference
topology, formulation, physical skin geometry or settings; it never re-pairs.
`domain.to_dict()` and `AutomaticContactDomain.from_dict()` provide canonical
versioned persistence. Unknown schemas/fields refuse.
Rigid normal/axis components restore bit-exactly after finite/unit/shape and
ordinary owner-constructor checks, avoiding repeated-normalization drift.

## Pair and role rules

Every shell-containing cross-body participant pair is included unless excluded;
there is no initial-gap, nearest-pair or top-N filtering. Explicit unordered
exclusions precede defaults and overrides. Existing explicit pairs and domain
overrides have equal precedence: identical duplicates are idempotent, conflicting
properties/orientation or duplicate names for different pairs refuse.

Deformable shells integrate against rigid targets. For generated shell-shell
pairs, the source has larger median **per-face physical reference area**, not
larger total surface area. Exact area ties use stable participant IDs. Areas
use the actual affine S3 or bilinear Q4 Jacobian. Planar Q4 uses the analytical
integral of its affine signed Jacobian with exact stored-coordinate squared
area, preventing equal Q4/S3 area ties from depending on quadrature roundoff.
The standalone warped metric uses fixed Gauss16x16; these are role measurements,
not conservative gap bounds.
Exact supported element classes are qualified Q4 and S3 V2D native-parity
adapters. Formulation-owned selected skin positions include side, thickness,
director and reference offset. This first resolver refuses warped skins that
the planar reference adapter cannot represent. It never triangulates Q4 for
the role metric or reverses an explicit orientation to force admission.

Rigid-rigid pairs are reported as outside this family. Larger rigid sets use
an aggregate rigid-rigid count, avoiding quadratic outside-family
record allocation. The surviving shell pair cap is counted before geometry
work and interaction allocation.
Shared-body/self shell pairs are unsupported and require an explicit exclusion. Beam/native pairing,
domain overlap policies, general feature ownership and search-complexity claims
are outside this implementation. Complete shell pair sets may still be refused
by the existing bounded multi-pair mechanics validators.

## Provenance and result names

Every compiled interaction name is `automatic:<full identity>:<pair digest>`.
The identity binds declaration/defaults/exclusions/cap, explicit pairs, settings,
reference selection and policy. The ordinary checkpoint therefore rejects
changed automatic provenance, including an all-explicit domain. Original
explicit names and orientations/properties are retained in immutable selection
records; use `compiled_interaction_name` to look up solver pair results.

Old core dataclasses, ordinary explicit definitions and restart identities are
unchanged. Package exports are lazy. This is development implementation and
focused-check evidence, not engineering qualification or release acceptance.

## Nonmatching shell-pair workflow candidate

`examples.general_contact_automatic_domain.build_shell_pair()` declares one
Q4 bottom skin and two S3 top faces as two stable bodies. Reference face
medians 1 m2 and 0.5 m2 select the Q4 integration side automatically. The S3
physical offset is 0.01 m, thickness is 0.05 m, penalty stiffness is
1000 N/m3 and the gap budget is 50 um. One target node's uz is free; other
target translations/rotations are guided or supported, with no added springs.
The proposed path presses, opens and recontacts through the existing ordinary
finite-difference penalty profile. `solve_shell_pair()` verifies the compiled
reference contract immediately before execution.

The opt-in test `test_actual_nonmatching_shell_pair_path_parity_and_restart`
is selected with `ANY_RUN_AUTOMATIC_SHELL_PAIR=1`. It uses fresh models for
automatic, explicit, prefix and restart comparisons. Declared input scales
are 0.02 N, 0.02 Nm and 2e-7 J; both-body wrench and explicit response errors
must be <=1e-6 independently. Displacement/restart comparison uses rtol1e-7
and atol1e-9 m, and every accepted phase must satisfy the 50 um gap.

This candidate is **not mechanically verified**. The installed single-Q4
Jet2 proposal was correctly refused because that derivative profile needs a
refined source patch. The admitted ordinary penalty caller then timed out
at 100.161 s before its first full path returned. No accepted phase,
checkpoint, target displacement, parity or restart result was obtained.
Fresh-model isolation and before-solve runtime recording added afterward
have only syntax inspection. Earlier installed shell/rigid evidence remains
separate; it does not establish shell-pair mechanics.


A separate prospective builder, `build_projected_shell_pair()`, uses two
Q4 source faces, two S3 target faces and the admitted `projected_penalty`
normal law with Jet2, exact fine-Q1 support and `overlap_local_dev` gap
certificate. The geometric footprint, skins, k1000 and 50 um gap remain;
mesh/law differ from the timed-out single-Q4 ordinary penalty fixture.
It tests one press, not lifecycle or same-mechanics performance parity.
The test is opt-in with `ANY_RUN_AUTOMATIC_PROJECTED_SHELL_PAIR=1`.

The installed projected solver call returned after a17.00s test call, but
NumPy boolean report serialization failed before returned status, checkpoint
or mechanics assertions were saved. This is a retained NONPASS, not an
active-mechanics success. Two preceding constructor refusals (law token and
missing overlap-local setting) are also retained. The serializer was repaired
without another solve; that final test edit is AST-checked, unexecuted.
Effective installed JITdisabled/Numba1/pools1 were recorded before this solve
and terminal runtime/import records have no errors. Actual active contact,
target motion, complete gap/wrench and checkpoint remain unverified.
