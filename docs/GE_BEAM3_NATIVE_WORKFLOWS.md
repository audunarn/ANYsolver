# Native GE-B3 owned workflows

Explicit interface: `from anysolver import ge_beam3_native as beam`.
Selection is `beam.SELECTOR == "ge-beam3-native"` in this module's definition
and analysis factories. This is deliberately not a generic element-factory
alias: three-node topology alone cannot select it. The existing `ge-beam3`
straight P3 interface, B2/B3, Q4/S3 and every default remain unchanged.

## Acceptance and provenance

The immutable `PROFILE_BYTES`, `PROFILE_SHA256` and `PROFILE_ID` describe this
delivery workflow. Qualification requires a separate accepted record binding
the exact source revision, independent reviews, verification, installed wheel
and performance gate. The profile never self-asserts artifact acceptance.
Until that record exists, this interface is a delivery candidate.

Preserved implementation and checkpoint IDs deliberately retain their historical
`CANDIDATE_...` identities and `production_qualified=False` fields. These are
immutable implementation/state contracts, not a mutable release-status switch.
Do not edit these fields, infer acceptance from them, or relabel old history.
No blanket `production_qualified=True` is introduced. Qualification, when
accepted, applies only to the named workflow and its exact tested artifact.

Keep `workflow_provenance(owner)` with actual result/checkpoint bytes and their
SHA-256, definition bytes/hash and external artifact-acceptance identity. The
provenance record describes the definition; it explicitly does not validate a
checkpoint. Only the selected owner's authenticated replay may validate state.

## Construction and operation

1. Supply all three coordinates in [end, midpoint-parameter, end] order and
   physical, right-handed nodal reference triads. Straight and regular curved
   Q2 reference geometry are admitted; concatenated elements form piecewise Q2.
2. Build an `EllipsoidalGeneralizedSection` with explicit symmetric positive
   elastic/metric matrices, yield force and positive hardening, or a
   `PhysicalFibreSection` with physical axial/biaxial `Fibre`/`FlowCurve` data
   and the declared elastic background factor. These are exact native laws,
   not generic J2 or implicit conversions from another finite-strain law.
3. Call `define_beam(beam.SELECTOR, element_id, node_ids, coordinates,
   nodal_triads, section, section_inertia, quadrature=4)`. Physical 6x6 inertia
   must be supplied and positive definite. The registered 4/8 rules and optional
   generalized precise-arithmetic policy remain exact definition inputs.
4. Call `create_analysis(beam.SELECTOR, tuple(definitions), tuple(boundaries))`.
   The returned exact model owner supports native force, translation-control,
   recovery, restart and spectral methods; it does not subclass a legacy beam.
   Do not mutate its owned model or use it concurrently. Homogeneous supports
   and complete rotational support triples are required. Generic MPC, activity,
   point masses and mixed section-family models fail closed. Ordinary owners
   admit at most16 elements; explicit `retained_refinement=True` permits the
   separately tested generalized N32 workflows, not every driver at that size.
5. Retain every returned checkpoint/hash, including a genuine cancelled or
   failed solve's accepted prefix. Pass `checkpoint` and `expected_sha256`
   together to the same workflow's resume/recovery API. Definitions reconstruct
   fresh elements; they never manufacture an accepted history. State commits
   only after equilibrium, and nonconservative loads cannot become conservative
   spectral authority.

Distributed force/couple data use `LinePattern` and `DistributedPattern`;
absolute generalized dead-force schedules use `NodalProgram`, `NodalDeadForces`;
retained translation uses `TranslationProgram` for generalized sections or
`FibreTranslationProgram` for fibre sections. These are the exact existing
program types, not coercing adapters. A wrong family/workflow raises an error.
The owner's docstrings specify each method and authenticated checkpoint route.

## Coupled beam/shell subset

`create_coupled_analysis` admits a generalized beam subdomain connected to one
owned elastic qualified Q4 or S3 V2D through the explicitly selected V2
variational pose map. Shell keys are exactly `topology` (`Q4` or `S3-V2D`),
`coordinates`, `reference_normal`, `thickness`, `elastic_modulus`,
`poisson_ratio`, `shell_node` and `beam_node`. Beam nodes are1-based IDs;
`shell_node` is the existing zero-based local index. The beam programme is
`DistributedProgram`. Nodal force rows are shell DOFs followed by ordered beam
node DOFs. `shell_fixed`, `targets`, forces and control bounds are explicit.
Supply positive `shell_density` for modes; `None` means static-only.

Use `solve`, `recover`, `modes` and `buckling` on this durable owner. Each
operation builds a fresh bounded inner owner and mechanically replays exact
authenticated history. It never resets a previous owner's120s lifetime, rebinds
state, or extends historical checkpoint limits. Nonzero massless drill equations
are handled algebraically, not given invented inertia. All six slave-beam joint
DOFs must remain free for the current spectral adapter. This is not a generic
mixed FEModel, physical-fibre/shell or plastic-shell coupling interface.

## Engineering interpretation and exclusions

Modal results describe conservative current-rest states using physical retained
cell inertia; static condensation is not substituted into mass. Frozen-current
buckling factors are predictions, not nonlinear limit loads. Active-yield,
nonconservative and unsupported spectral states fail closed. Signed negative
modes and seeded postcritical branches remain explicitly unstable; no stable
postbuckling or path-from-rest claim follows. Spectral root windows and driver
limits remain mandatory where required.

This interface does not qualify arbitrary materials, finite-velocity rotational
dynamics, generic beam-shell meshes, untested connections, general shell
plasticity, or a release/default change. Native generalized recovery supplies
resultants; physical fibre stresses are available only from the fibre law.
Existing element mechanics and all historical evidence remain unchanged.
