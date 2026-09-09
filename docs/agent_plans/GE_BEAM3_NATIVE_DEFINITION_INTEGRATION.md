# Native curved-beam definition integration

Parent `fd7c489fe7d6ce745f76650b8dc701b6ef610a59`, tree
`d404b1caafdd4b77d9cff068772afb34b5564c84`.

The current private elements' `to_dict()` records identify their sections by
hash but do not contain enough constitutive data to reconstruct them in a clean
process. This step adds a reconstructible definition codec, not a new equation,
public selector, qualification claim or hot-restart owner. It serves the actual
native curved/generalized and physical-fibre scalar adapters, not the earlier
straight facade or a legacy beam wrapper.

Freeze the definition schema `GE_BEAM3_NATIVE_RECONSTRUCTIBLE_DEFINITION_V1`:
exact native class/family and formulation; three ordered node IDs and element
ID; complete stress-free coordinates, physical nodal triads and reference
evaluation/tolerance identities; exact quadrature; complete resultant-ellipsoid
or physical-fibre/flow-curve/background data; physical 6x6 section inertia;
recomputed section/operator/element identities; distinct static and dynamic
policies; production_qualified=false. Definitions contain no committed history.

Reading requires explicit external SHA-256, strict canonical bounded JSON,
duplicate/nonfinite rejection and complete exact schemas. Constructors are a
closed typed dispatch, never dynamic imports chosen by input text. Reconstruct
the real existing class and recompute all identities. No historical B2/B3 or
other GE-B3 formulation migrates implicitly. Changing physical data with valid
successor identities constitutes a different definition, not resumed history.
Existing authenticated state owners still control all hot restart.

New elements are unbound to a mesh or state-store validator. Attaching them to
an ordinary FEModel uses existing node/material/element registration. The codec
must not construct trial or committed states, infer virgin material from an
old history or advance station history. Capturing a definition from an already
used element does not capture its state and must leave its definition unchanged.

Physical section inertia is explicit and SPD. Supplying it does not enable the
static element's unsupported mass route: dynamics must retain cell-rotation
inertia through the distinct descriptor assembly. No Guyan policy or nodal-trace
mass is invented here. The two existing section laws remain distinct; neither
is reclassified as arbitrary elasticity, 3D J2 or the other law.

## Verification

- Straight and curved definitions, both actual section families, orders4/8:
  exact class, reference arrays, section/operator/element IDs, immutable inertia,
  fresh ownership and canonical bytes after reconstruction.
- Actual native state-store dispatch for both families and both geometries,
  using the existing actively plastic fixture and trial displacement: complete
  residual/tangent/state bytes equal original construction; commit once, replay
  original origins, evaluate a later trial and discard without history advance.
  Generalized load scope retains its actual distributed force/couple pattern.
- Rebound mutations of references, sections, flow curves, identities, quadrature,
  policies, IDs and qualification flags; history injection; invalid JSON; external
  hash rejected before construction. No missing case interpreted as pass.

Run schema/constructor tests first, then four real native transaction cases in
a separate inventory. Use existing Windows Job process supervision: one numeric
thread,24GiB,600seconds/child,1800seconds/wave,120seconds inactivity, exclusive
fresh external output, no automatic retry. After correction/rehearsal passes,
freeze and repeat the new integration inventories twice; scientific output
bytes must match where generated. Do not rerun earlier lifecycle/onset waves.
Same-author parity tests are not independent mechanics qualification.

Full goal remains active: actual current-core production solver integration,
spatial postbuckling, remaining section/load/solver/mass/state parity, installed
wheel/env qualification, independent review and objective shell connections.
No public activation, existing beam/shell mechanics/default or publication change.
