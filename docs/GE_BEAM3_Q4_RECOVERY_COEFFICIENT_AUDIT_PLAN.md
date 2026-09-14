# Q4 retained-space audit: successor preregistration

Implementation base: 22289a62fda9bb09def91c21b297b2cf06533a19.
Boundary: private integration only; public operators and old identities unchanged.
The separately authored draft below is adopted as the proposed equation/test
contract. Independent contract acceptance is required before implementation.
Implementation freeze and independent execution review are required before runs.
This plan does not authorize qualification claims from drafting or smoke results.
Source hashes in the draft bind unchanged inherited files, not the draft's old HEAD.
Full G3c, G4/G5 and all applicable parity rows remain mandatory.

---

# Q4 retained-space finite-recovery coefficient audit

Status: INDEPENDENTLY_AUTHORED_DRAFT_NOT_FROZEN_AUTHORITY.
Author: /root/q4_recovery_feasibility. No mechanics or qualification runs were performed in preparing this draft. This artifact is outside the frozen execution worktree. It is not an independent acceptance review of a future implementation.

## 1. Authority and narrow question

Subject commit: 62133e084b5c7ff14424559462b0fe1911cd79f9.
Subject tree: 5b08a2740cc9db6a06762cfc837b21564b482e66.

Question: Does the natural nonlinear compatibility extension of the existing 35-coordinate mixed stationary functional, retaining its physical material law and field spaces, reproduce the existing private Q4 finite physical potential exactly on the two frozen fixtures?

This audit does not test arbitrary possible representations. A negative result must not be reported as universal impossibility of unchanged-potential recovery.

Bind these UTF-8, CRLF-to-LF-normalized source inputs:

| Path | LF bytes | SHA-256 |
| --- | ---: | --- |
| src/anysolver/e4_pl_element.py | 293258 | 7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38 |
| src/anysolver/elements.py | 244692 | f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37 |
| src/anysolver/_ge_beam3_g3c_local_shell.py | 19430 | 69d9f27a96ed7e9a5959a42a081eeafbbe72021de6e4da1f91355c5fb3850f10 |
| docs/GE_BEAM3_G3C_MATRIX_SHELL_CONTRACT.md | 9625 | 59a09dc7db6256a145520ae7b4f2d325dee1abca5d5b5c381a7ada57a2ad92fd |
| docs/GE_BEAM3_G3C_MO16_SOURCE_ASSESSMENT.md | 7666 | e6b702fba5c32ef22537a137fc150fa54b63028c6910df96c5c5f0c6a722026e |

Source anchors: e4_pl_element.py _stationary_blocks at 2159 onward, _recover_planar_mixed_fields at 5962 onward, qualified finite correction at 5641-5776; elements.py source nonlinear membrane operators; _ge_beam3_g3c_local_shell.py q4_channels. Line references supplement, not replace, complete file hashes.

Freeze the audit/checker source and arithmetic environment separately before execution. Neither executable may import production mechanics or former mechanics-oracle modules.

## 2. Exact fixtures and coordinates

Use two new diagnostic fixture IDs, not historical Q1 geometry IDs:

1. MO16_SQUARE_EXACT: nodes (-1,-1,0), (1,-1,0), (1,1,0), (-1,1,0).
2. MO16_AFFINE_RHOMBUS_EXACT: nodes (-8/5,-4/5,0), (2/5,-4/5,0), (8/5,4/5,0), (-2/5,4/5,0).

Both use physical director (0,0,1), homogeneous isotropic virgin elasticity, E=1, nu=1/4, thickness=1/10, no offsets, initial fields, section history or material coupling. Use the actual source isotropic membrane, bending and shear section blocks, including its 5/6 shear factor.

Use the actual ordered four-point source quadrature, each coordinate +/-1/sqrt(3) and unit natural weight. Do not replace inherited and Equation-7 frames by a shared guessed frame.

Independent reconstruction must derive Equation-7 and inherited centre frames, global-to-local DOF transformations, natural shape derivatives and physical Jacobians, engineering-strain tensor transformation between frames, actual stress/strain/compatible basis functions, positive quadrature Jacobians and frame orthogonality/orientation.

Set the 24 independent formal variables to source-centre-frame nodal components, ordered [u,v,w,rx,ry,rz] per node. This is an invertible parameterization of all local displacement vectors; do not restrict rotations or transverse patterns in the coefficient inventory.

## 3. Stationary representation and complete inventory

Independently assemble the actual source matrices:

    H = [[0,F^T],[F,E_s]]
    F = -sum_g w_g N_epsilon,g^T N_sigma,g
    E_s = sum_g w_g N_epsilon,g^T C N_epsilon,g

Let b0(d)=Cq^T d, with all required coordinate transformations included.

At each inherited membrane station construct:

    e = Bm*y
    p = Gw*y
    n = [p_x^2/2, p_y^2/2, p_x*p_y]

Transport n as an engineering-strain tensor into the mixed frame, embed it in the first three generalized-strain rows, then define:

    j(d) = [sum_g w_g N_sigma,g^T n_mixed,g(d); 0_21]

The candidate stationary functional and its condensed physical potential are:

    Pi(d,z) = z^T H z/2 + z^T [b0(d)+j(d)]
    z*(d) = -H^-1 [b0(d)+j(d)]
    U*(d) = -[b0(d)+j(d)]^T H^-1 [b0(d)+j(d)]/2

Compute exact solutions of the required linear systems, not a floating-point inverse. Verify their original-system residuals exactly.

Freeze these difference polynomials:

    D3 = -b0^T H^-1 j - sum_g w_g e_g^T A n_g
    D4 = -j^T H^-1 j/2 - sum_g w_g n_g^T A n_g/2

For each fixture, emit all 2600 degree-three monomial coefficients and all 17550 degree-four monomial coefficients in 24 variables. Total: 40300 ordered coefficients across both fixtures.

Ordering: fixture order above, then degree three before four, then lexicographically ordered nondecreasing variable-index tuples. Retain explicit zero coefficients in canonical evidence or a canonical index-complete zero representation whose expansion is checked independently.

Sparse computation is permitted: it should discover only membrane/transverse sectors after exact block separation. It must nevertheless account for every coefficient, including absence of rotation, drilling and other sectors. Do not assume those zeros without checking reconstructed matrices.

Also verify the degree-two identity Kphysical=-Cq H^-1 Cq^T against an independently reconstructed stationary condensation. This is source-algebra consistency, not an independent qualification of the public baseline.

The associated recovery fields are epsilon=N_epsilon*alpha*, s=N_sigma*beta*. Their source constitutive condition is weak stationarity F*beta+E_s*alpha=0. Do not claim pointwise s=C*epsilon unless separately established for the selected spaces. Physical force is b_,d^T*z* and tangent is -b_,d^T H^-1 b_,d + sum_i z*_i*b_i,dd, with b=b0+j. These explain the candidate but do not create accepted recovery evidence.

## 4. Independent reconstruction, guards and outputs

Use exact algebraic arithmetic only. These fixtures permit a small multiquadratic field; a suitable field is Q(sqrt(2),sqrt(3),sqrt(5)) with positive real embeddings. Verify every normalization radicand and frame identity rather than silently extending the field or approximating it.

Producer and checker implement their own assembly paths. Producer may use compact sparse polynomial coefficient algebra. Checker independently reconstructs source equations and verifies coefficients using exact field arithmetic. Do not share an assembled H, basis matrices, coefficient-generation routine or cached mechanics. Shared canonical I/O and resource harness are permissible. No float, evalf, tolerance-based zero, generic simplify, numerical frame differentiation or fitted station fields.

Mutation tests must detect a changed frame map, engineering shear factor, quadrature weight, stationary coupling sign, nonlinear compatibility coefficient, reported zero/nonzero coefficient and bound hash.

Every run retains the existing limits: 600 seconds/child, 24 GiB/process tree, one numerical thread, at most three workers, 120-second inactivity watchdog, 1800-second wave, exclusive outputs and no automatic retry.

Run both fixtures even if the first supplies a contradiction. Preserve all completed coefficient tables. Two independent checker executions must agree byte-for-byte on scientific content. Timing/process logs remain separate.

The canonical result binds source/environment/executable identities, fixture definitions, complete coefficient-table hashes, zero/nonzero counts and the first nonzero coefficient in frozen order. A nonzero witness includes its monomial, exact algebraic coefficient and both contributing sides.

## 5. Numerical separation and decision limits

PL and hourglass are excluded from both physical polynomials, remain unchanged, and must be separately identified. They cannot absorb a failed coefficient. Their zero contribution to D3,D4 follows from their unchanged quadratic form; no numerical energy may be relabeled as physical material energy.

Terminals, in precedence order:

1. BLOCKED_G3C_Q4_RETAINED_SPACE_COEFFICIENT_AUDIT: source, process, arithmetic, inventory, mutation or checker failure.
2. NO_GO_G3C_Q4_NATURAL_RETAINED_SPACE_FINITE_IDENTITY: at least one independently verified exact nonzero coefficient.
3. UNCLASSIFIED_G3C_Q4_TWO_FIXTURE_COEFFICIENT_IDENTITIES: every registered coefficient is exactly zero.

A NO-GO establishes that this explicitly defined nonlinear stationary extension differs from the retained finite potential for at least one admissible fixture. It supports preregistration of the approved private Q4 successor, but does not qualify that successor or prove every alternative representation impossible.

An all-zero result establishes only the two finite fixture identities. It does not establish arbitrary geometry, physical recovery acceptance, full G3c, history-bearing parity, or public Q4 changes. The next gate would be geometry-general derivation plus finite recovery/work/tangent validation under separate reviewed authority.

Public legacy beam, qualified Q4/S3 mechanics, aliases/defaults, prior qualification records and all raw evidence remain immutable under this draft.
