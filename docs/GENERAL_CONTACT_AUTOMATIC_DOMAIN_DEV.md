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
