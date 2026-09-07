# Connected-member equilibrium controller development closeout

Frozen tests `a93417e859204a58321f9eeac1b5297150b49739`, tree
`22a9c7dc8831a1ed1c953a6437c269379792041f`, pass this bounded development gate.
Controller `66774bf` and force recovery `d4611ac` are unchanged. This turn adds
tests/evidence only, not mechanical or solver implementation changes.

## Separate inventories

- Smoke: 3 passed, 3 deselected; supervised wall 35.481 seconds.
- Complete rehearsal: 6 passed; supervised wall 53.318 seconds.
- Frozen cycle A: 6 passed; supervised wall 54.519 seconds.
- Frozen cycle B: 6 passed; supervised wall 53.915 seconds.

All 24 canonical packets match byte-for-byte between frozen cycles. Exact
commit/configured-runtime guards passed before and after both; these guards
are not complete dependency-graph qualification. All child processes ended
within existing limits, and no automatic retry occurred.

Cases are a two-macrocell straight plastic cantilever with load/unload/reversal,
a two-macrocell curved member fixed at both ends, and a four-macrocell curved
cantilever. Full mixed dense solves and equilibrium-recovery solves agree at
every accepted mechanical state, constitutive origin/history, residual, and
final recovery within the unchanged 1e-11 gate. This compares linear-solver
paths over the same native mechanics; it is not an independent formulation
oracle or proof over a geometry/slenderness domain.

Maximum normalized record difference is 5.180760571869078e-15; maximum final
recovery difference is 1.908195823574488e-15. Independently reconstructed
declared-quadrature Q2 line loads balance the sum of ALL nodal translation
residuals with maximum normalized error 1.1145513959121702e-16. This test sum
includes the small free-node residual, so it is not a support-only sum. A
separate post-cycle read-only audit of the archived residuals, selecting ONLY
constrained translations and directly differentiating the declared parabolic
reference curve, verifies support reactions plus applied load with maximum
normalized error 9.277641081628808e-16. Both checks satisfy the unchanged
1e-11 gate. Their distinct results are retained in the status; no mechanics
was rerun and no frozen test or packet was changed. Plastic history is nonzero.
The fixed-end curved case uses six compatibility completion equations; the
cantilevers use none. The three paths take 24, 15, and 15 Newton factorizations,
respectively, without full mixed fallback. No general speed claim is made.

Same-backend pause/resume is byte-identical to the uninterrupted result for
all cases. Changed support authority is rejected on restore. Historical
qualification evidence and earlier development results remain untouched.

The canonical manifest and status bind 104 data files plus a manifest copy at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-equilibrium-multi-a93417e-20260907`.
Original run directories also remain preserved. Only the hash-verified
intermediate transfer duplicate may be removed.

## Next production-integration boundary

Current-source inspection confirms the public `ge-beam3` selector in
`src/anysolver/elements.py` still constructs the earlier
`GeometricallyExactBeam3D3NElement` facade. The physical-fibre successor's
`NativeRetainedFibreElement` deliberately rejects generic stiffness, internal
force, mass, geometric-stiffness, and recovery calls. Thus these successful
private drivers are not production integration or full qualification.

The repository already has a token-bound material validator protocol in
`_native_material_protocol.py`, candidate checks in `nonlinear_state.py`, and
scalar dispatch in `nonlinear_element_evaluation.py`. Earlier P5 bridge tests
do not establish this retained-physical-fibre successor's integration. Next:

1. Bind the successor's compensated nodal positions, authoritative nodal and
   cell rotations, resultants, and fixed accepted material origins to native
   trial/commit/discard transactions. Verify rejected-step and replay safety.
2. Provide an explicit internal-coordinate assembly/solve contract. Keep six
   external DOFs per node; do not lose physical cell inertia by reusing static
   force elimination as a dynamic condensation rule.
3. Exercise actual solver interfaces under a private successor identity before
   public routing, with bounded straight/curved, plastic, support, and restart
   comparisons. Preserve the currently qualified public facade.
4. Complete native mass/current-state/modal/buckling routes, general coupled
   six-resultant nonlinear sections, independent qualification and review.
   The objective eccentric/curved beam-shell joint remains separately required.

Independent review is pending; the full goal remains incomplete. B2/B3,
Q4/S3 mechanics, aliases, defaults, qualification evidence and packages are
unchanged. No publication, public activation, merge, or push is performed.
