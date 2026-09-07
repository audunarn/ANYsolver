# Native load-aware static trial development

Parent ba82c0c46c6257648702f565e9a72944f68e3b67, tree
1913ef277c7c7810782b4486c9bd3391411d4cd5. Preserve the nodal-only native adapter,
restart/load guards, all physical kernels and old evidence. Create a private
NativeLineFibreStaticElement successor, not a legacy-derived element.

Use the preserved reference-arclength spatial-dead line potential with its
physical internal cell-rotation work. Own an immutable effective line pattern
inside a live actual-assembly scope bound to the exact mesh, state store and
element identities. Include that pattern in accepted state and exact local
replay. Require live material/rotation authority before evaluation and bind each
issued candidate to its store-specific validator and active trial before commit.
Different state-store registrations receive different validator objects.

The local solve subtracts the complete line potential. Add its nodal force part
back to the element's returned internal residual, and assemble that same nodal
external force once. Retain the load-aware Schur tangent. Do not alter the frozen
static boundary, line potential, material laws, interpolation or quadrature.

Reconstruct line-only work, spatial torque and Hessian independently from the
Q2 nodal polynomial, cross products and reference arclength, without calling the
producer load/Jet2 helpers. Compare full retained and condensed identities at
1e-11 and directional tangents at 1e-7. Require zero-line byte equality with the
preserved nodal adapter. Exercise real trial commit/discard, fixed origins,
locally valid wrong-load candidate rejection, missing scope, resealed load/state
corruption and changed-pattern rejection before mechanics.

Eighteen nodes: three analytical load checks, three directional checks, missing/
wrong-trial authority, four resealed mutations, zero-line equivalence, changed
pattern and accepted-load discard, distinct-store authority, and two closed
pressure routes and post-assembly authority-failure cleanup. Scope exit on any
exception discards an active trial. Each child uses one numerical thread, 24 GiB,
600-second wall and 120-second CPU-inactivity limits; no automatic process retry.
Smoke first, complete rehearsal, clean implementation freeze, then two fresh
deterministic cycles. Preserve failures and compare scientific packets exactly.

This gate integrates the real native assembler/state transactions, not yet the
global Newton load-case controller. Next bind proportional/constant/staged load
patterns and parameters at each solver evaluation, then extend strict typed
restart/recovery and qualify distributed-load engineering paths. Nodal couples,
mass/dynamics, complete workflows, independent review and beam-shell connection
remain required. No public registration, default, release or qualification claim.

The initial 17-node rehearsal passed 15 and failed two test-lifecycle checks:
active_trial_token raises when no trial exists, and trial-backed payloads expire
at discard. Use has_active_trial and capture owned values before advancing or
discarding tokens. Correct the new wrapper's exceptional cleanup to use the same
active predicate; add a deliberate post-assembly authority mutation proving
scope reset and complete trial discard. Preserve the failed rehearsal.
