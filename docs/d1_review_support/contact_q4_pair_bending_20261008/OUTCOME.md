# Q4 pair force-loaded bending development outcome

The installed ordinary force solver completes a genuinely deformable Q4/Q4 contact fixture with nonuniform upper displacement, independent lower normal motion, and free rotations on both bodies. Fresh continuation matches the full endpoint. This is development evidence; engineering acceptance and release are not established.

## Physical and numerical scope

Two upper Q4 faces contact four lower Q4 faces. Automatic area selection retains the upper six-node pressure side and all positive Q1 supports, including shared material nodes. The upper left edge is clamped; no common-source-uz tie remains. Only the four lower corner normal coordinates are supported, with three minimal inplane anchors. Rotations remain free elsewhere. Loads at upper nodes 3 and 6 are each -5e-5 N in z. Material, fine Q1 law, projected penalty 1000, 50um gap, geometry/derivative budgets and whole-face swept admission are unchanged.

The reference skins are nominally coplanar at z=.015 m; represented binary skin heights differ by -1.734723475976807e-18 m. The authoritative admitted skin is `reference_skin + u + offset*(theta cross reference_director)`, with offsets -.025 m / +.025 m. This is the existing linearized director work map, not an SO3 or deformed-normal skin model.

The original default solve tolerance 1e-6 completed but failed the frozen independent equilibrium gate. The lead adopted one explicit existing tolerance 1e-12 for this example, preserving physics and all scientific gates. The original failed report and its captured source remain immutable. No solver default, product equation or source payload changed.

## Actual checks

All equilibrium/wrench errors below are normalized with separate positive scales 1e-4 N and 1e-4 Nm, about origin (0,0,0). Gates are 1e-6 for equilibrium/wrench, 1e-5 for directional tangent, and 50um for gap.

| Check | Observed result |
| --- | --- |
| Full free-coordinate equilibrium | 1.5870432056292853e-12 |
| Resumed free-coordinate equilibrium | 8.150705541917186e-14 |
| Exact accepted binary-pose all-pair gap lower bound | -3.6740036580909347um |
| Upper normal displacement range | 3.7818849628221637um |
| Lower normal displacement norm | 2.9875746135871837um |
| Upper / lower rotation norms | 1.1267324946347896e-5 / 1.5875938302499036e-5 rad |
| Rotational skin displacement norm | 4.866967924377297e-7 m |
| Physical-skin force / moment errors | 1.0164446296459926e-16 / 2.142842905514856e-16 |
| Structural-coordinate moment error | 1.9033320286241912e-7 |
| Both-body directional tangent, two perturbations | 3.5531881540481714e-10 / 7.652268529082066e-10 |
| Fresh restart endpoint maximum displacement difference | 1.4179331537036988e-18 m |
| Active pressure coefficients | 3 of 6 |

The structural-coordinate moment deficit is nonzero and retained. Its physical-skin counterpart includes the second-order term `offset*(theta cross dref) cross F`; this fixture remains within the frozen wrench budget. Instantaneous upper/lower contact residual work is 2.815211048515665e-10 J / -1.680960326442622e-10 J. External residual work is 3.3558331658974407e-10 J. These are endpoint residual contractions, not integrated path work or a potential-energy identity. The executed convention is `projected_weak_gap_nonpotential_v1`.

The independent static gap bound uses Fraction arithmetic on the actual binary points returned by the manager, after an independent skin reconstruction agrees within 2.220446049250313e-16 m. It examines every source/target face pair and all nodal/corner combinations. Negative signed numerators are divided by a positive z-component lower bound on normal length. The bound is sufficient and conservative, not an exact projection-minimum result. `saved-pose.json` binds the immutable full report hash and closes this authoritative-pose check without repeating the solver.

## Independent contact reference and pressure detection

Separate Fraction rectangular Q1 integrals produce support and weighted-gap rows, including shared source-node sums. The qualified structural elastic K is reused explicitly. The independent reference enumerates all 64 pressure active sets using `H = G_free K_free^-1 G_free.T + diag(S/1000)` and checks nonnegativity/complementarity and structural equilibrium.

The matched reference contact operator error is 1.6653345369377348e-16 and independent linear-reference equilibrium error is 1.74982029387142e-14. All six support-weighted constrained pressure-compliance eigenvalues are positive: smallest 1.3652191831014562e-6, largest .04160290452172261. The weakest signed pressure mode has actual structural compliance work 1.3652191830920415e-6, with nonzero structural forcing. No mode was removed. This demonstrates six-mode detection for this finite, supported linear reference, not a universal inf-sup or mesh-stability qualification.

The actual nonlinear displacement differs from the linear reference by 1.829664904298842e-6 relatively. That observed correction is reported separately: a 1e-6 nonlinear-versus-linear code-comparison claim is not made because no truncation-error bound has been derived. The 1e-6 matched-reference gates apply to the contact linearization and independent reference equilibrium only.

## Restart, refusal and installed execution

Exact accepted snapshot inventories are full [.5,1], prefix [.25,.5], and fresh resume [.75,1]. Resume binds `full-accuracy.json` by SHA-256, not the failed original `full.json`. Actual public calls refuse changed automatic provenance, changed contact controls, tampered checkpoint content and continuation from the old default-tolerance checkpoint. Public precancellation raises before changes to declared FEModel fields. The representation check is not a proof of every hidden transaction field.

The installed public CLI completed. Product sources were unchanged, so the immutable verified 629-payload wheel `d23e40b64e078f65940b9a0efd8260a98be72153f26a8ef248a0f5efc0e43c2b` was reused. Every private import was checked against that artifact, with JIT disabled and Numba/BLAS pools at one thread. Unchanged historical defaults, geometry proofs and compatibility evidence are reused by source impact; no new default identity claim is inferred from this fixture alone.

## Preserved failures and accounting

Ten guarded jobs used exactly 127.60764899998321 of 420 process-wall seconds; 292.3923510000168 remain in this scope, including the unused protected 60-second final reserve. Maximum job 21.619471799989697 s; peak sampled process-tree RSS 189.7109375 MiB. Nine JUnit cases comprise six passes and three retained failures; the tenth job is the passing CLI. There are 2919 authenticated private module imports. No job is active.

Retained failures: the first reference test called an overlap-only local kernel on an independently empty pair (test repaired by exact exclusion); the original default-tolerance full solve failed independently recomputed equilibrium; the first refusal test used an incorrect import location (test repaired). None is erased or reclassified as a passing original run.

Raw evidence: `C:/ANYworkspaceWork/contact_q4_pair_bending_20261008/`, including immutable per-attempt commands/source snapshots/stdout/stderr/JUnit/runtime, `ledger.json`, `CLOSURE.json`, and all outputs. `reconcile_metadata.py` only reads saved evidence and authenticates bytes/counts/inventories; it does not rerun mechanics.

Remaining programme gates include spatial/refinement pressure stability, general deformable normal-trace admission, nonlinear independent-reference truncation control, finite rotations/director evolution and the broader programme acceptance/release requirements. This outcome closes one force-loaded small-motion bending slice, not those gates.
