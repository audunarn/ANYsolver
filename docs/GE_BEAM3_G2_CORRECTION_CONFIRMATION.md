# G2 reviewed correction and confirmation protocol

Successor of blocked review `435f848d79ef5180e1fd7b8778bc7f2f935219e0`;
original candidate `3e89a5e30ba86103bad6c236356d700229d2820f` and all development
and accepted G1 evidence remain immutable. No existing qualification is revoked.

The user authorizes correction of G2-IR-01 through G2-IR-04, regression tests,
independent re-review, and formal G2 confirmation only after acceptance.
Private one/two-element exact-elastic S09-S14 scope remains unchanged.

## Correction extent and fixtures

Permit one entry-point type guard in the shared private G1 `solve` to reject
non-G1 owners before callback/evaluation/publication. G2 retains the authorized
assembly/state seams and its own constrained solve. This is an orchestration
guard, not a change to element mechanics, coefficients or constitutive laws.
Regress both explicit base and super-bound calls on virgin and accepted-prefix
G2 owners with root x offset 0.001. Require byte-identical state, generations,
journal/checkpoint, no active trial, and successful authenticated replay.

Preserve the original fixture file; supplemental tests use its material,
geometry, tip loads, noncommuting target vectors, relative-pose offset/frame,
common transform and all three perturbation steps. Replace implicit invariant
tolerances with norm(a-b)/max(1,norm(a),norm(b)) <= 1e-11 using the existing unit
length/force/moment scales. Directional tests retain 1e-7 at every step.

Add nonzero loaded prescribed-target work checks at two noncommuting frames.
Independently reconstruct the spatial Exp Jacobian by Rodrigues' formula and
check target perturbation work, constraint-Jacobian work and chart/spatial
support moments including sign. No target interpolation is added to runtime.

Add explicit DOF/row transport of g/J/H and work-dual reactions for selected
orientation axes and eccentric relative poses. Use global rotation, node-ID
permutation and reversed element connectivity, with physical node frames kept
distinct from element reference triads. Check accepted physical rotations.
Also test the actual assembled constrained Newton block at nonzero multipliers
and nonzero chart increments against finite differences of its full residual;
compare multiplier and independently reduced nullspace Newton increments.
The directional vector is linspace(-0.3,0.2); multipliers linspace(0.1,0.3).
These are verification fixtures, not changed mechanics or tuned coefficients.

## Formal confirmation

Freeze the corrected source, tests, exact ordered inventories and separate G2
confirmation runner in a clean commit. Independently review all four findings,
the added curvature check and runner before execution. Review must have exactly
five keys, empty findings, independent reviewer, and exact candidate commit/tree.

Smoke and full rehearsal precede formal execution. Run the G1 49-test regression
inventory separately; do not reinterpret it as replacement accepted G1 evidence.
Run two serial G2 cycles in fresh external directories: one numerical thread,
24 GiB/tree, 600 seconds/child, 120-second CPU/output inactivity and <=1800
seconds/wave. No automatic retry; terminate the complete tree on resource breach.
Keep all failed/rehearsal logs outside canonical acceptance evidence.

Bind all runtime source, G2 and supporting G1 tests/fixtures, contracts, runner,
process harness, Python executable and installed distribution versions. Verify
clean Git HEAD and every binding before and after each child and publication.
Require exact ordered passed setup/call/teardown records, all milestones, and
byte-identical development packet and supplemental correction scientific records
across cycles. Do not relabel the old development packet as a certificate.
Publish a separate canonical aggregate exclusively after all checks pass;
validate staged bytes and atomically link on the same volume. Review the final
evidence independently without rerunning mechanics.

Terminal: `PROVISIONAL_GO_GE_BEAM3_G2_CONSTRAINED_ELASTIC_STATIC_ONLY` only after
accepted implementation and complete deterministic confirmation. Any authority,
process, state/restart, constraint/work or evidence failure blocks confirmation.
No full general-static parity, G3, public integration, default change or release.
After accepted G2, recommend freezing G3 graph/junction fixtures; do not run G3.
