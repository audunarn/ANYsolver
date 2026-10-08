# GE point actions and ordinary native point-input persistence

Development result only, 30 September 2026. Solver parent 371aa573;
ANYfem parent 7cf1fd7e, consumer implementation commit 6226230.
Exact source/wheel/site maps are in installed-v1/identity.json and the source
snapshots. No element, constitutive law, physical tolerance, checkpoint schema,
legacy selector, default, package version or release status changed.

GE results now retain immutable physical point loads from the actual assembly
work map, with model IDs and port high/low positions. Linear actions use reference
ports/C; finite actions use the spatial pose residual before chart pullback.
Signs denote loads exerted on each domain, minus the connection resisting
residual. Moments are about each port, not raw logarithmic multipliers or ground
reactions. Accepted recovery makes no new element/material/joint evaluations.
Rejection, cancellation, rebase and restart preserve the accepted-state contract.

ANYfem records own exact experimental GE/B2 mesh-native inputs in ordinary
.anyfem Projects. Explicit selector/status/schema pairs, deep ownership and
save/create revalidation reject mismatches and unsupported Project settings.
Reopen constructs the existing public owner, preserving GE actions and ordered
B2 cases/selection/cancellation. Inputs are not regenerated from Project geometry;
accepted solver checkpoints are not native-project input records. Standalone
consumer formats and legacy native/default routes retain their meanings.

| Installed inventory | Distinct cases |
|---|---:|
| GE reference-linear owner | 25 |
| GE finite owner/material/restart controls | 23 |
| Physical point action work/balance/lifecycle/low positions | 9 |
| New ordinary native input persistence | 36 |
| Existing GE consumer | 21 |
| Existing B2 consumer | 19 |
| Historical GE opt-in/default | 5 |
| Native Project/meshing compatibility | 33 |
| Total | 171 |

V1 is FAILED evidence: 170 passed, one failed, zero skipped. The failure was a
test fixture passing a tuple to an exact binary64-array joint API. V2 passes that
exact corrected selector; only tuple -> np.array changed. Wheel/source/site
identities and all other test AST/inputs match, so 170 passes are reused without
repeating the campaign. This is 171 distinct covered predicates, not an all-green
V1 run. adjudication.json records the union and unchanged-input checks.

Solver wheel SHA256 615596739690168a5ecc7f02ac3a20a078cda5490e79604a50440a61a7d2f597.
ANYfem wheel SHA256 0b6c51afc71266ef67168fafbbd53be126e64bdab4e750e724a4ad7dde8ee937.
All387 solver/98 consumer modules match source/wheel/site; 288 V1 imports are
onsite. Python3.14.2, effective BLAS/Numba1 thread and JIT disabled. V1 supervised
399.277s, sampled process-tree peak269524992B; V2 3.616s/200060928B. Limits600s/8GiB.
These are verification costs, not performance or development-speed claims.

Original source seven-case pass, consumer V1/V2 fixture failures and corrected
V3 source checks remain preserved. Source review found a cancellation gap after
the added linear recovery loop; final publish safe point and cancel-during-capture
checkpoint test close it. The low-part test exposes a >0.5N m lever couple that
would be lost without the stored subspacing offset. Independent source/consumer
and artifact review reports no remaining actionable finding in this slice.

This delivers recovery and input persistence predicates. Physical nodal torque/
drilling fidelity, full M1/M3/F01/F02/F13, general consumer dispatch/checkpoint
integration and aggregate gates remain OPEN. No F03 execution, main merge,
publication or external-reference acceptance occurred.
