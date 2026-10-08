# Physical B2 rigid footprint: source development

The connected Q4 physical-footprint static and conservative reference-buckling route is implemented and verified against assigned source-development controls. Twenty unique instances passed by impact reuse across V2-V5; this is not a clean twenty-case campaign, installed verification, qualification or release. The two-member/two-shell public workflow completed with load factor 0.16324601652203263. The historical square POINT workflow retained 24.60872920125391.

## Explicit family and scope

B2PhysicalRigidFootprintDefinition selects B2_PHYSICAL_RIGID_FOOTPRINT_DIRECTOR_REFERENCE_V1_EXPERIMENTAL, separate from the historical six-row nodal-spin footprint. It requires an owned nonempty complete, edge-connected Q4 patch, distinct noncollinear nodes, a director consistent with attached flat shell faces and an orthonormal tangent basis. Existing topology, overlap, representability and supported constraint-rank checks remain active. No nodes merge. Selected positions and physical directors form a rigid region; outside nodes remain free. Normal spin performs no interface first work. Normal torque passes through noncollinear translation arms.

The new family admits reference-linear single and selected batch static solves, plus a separate B2PhysicalFootprintBucklingRequest. POINT coexistence and modes explicitly refuse. Historical POINT and six-row footprint defaults, selection types and result identities remain separate. Static torque loading is separate from conservative preload.

Buckling requires zero prescribed displacement, Cartesian dead nodal forces, endpoint traces and explicit source-bound sectional traction reconstruction for every member. The full member Green work and algebraic multipliers remain. Q4 shell prestress admits physical N/M and homogeneous second moment N*h*h/12 with EXACTLY zero recovered shear. General S3, shell shear prestress, interior ports, weak lines, distributing footprints, prescribed prestress splits and dead-couple potentials remain open.

## Common reference work extension

For a0=Xs-Xb, Qb=Exp(theta_b), ds=Exp(theta_s)*n0 and fixed owned E:

    ct = Qb.T * (rs-rb) - a0
    cd = E.T * Qb.T * ds

The positive hemisphere n0.dot(Qb.T*ds)>0 is required. C and all coordinate Hessians derive from this same functional. Recovery uses actual actions -C.T*lambda; director multipliers are not raw display moments. Reference-arm expansions and compensated force-moment sums retain the existing recovery contract. Five labels, multipliers and gaps are exposed per incidence.

The inherited Q4 kernel has a linear director and no drilling geometric term. The new policy uses nodal Exp-directors followed by shape interpolation. Its tangential pullback is beta=n cross (Exp(theta)*n-n). Native physical first work contracted with the beta Hessian is added ONCE. The 35-field stationary coupling covector excludes PL/drilling forces. At strict zero shear the normal director second variation has zero first work. This spectral continuation creates no nonlinear B2 API.

Review identified a physical-resultant frame defect: native Q4 N/M are in the Equation-7 physical frame; the inherited kernel uses each GP tangent frame. BOTH experimental B2 POINT and new-footprint assembly now re-express physical tensors into the actual GP frame. N/H are director-even; M includes director parity. The new kernel identity is Q4_QUALIFIED_REFERENCE_RECOVERED_N_M_HOMOGENEOUS_SECOND_MOMENT_PHYSICAL_TO_GP_FRAME_V2_DEV. The new-footprint policy additionally names NATIVE_PHYSICAL_EXP_DIRECTOR_FIRST_WORK_PULLBACK. Element equations and historical evidence were preserved.

## Actual checks and preserved failures

V1: 7 FAIL/6 PASS. Public API mistakes and a shear-contaminated scalar fixture were preserved. V2: 3 FAIL/10 PASS, concerning torque load path, a missing batch argument and that fixture. V3: the 3 repaired cases PASS, including actual recovered Q==0. No tolerance relaxed. V4: 4 PASS: nonzero director-multiplier mixed-spin shell/pad cancellation, coexistence/selection refusal and two legacy public static full-KKT/dense-oracle controls. V5: 8 affected/new PASS after frame repair.

Controls include first/second finite-work plateau <=1e-6, common finite rigid motion and Hessian-plus-gradient acceleration work, actual-C.T wrench balance <=1e-8 and gaps <=1e-9, interface normal-spin independence, tangent-basis/rigid-frame/director-reversal covariance, native first-work identity <=1e-10, independent fixed N/M thickness Green work on square and skew/distorted rotated faces, nonzero director-lambda cancellation with omission/double-count counterexamples, sparse buckling versus a full singular indefinite dense pencil, equations <=1e-8 and constraints <=1e-9, midassembly cancellation, ownership/refusal and actual public workflows.

Each serial job used Python3.14 and pinned NumPy2.5.3/SciPy1.18.1/Numba0.68.0/llvmlite0.50.0 from unchanged CI network-v2, affinity[0], pools/Numba1, JIT off and unforced backend. Each loaded 246 actual source ANYsolver modules; pre/post thread controls were checked. All jobs stayed below 600s/2GiB sampled tree RSS. Logs/JUnit/snapshots/runtime/receipts and versioned manifests remain in .qualification/b3-ge-e4-pl/r8-b2-physical-rigid-footprint-dev-20261006-v1/.

## Remaining mandatory evidence

The pre-batch footprint baseline has isolated installed development evidence (36 fresh cases); the batch extension still needs its own installed boundary. External transfer/reference comparison, thickness/refinement and drilling sensitivity remain open, together with public full-model unit/member-reversal covariance beyond local controls, mixed new attachments, broader shell/line/interior/distributing families and complete F12/B14. Independent OpenAI Read review supports adoption; unavailable different-family assessment is not replaced by author tests. No aggregate acceptance or publication claim follows.


## Physical footprint batch extension (source development)

`solve_linear_many` now returns `B2PhysicalRigidFootprintBatchResult` and complete `B2PhysicalRigidFootprintSelectedCase` records. The five-row physical law and previous six-row/POINT batch output identities remain separate. The caller selects displacement/reaction DOFs, physical footprint IDs and member station recovery. `B2PhysicalRigidFootprintSelection` is required for the physical family; `B2NodalRigidFootprintSelection` retains its historical family admission. Both public method annotations declare this union without broadening either runtime selector. Only these outputs are retained: no complete displacement/reaction or unselected member/wrench arrays survive per case. One transient full static result is processed at a time; maximum RHS chunk is one. `recover_members=None` retains the existing batch meaning of no member recovery. Envelopes cover complete cases only and preserve first-case ties.

The later selected-member envelope addition returns signed extrema for each requested normalized station and local `N`, `Qy`, `Qz`, `Mx`, `My`, `Mz` component. A station index distinguishes repeated coordinates. It envelopes the existing `beam_resultants_local` case values, not body-load equilibrated-section records. No member request yields no member envelopes; cancellation and failure use only the complete case prefix. This is an experimental output addition, not physical-response qualification.

Selected constraint rows carry their ACTUAL compiled global row IDs and component labels. Compact multipliers/gaps follow that compiled row order; selected wrenches follow the requested footprint order. Director multipliers remain work-conjugate coordinates, not displayed spatial moments. A two-pad public control selects only the nonfirst pad and verifies rows20..39 against the full single-result entries, with no unselected pad retained.

The constructor already owns one eligible eager factorization. Compatible 1/10/100-case batches reuse that factor and perform exactly 1/10/100 solves. Pre-cancel and invalid selections/loads do not add a solve or refactor. Inventory/selection/member stations are copied before processing; each load is fingerprinted before the first RHS and immediately before its solve. Later load mutation and callback programming errors propagate. Only complete successful cases enter a returned prefix. Cancellation/closure stop between complete cases; final-case cancellation/closure remains completed. Numerical solve failure returns a failed complete prefix. Actual factory factorization failure propagates and cannot escape as an offset-only success. Typed body metadata is rejected before ANY RHS snapshot/driver evaluation; no body run was performed.

Source checks: V1 preserved 2FAIL/24PASS; the failures assumed lazy constructor factorization. V2 corrected those premises without product/tolerance changes and passed5affected/new cases. Thus29unique cases PASS by impact reuse (22new batch controls, one updated refusal control, six legacy batch/lifetime controls), not a clean29 campaign. 1/10/100 selected outputs, member/physical-wrench recovery, complete-case lifetime, ownership/refusal/mutation/failure and actual public example pass. `batch_workflow(10)` reports completed/10cases/1factor/10solves/chunk1/nonqualified.

Full-model controls compare dimensionally scaled PHYSICAL SI models (length factors .25 and4, force factors2 and3), common spatial rotation, and reversed physical member endpoint orientation. They compare selected global displacement/reaction fields, physical footprint wrenches and energy, including shell-arm normal torque. They do not reinterpret `_m`/`_N` fields as alternate units. Member-local section axes/resultant signs under reversal remain explicit rather than claiming those local arrays are invariant.

The new raw directory is `.qualification/b3-ge-e4-pl/r8-b2-physical-footprint-batch-dev-20261006-v1/`. Both serial source jobs preserve source snapshots, actual imports, pinned pre/post runtime, JUnit and resource receipts: V1 10.8196807s/224751616B; V2 5.5888492s/220495872B sampled tree RSS. Both satisfy600s/2GiB, affinity0/pools1/Numba1/JIToff/unforced pinnedCI controls. Installed batch verification and aggregate/external/different-family/full F12/B14 acceptance remain open.
