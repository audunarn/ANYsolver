# Supporting source review: nonprincipal native complete slice

Scope: C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001, HEAD e166100ca171f54911b4e75e8de2985030fe5cba. Four new example/reference/test/doc files only. Source and algebra review; no solver/NumPy imports, numerical evaluation, tests, CLI, builds, product changes, Git mutations, or nested workers. Supporting OpenAI review is not different-family engineering acceptance. Status: complete supporting source review of held author V2 plus energy-partition repair. Current source hashes match author_source_checks_v2.json and the lead-provided held V2 identity. No remaining source finding identified; all numerical gates are unexecuted.

## Findings and repair status

1. Accounting partition coverage: the original `_physics` compared total energy only. The concrete counterexample stored elastic'=elastic+delta, kinetic'=kinetic-delta preserves total and escaped that assertion. Current tests/test_ge_beam3_native_nonprincipal.py:62-63 compare both partitions against independent `ref.account` with ENERGY_SCALE, and `_assert_trajectory`:183 applies 1e-6 to initial, stage and endpoint balances in both coarse and fine routes. Source finding closed; numerical execution remains unverified.
2. Full inertia coverage: the earlier mass assertion omitted translation/rotation cross blocks and the massless/algebraic extension. Current test:104-118 probes an arbitrary finite rotated pose, checks all physical mass blocks, exact cross/algebraic zeros and inertia force against M*a+gyro. Test:125 retains exact zero and 1e-6 inertia-force criteria. Source coverage finding closed.
3. Fine complete-state coverage: the earlier temporal check examined final representative position/rotation/velocity and energy only. Current test:212-217 computes `_trajectory_metrics(fine)` and invokes the same complete state, algebraic, local balance, accounting, energy and strict P/H checks as the coarse route. Source coverage finding closed.

No remaining equation/sign or concrete source defect identified within the assigned slice. This is not a test-pass claim.

## Algebra and actual production path checked

The primitive reference uses no production kernels. It retains nine translational and six spatial cell-spin physical coordinates; only massless free nodal frames and retained resultants are eliminated on the explicitly bounded branch.

For each half-cell, z=U^T*d-ell*e1, n=diag(EA,GA,GA)*z/ell and f=U*n. Elastic gradients (-f,+f) and cell torque -d cross f follow from delta(U^T*d)=-U^T*(eta cross d). With gamma=Log(U0^T U1), the stationary geodesic nodal frames U0*Exp(a*gamma), a=(-1/4,1/2,5/4), give b=(gamma/4,gamma/2) then (gamma/2,gamma/4). Inverting ell/(6*EI)*[[2,1],[1,2]] gives EI/ell*[[4,-2],[-2,4]]: endpoint retained moments vanish, central moments are 3*EI*gamma/(2*ell), and energy is 3*EI*|gamma|^2/(4*ell). All moment directions are parallel to their log axes, so the log inverse-Jacobian transpose leaves them unchanged; the free trace torques cancel exactly on this branch. Relative-axis transport U0*gamma=U1*gamma supplies the opposite physical bending torques.

`_ge_beam3_retained_generalized.py`:110-131 constructs these chord/log kinematics, residual [J^T*p, k-grad(Psi*)] and the full 42x42 saddle Hessian. The local test evaluates this actual operator and eliminates the 27 algebraic coordinates via Hpp-Hpz*Hzz^-1*Hzp. `ref.chart_gradient` uses the left exponential Jacobian transpose, matching the Hessian chart rather than comparing a raw spatial torque derivative.

The independent symmetric P1 translation mass rho*ell/6*[[2,1],[1,2]] and positive rotated rotary mass ell*U*diag(Jdensity)*U^T match the zero-lift/diagonal-inertia specialization. `_ge_beam3_centered_batched_finite_inertia.py`:76-99 yields translational force rho*a and rotary I*alpha+omega cross(I*omega) with the positive gyro sign. No algebraic frame inertia or physical mass condensation is introduced.

The public example selects `stage_coordinates='acceleration'`. `_ge_beam3_native_midpoint.py`:551-554 solves initial algebraics then physical acceleration; :587-645 gives the full native stage residual/tangent with stage position x+.5*h*v+.25*h^2*a, stage cell frame Exp(.5*h*omega+.25*h^2*alpha)*U, velocity v+.5*h*a; :708-742 gives the full endpoint exponential/linear velocity update, independently solves endpoint algebraics and recomputes endpoint acceleration. These match the independent midpoint recurrence. The public trajectory restore binds the full contract/native bytes on a fresh never-initialized owner; t_end may extend. Test:223-229 uses fresh owners for 4=2+2 and compares complete dictionaries and capsules exactly.

## Angular impulse and temporal accuracy distinction

Let wm=(w0+w1)/2, am=(w1-w0)/h, A=skew(wm), C=Exp(h*A/2), Im=Um*J*Um^T. The declared update gives I0=C^T*Im*C, I1=C*Im*C^T. Since C*wm=wm,

Delta Hspin = h*sinc(h*|wm|/2)*(wm cross(Im*wm)) + h*Iavg*am,
Iavg=(C*Im*C^T+C^T*Im*C)/2.

Subtracting the linear stage impulse h*(Im*am+wm cross(Im*wm)) gives
D=h*((sinc-1)*(wm cross(Im*wm))+(Iavg-Im)*am)
 = h^3*(-|wm|^2*(wm cross(Im*wm))/24 + [A,[A,Im]]*am/8)+O(h^5).

Symmetric consistent translation mass gives exact orbital endpoint impulse h*sum(xm cross(M*am)). Thus `ref.discrete_angular_increment` is the exact ideal-SO3 endpoint increment of this method, and does not certify conservation. The test records exact increment, linear stage impulse, method defect, cumulative values and endpoint mismatch separately. Strict endpoint H=1e-6 remains asserted at test:189, independently of exact-impulse compatibility. Any observed failure must remain FAIL; a successful same-method comparison cannot regrade it.

The independent unprojected RK4 reference uses all 15 physical coordinates plus full rotation matrices, no production kernels and no projection. Its 64/128-subdivision convergence and orthogonality checks remain numerical validity evidence, not a rigorous continuous-time enclosure. Common-time coarse/fine comparison uses position/L, SO3 angle/(1 rad), nodal velocity/(L*sqrt29), cell omega/sqrt29. Exact midpoint correspondence and temporal representative response <=2% are separate assertions; energy drift <=1%, tangent <=1e-5, local equilibrium/accounting/state <=1e-6 remain unchanged.

## Remaining limits

No numerical allowance was used or inferred. Actual SO3 branch admissibility, root convergence, finite-angle/noncommutation excitation, strict P/H, reference convergence, 2% response, 1% energy improvement and complete restart equality remain unexecuted. No engineering acceptance, C7 qualification, release/default change, performance/cost or runtime claim is supported by this review.

## Final reviewed identity

Author evidence: C:/ANYworkspaceWork/contact_native_nonprincipal_20261006/author_source_checks_v2.json; immutable author snapshot: source_snapshots_v2. Current source hashes independently read after author completion and matched:

- examples/native_nonprincipal_reference.py: 6cd821b3ccc49aa73892b9704e541627511fc25b5c4f9f8fe4688ad96ffb8bfb
- examples/native_nonprincipal_dev.py: 93fc94c55c507b0247910d8719d15d48083263e61246d3d560fb29983f4cd480
- tests/test_ge_beam3_native_nonprincipal.py: de62e248a354b697222d6642a6544ce5363fdf5cf5d9ea40fa0e1b53976b4e1f
- docs/GENERAL_CONTACT_NATIVE_NONPRINCIPAL_DEV.md: 86fe48f0ecace27aae636933b362fb68b2e2de6e90dae969cd8875fe9b654b41

Machine-readable supporting identity: supporting_source_review_v2_identity.json. Author metadata records source-only AST/whitespace/EOF checks; this reviewer performed source/algebra inspection and hash reads, not those parses or any execution. The held example additionally admits only steps 0..8, dt in {1/64,1/128}, and horizon steps*dt<=4/64; unsupported timestep/horizon choices are rejected. No numerical or scientific pass is inferred from source checks.
