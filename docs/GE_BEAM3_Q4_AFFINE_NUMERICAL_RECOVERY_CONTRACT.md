# Q4 affine chart-image physical recovery: numerical gate contract

Status: FROZEN_DESIGN_CANDIDATE_PENDING_INDEPENDENT_REVIEW. Prepared by /root/q4_recovery_feasibility from the accepted affine exact-gate design and q4-affine-numerical-integration-notes.md. Proposed clean implementation base5307667ad5f300703140c16e8afcd6084beded69, tree cef701d71ca19544bd5195cd4fb1c0101f042d9f. Exact prerequisite d49aacdd64dd9226e431f72e3078fbfb6cabb957, tree dc328e01e612b6988dda3b04080a4c3340c1808c, is now independently accepted for its three fixtures: two formal cycles,21375 zero coefficients per cycle. Bind docs/reference_cases/ge_beam3_d49aacd_affine_evidence_review.json SHA-256 a40277da9d95692e690f51e19dc069a7229455bcf76b84ea11f5f0dbd71dda7f and ge_beam3_d49aacd_affine_evidence_manifest.json SHA-256 f5983d496cdac583c8ce4d13c49bcd882579aa0751864389bcc588d8b6e2e529. This successor contract requires an independently accepted hash-bound design review before implementation; frozen implementation review is additionally required before numerical execution. No numerical gate result is asserted here.

## 1. Identity, source authority and integration boundary

Introduce private facade AffineQ4PhysicalRecovery in a new _ge_beam3_g3c_affine_q4_recovery.py module. Its evaluate(displacement, accepted_rotations, *, cancel_check=None) accepts the existing exact binary64 shapes (24,) and (4,3,3). It has descriptor() but no commit, graph restart or public factory API. cancel_check is None or a callback returning an exact bool; True raises private AffineRecoveryCancelled before construction or final publication. Invalid callback output fails closed. Apply definition pre/post-observation guards around this callback too. Do not inherit LocalShell merely to alter its historical flags. Reuse its pure analytical deformation/chart helpers and call the actual unchanged qualified Q4 kernel through a fresh owned virgin family object.

New facade policy: GE_BEAM3_G3C_AFFINE_Q4_PHYSICAL_FACADE_V1. Recovery ID: GE_BEAM3_Q4_AFFINE_CHART_PHYSICAL_RECOVERY_V1. Internal representation ID: GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1. Record the actual qualified operator formulation ID separately; do not rename the qualified element or original 35-coordinate system. Historical GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1 results remain unchanged and recovery-incomplete. Old facade/recovery/representation identities are rejected by the new definition boundary, not redirected.

Initial numerical admission is the finite registered construction set in section4, including ALL54 base shape/scale/pose contexts and ALL10 graph-reference variants plus their registered D4, director and passive-transform contexts. It is not arbitrary affine or almost-affine geometry. The facade definition must include a construction_id, immutable source coordinates/node identities/director/material direction, recipe and actual binary64 byte fingerprints. Freeze these reference constructions in a new successor numerical registry before implementation freeze; never edit the inherited fixture manifest or its evidence. Reconstruct/check the registered recipe, then require bit-identical supplied reference arrays; reject foreign geometry before family evaluation. Never project, snap or repair rounded coordinates into affinity. The usual finite/positive-Jacobian and orthonormal-director source guards are retained, but their tolerances are NOT proof of exact affine geometry. Current positions may warp. Preserve the existing smooth simple-top Procrustes admission and relative rotation limits.

Section admission remains scalar homogeneous E=100, nu=1/4, thickness=1/10, three virgin layers; no generalized/history section, offsets, initial fields or external loads. These are genuine remaining parity obligations, not declarations that legacy functionality is unsupported.

Before numerical acceptance, independently verify a source-level exact homogeneity/isometry/D4 extension lemma for all registered ideal recipes. Show centered translations remove shifts, frame/strain/resultant maps transform covariantly under the proper transformations, positive scale lambda leaves reference frames invariant and multiplies station measures by lambda^2, and transformed original stationary/M maps preserve the linear energy identity and chart-image cubic cancellation. Include thickness-fixed membrane/bending/shear scalings and the constraint/RREF-coordinate transformation; do not infer this lemma merely from three exact specimens. If any required lemma is unproved, keep numerical acceptance blocked and preregister exact per-context prerequisites under successor authority; do not drop cases. This lemma concerns ideal constructions. Binary64 passive transforms may have a tiny nonzero affine residual: evaluate the unchanged operator on the actual registered rounded arrays and test all numerical identities directly. Do not call those arrays exactly affine or silently erase their residual. Passing finite registered contexts does not establish an unrestricted geometry theorem.

Bind the complete immutable inherited source graph before implementation. In addition to accepted exact-gate authority and the five inherited coefficient-audit source hashes, freeze these LF-normalized files:

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| src/anysolver/e4_pl_element.py | 293258 | 7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38 |
| src/anysolver/elements.py | 244692 | f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37 |
| src/anysolver/_ge_beam3_g3c_local_shell.py | 19430 | 69d9f27a96ed7e9a5959a42a081eeafbbe72021de6e4da1f91355c5fb3850f10 |
| src/anysolver/_ge_beam3_variational_shell.py | 7234 | b0db7a83633f4a835c06e940a6f0de36ab958f7e816c37a23c6ebc16259a2a60 |
| src/anysolver/_ge_beam3_mixed_ad.py | 8989 | b299ff765cd2eaae8b33a2ba1d05069f6fe8c39209e1eac75df356a2afb1fe36 |
| src/anysolver/_ge_beam3_pose_joint.py | 12350 | 69cfb0a71761ab7cad0d62080d81511949e7c920f7f70162bcaba0497b402657 |
| src/anysolver/_ge_beam3_g3c_definition.py | 6517 | 4b46b870fec010e3378df83c374d763f858d8f25820c14f9704dc6f0a656f0c2 |
| src/anysolver/_ge_beam3_g3c_owner.py | 25718 | 18b9565d56192e23f192b1a3fbae3cb12ed7ede958c0e4b3e46279a799d1afc5 |

Also bind docs/reference_cases/ge_beam3_g3c_fixtures_v1.json, SHA-256 d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006. Source changes require reviewed successor authority; never copy new hashes over old evidence.

## 2. Actual physical reconstruction and stationary work

Use actual source _recover_planar_mixed_fields and its original 35-coordinate H, coupling and certified solution S=H^-1 coupling^T. If T maps numbered local components to reference-global components, recover M_g=-N_epsilon,g S[14:] T^T. Independently verify M_g d against actual source independent strain and sum w M_g^T C M_g against actual physical stiffness. Keep N_sigma beta_linear explicitly named as the old mixed equilibrium diagnostic; it is not the new constitutive resultant.

Use actual _nonlinear_geometry T0,R0,Bm,Gw and ordered detw values. For y=T0 d, construct n=[p_x^2/2,p_y^2/2,p_x p_y], p=Gw y; derive both first and second derivatives analytically. Transport membrane engineering components and derivatives to the Equation-7 frame before forming e=M d+n and s=C e. Bind coincident physical station positions and measures, not only station indices. Current physical station positions use actual shape interpolation of trial nodal positions.

Retain actual old local force f and tangent K unchanged. Subtract only the unchanged PL/hourglass local contributions to identify actual source physical f_p,K_p. With the full common-pose map d(q), D=d_,q and S_i=d_i,qq, compare recovered energy and work to

    g_p = D^T f_p
    H_p = D^T K_p D + sum_i f_p,i S_i.

For every station independently assemble internal Hessian w[[C,-I],[-I,0]], its two-sided inverse (1/w)[[0,-I],[-I,-C]], and internal state (e,s). With F(q)=M d(q)+n(d(q)), J=F_,q and F_,qq, verify full 64-coordinate stationarity and condensed force sum w J^T s and tangent sum w[J^T C J+sum_a s_a F_a,qq]. Condense the actual external/internal blocks; do not replace this test by the constant constitutive metric identity alone. Include both Hess(n) pulled through D and (M+Dn)-weighted Hess(d).

Add numerical PL/hourglass chart work only when comparing total force/Hessian. Keep their energies and forces separate and exclude them from material resultants and constitutive station energy. Do not assert recovered/off-image local f or K equality: exact identity applies on the chart image. Explicitly compare D^T grad(Phi)=0 and D^T Hess(Phi)D+sum Phi_,i Hess(d_i)=0 as derivative sentinels.

### Independent proper-polar differential proposal

The checker must independently review/implement the following route rather than import production Davenport/Jet2 mechanics. Treat Xc and xc as4x3 row arrays of centered reference and current positions, and A=xc^T Xc. The proper Kabsch fit satisfies A=R S, S=R^T A symmetric rank-two positive-semidefinite on the admitted planar branch. R maps reference-global vectors into current-global vectors. With hat(v) w=v cross w and axl(hat(v))=v (no extra factor1/2), let Kpolar=tr(S)I-S. It is nonsingular when the two in-plane singular values are positive; enforce the existing admitted branch rather than add an arbitrary regularizer.

For translational chart coordinate i define A_i from the centered nodal translation derivative, M_i=R^T A_i and b_i=axl(M_i-M_i^T). Then

    omega_i = Kpolar^-1 b_i
    R_i = R hat(omega_i)
    S_j = -hat(omega_j) S + M_j
    Kpolar_j = tr(S_j)I-S_j
    (M_i)_j = -hat(omega_j) M_i  [A_ij=0]
    omega_i,j = Kpolar^-1[axl((M_i)_j-(M_i)_j^T)-Kpolar_j omega_i]
    R_i,j = R[hat(omega_j)hat(omega_i)+hat(omega_i,j)].

Centering is differentiated explicitly. R has no nodal rotation-increment dependence. Verify the symmetry of mixed second derivatives and differential orthogonality identities independently. Combine these with independently authored analytic Exp/Log first/second derivatives for local relative nodal rotations and translational d=R^T xc-Xc (column convention). No numerical frame differentiation or borrowed production Hessians are permitted. These equations are proposed source mathematics requiring independent review, not accepted numerical evidence.

### Spatial work connection

For additive chart increments q=(u,eta), spatial rotational variation is J_left(eta_i) delta_eta_i. Assemble P=diag(I3,J_left(eta_i)) over the four nodes. Solve P^T r=g for spatial wrench r. The derivative with spatial rows/additive columns is Jsp=P^-T[H-Cconnection], where (Cconnection)_ij=sum_k (dP_ki/dq_j)r_k. Verify this work connection independently; H is the conservative symmetric chart Hessian, whereas Jsp need not be symmetric. Do not compare raw additive Hessians under a rebase as though their coordinates had not changed.

## 3. Physical outputs and state-safety protocol

Return a frozen detached result containing definition/operator/recovery/representation identities; virgin/uncommitted provenance; d,D,Hess(d), current fitted R; four positive reference weights and natural/reference/current station positions; numbered and physical strains/resultants; reference/current tensor representations; physical energy/force/chart Hessian; numerical PL/hourglass diagnostics; full station residual and Schur check data. No fibre stress, material history or accepted graph-state claim. No mutable arrays, dictionaries or aliases into candidate kernels escape.

Let sigma=sign(numbered normal dot authoritative physical director). Use actual source physical-director transforms: membrane diag(1,1,sigma), curvature sigma*diag(1,1,sigma), shear sigma*diag(1,sigma), acting on both strain and resultant conjugate components. Engineering membrane/curvature xy is twice tensor xy; resultant xy is tensor xy. Transform reference tensors into current space with fitted R on both sides; transform shear vectors with the same R. Connectivity reflection is not director reversal. Reverse the actual director policy separately without changing connectivity. Material direction is a physical vector, not a raw local angle.

Capture immutable definition bytes, seal and lock before any caller-controlled descriptor/material/array observation. Revalidate captured identity immediately after each such observation and BEFORE family construction/evaluation, then at finalization. Reject reentry or concurrent access. Every evaluation creates a fresh virgin origin and returns uncommitted results; failed/cancelled evaluation publishes nothing. Caller mutation of supplied arrays or returned values cannot change prior snapshots or subsequent evaluations.

## 4. Frozen fixture and pose inventory

Three local shapes, all z=1/8: square [(0,0),(1,0),(1,1),(0,1)]; rectangle [(0,0),(2,0),(2,1),(0,1)]; rhombus [(-8/5,-4/5),(2/5,-4/5),(8/5,4/5),(-2/5,4/5)]. Node IDs 101-104, director +Z, material direction +X. Scale all reference coordinates by lambda in {1/100,1,10}; thickness and material remain fixed as admitted. This is coordinate/response-scale coverage, not a unit-conversion claim or thickness-domain qualification.

For each scaled shape let X_i be reference points, L the maximum reference edge length, and (x_i,y_i,z_i)=X_i-mean(X). Rotations Exp(v) use the spatial exponential; the variable rotation increment eta acts on the separately supplied accepted matrix Q_a. Freeze six manufactured local poses:

| Pose | Translation u_i | Accepted Q_a,i | Trial eta_i |
| --- | --- | --- | --- |
| ZERO | (0,0,0) | I | (0,0,0) |
| MEMBRANE | (.012*x+.004*y,-.003*x+.007*y,0) | I | (0,0,0) |
| BENDING | (0,0,.009*(x*x+2*y*y+x*y)/L) | Exp(-.018*y/L,.018*x/L,0) | (0,0,0) |
| SHEAR | (0,0,.011*x-.006*y) | I | (0,0,0) |
| CHECKERBOARD | (0,0,.008*L*chi_i), chi=(1,-1,1,-1) | I | (0,0,0) |
| MIXED | .009*L*(sin(6*i+.4),sin(6*i+1+.4),sin(6*i+2+.4)) | Exp((.09,-.04,.06)+.004*i*(1,2,-1)) | .009*(sin(6*i+3+.4),sin(6*i+4+.4),sin(6*i+5+.4)) |

Index i=0..3 follows canonical physical nodes before reordering. Arrays then follow physical node identity. For tiny-response checks additionally use amplitudes 1e-6 and 1e-3 multiplying all nonzero MIXED translations, accepted rotation vectors and trial increments at lambda=1; do not apply an absolute max(1,...) comparison floor.

The ordinary station/work table is 3 shapes x3 scales x6 poses =54 records. Tiny-response table is 3x2=6 records. Count these separately.

Transport tables at lambda=1 use MIXED pose on all three shapes: all eight D4 permutations [(i+k)%4 for i in base], base=(0,1,2,3) or (0,3,2,1), k=0..3, giving24 records; physical director polarity {-1,+1} with unchanged canonical connectivity gives6 records. Reorder physical stations using independently derived natural-coordinate maps.

Common rigid motion table: W=Exp(v) for v=(0,0,0),(.4,-.3,.2),(pi,0,0),(0,1.4*pi,0), shift=(2,-3,1)*L; set x'=W x+shift, Q_a'=W Q_a, eta'=W eta while holding X fixed. Thus Exp(eta')Q_a'=W Exp(eta)Q_a and this table has12 records. Passive re-expression table: W=Exp(.31,-.22,.17), shift=(2,-3,1)*L; set X'=W X+shift, x'=W x+shift, Q_a'=W Q_a W^T and eta'=W eta, and transform material direction/director by W, giving3 records. Same-pose rebase: Q_a'=Exp(eta)Q_a and eta'=0, positions unchanged, giving3 records. Compare invariant local physical fields, energy and spatial wrench/work with the appropriate coordinate transports; compare chart derivatives through their chain-rule maps, not raw equality. These operations preserve the fixed54 and20 context inventories; none is removed for roundoff convenience.

Extract all10 Q4-bearing graph reference variants independently from the frozen fixtures and expansion rules: J_Q4_PAIR and J_MULTIFAMILY_LOOP, each BASE, SHUFFLED_INSERTION, RENUMBERED, CONNECTIVITY_REVERSED, PROPER_GLOBAL_TRANSFORM. Q4 element IDs are respectively11 and13 before renumbering; the loop reference is [(0,.5),(2,.5),(2,1.5),(0,1.5)] at z=1/8. Renumber nodes by10000+7*n, elements by20000+5*e; reverse Q4 connectivity [0,3,2,1]. Proper transform U=[[0,-1,0],[1,0,0],[0,0,1]], shift=(2,-3,1). Reordering insertion changes no physical geometry. Per actual owner source lines211-216, shell material direction is +X and becomes U*(+X) only for PROPER_GLOBAL_TRANSFORM; it is NOT graph element.orientation=+Z. Physical normal comes from shell definitions.reference_normal and its specified transform. Run ZERO and MIXED per extracted context:20 records. Compare definition/normal/frame/station provenance as well as numerical fields. These are manufactured local poses, NOT solved graph history coverage.

## 5. Named numerical tests and acceptance

Freeze this ordered numerical inventory as separate nodes (no dynamically hidden parameter subset):

1. test_affine_recovery_definition_and_source_identity
2. test_affine_recovery_zero_and_station_constitutive (54-record source/station table)
3. test_affine_recovery_independent_material_fields (same54 contexts, independent source reconstruction)
4. test_affine_recovery_64_stationarity_and_schur (all54 actual chart contexts)
5. test_affine_recovery_actual_chart_work_hessian (all54; actual unchanged kernel comparison)
6. test_affine_recovery_directional_derivatives_all_steps (MIXED, all3 shapes/scales; h=1e-4,1e-5,1e-6)
7. test_affine_recovery_six_rigid_modes_and_common_motion (3 zero-state total tangents and12 common-motion contexts)
8. test_affine_recovery_d4_and_director_transports (24 and6 separate records)
9. test_affine_recovery_passive_and_same_pose_rebase (3 and3 separate records)
10. test_affine_recovery_all_graph_q4_reference_variants (20 local records; ten exact variant identities)
11. test_affine_recovery_tiny_physical_energy_and_numerical_separation (6 tiny records plus54 channel decompositions)
12. test_affine_recovery_definition_observation_races
13. test_affine_recovery_immutable_detached_results_and_reentry
14. test_affine_recovery_unsupported_routes_and_cancellation
15. test_affine_recovery_actual_mutation_rejection

Smoke selects node1 and a separate registered test_affine_recovery_smoke_square_station_work, using ZERO/MIXED square at lambda=1. That smoke-only node is not counted as full node2 or added to the15 full numerical nodes. Complete rehearsal and both formal cycles run all15 numerical nodes in dependency order. Record evaluation tables separately rather than summing duplicate contexts into a misleading combined case count.

Independent checker reconstructs frames, original mixed source fields, constitutive law, n and analytic derivatives, 64 station saddle and physical tensor maps without importing the facade, production mechanics/recovery or cached matrices. Independently derive Procrustes first/second variations or use an independently authored analytic chart; finite differences are directional checks, not the only force/Hessian oracle. Original exact proofs are prerequisites, not replacement numerical outputs.

For all nonzero quantities use relative 1e-11 invariant/energy/work/symmetry and 1e-7 directional agreement; check finite values before contractions. Nondimensionalize using diag(L,L,L,1,1,1) per node before mixed-unit norms. Direction v_j=sin(j+1), normalized after that scaling; run every h above, including work gradient and actual chart tangent, on the nine ordinary MIXED shape/scale contexts only. Tiny-amplitude contexts have separate relative energy/work tests, not h=1e-4 checks normalized against an amplitude1e-6 signal. Zero/rigid residuals use the corresponding physical or total zero-state tangent norm and explicit unit nondimensional direction as reference scale, never a dimensionless max(1,...) floor. Compare tiny nonzero energies relative to their actual physical values. Construct the six rigid vectors analytically (three translations and three common rotations with delta_x=omega cross Xc and delta_theta=omega); evaluate their numerical null residual at relative1e-11, not literal binary64 zero. Exactly six total qualified modes is checked including unchanged numerical PL/hourglass. Do not demand exactly six nulls of the numerical-term-excluded physical core unless its source rank proves that assertion.

Negative probes in12-15 must actually intercept observation before construction/evaluation, mutate descriptor/seal/coordinates/material direction or returned data, reenter evaluate, change accepted matrices, supply nonfinite data, tamper source station order/weight/frame/M/n/resultant, omit Dn or either geometric Hessian term, leak PL/hourglass energy into material results, change coupling/inverse sign, supply historical IDs, nonaffine reference, generalized/history sections, offsets/initial fields, and trigger cancellation before family work and before final publication. Require rejection or a failed physical identity; no fake summary flags. Reuse verified baseline contexts for mutations, not repeated full solves for every corruption. Any state-safety or correctness finding blocks regardless of severity label.

Rehearsal success is prerequisite to two fresh formal cycles with byte-identical canonical scientific outputs and independent implementation/evidence review. Reuse current shared runner: at most3 workers, one numerical thread,24GiB/tree,600seconds/child,120seconds inactivity,1800seconds/wave; exclusive external output, whole-tree termination, no automatic retry or consumed authority reuse. Register one full named node per child; dispatch ordered batches of at most3 children after smoke. Within each child capture immutable source/definition data once and reuse read-only station operators across matching contexts. Never drop cases or relax thresholds to meet a limit. Bind exact execution inventory before dispatch.

Each of the15 full nodes is isolated and self-contained: no dependence on another node's process globals, cache, generated fixtures or successful execution. Every child has its own existing ProcessJob and limits; the coordinator monitors all active jobs, enforces global3 and advances a batch only after every launched tree is terminal and drained. Child assignment ID, node name, lane, frozen input graph and exact parent whole-inventory identity must agree before evaluation. Shared immutable source artifacts may be read; unverified output from another node is not input authority.

A stopped, skipped, crashed or timed-out node cannot be reported as passed or as a scientific counterexample merely because pytest emitted an assertion. An actual scientific NO_GO requires a complete typed contradiction record containing the specific failed physical predicate, compared quantities and scales, source/candidate/fixture identities, and independently verifiable payload accepted by the evidence checker. Unexpected assertion/exception, malformed evidence or process/resource failure is BLOCKED. Keep partial logs outside canonical science, enumerate actual completed node states, and never fill missing rows or manufacture an all15-passed aggregate. This distinction is implemented in the same shared runner and existing completion register, not a second administrative framework.

Terminal precedence: BLOCKED_G3C_Q4_AFFINE_RECOVERY_PROCESS_OR_EVIDENCE; NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_OR_STATE; PROVISIONAL_GO_G3C_Q4_AFFINE_LOCAL_PHYSICAL_RECOVERY_ONLY. Success enables a separately frozen successor mixed-owner integration and actual solved-graph recovery tests only. Full MO16/G3c375-history/3075-stage/3450-prefix cycles, G4/G5, unrestricted geometry/material parity and public integration remain open. Public Q4/S3 and legacy beams, coefficients, defaults, old evidence and releases remain unchanged.

## 6. Implementation extent and preserved authority

Use new private source modules for the recovery facade and its construction registry,
and new research-only independent checker, analytic-chart, fixture/test and extension-
lemma artifacts as needed. Reuse scripts/run_ge_beam3_qualification.py and its existing
inert guard tests. Bind their complete changed-path inventory at implementation freeze;
no arbitrary command or module dispatch is permitted. Existing public source files
listed above, historical fixture manifests, old gate programs, defaults, version and
package metadata remain immutable. This contract and its independently authored review
are design authority only, never numerical acceptance. Update the single completion
register after actual gate outcomes; do not replace the full parity matrix.

