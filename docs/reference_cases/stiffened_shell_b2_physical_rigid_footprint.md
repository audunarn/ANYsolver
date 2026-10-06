# Physical B2 rigid footprint: source development

The connected Q4 physical-footprint static and conservative reference-buckling route is implemented and verified against assigned source-development controls. Twenty unique instances passed by impact reuse across V2-V5; this is not a clean twenty-case campaign, installed verification, qualification or release. The two-member/two-shell public workflow completed with load factor 0.16324601652203263. The historical square POINT workflow retained 24.60872920125391.

## Explicit family and scope

B2PhysicalRigidFootprintDefinition selects B2_PHYSICAL_RIGID_FOOTPRINT_DIRECTOR_REFERENCE_V1_EXPERIMENTAL, separate from the historical six-row nodal-spin footprint. It requires an owned nonempty complete, edge-connected Q4 patch, distinct noncollinear nodes, a director consistent with attached flat shell faces and an orthonormal tangent basis. Existing topology, overlap, representability and supported constraint-rank checks remain active. No nodes merge. Selected positions and physical directors form a rigid region; outside nodes remain free. Normal spin performs no interface first work. Normal torque passes through noncollinear translation arms.

The new family admits single reference-linear static solves and a separate B2PhysicalFootprintBucklingRequest. POINT coexistence, batch recovery and modes explicitly refuse. Historical POINT and six-row footprint defaults, selection types and result identities remain separate. Static torque loading is separate from conservative preload.

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

Installed artifact verification is next. External transfer/reference comparison, thickness/refinement and drilling sensitivity remain open, together with public full-model unit/member-reversal covariance beyond local controls, mixed new attachments, broader shell/line/interior/distributing families and complete F12/B14. Independent OpenAI Read review supports adoption; unavailable different-family assessment is not replaced by author tests. No aggregate acceptance or publication claim follows.
