# Submodel transfer contract

Status: contract proposed in C0 (2026-10-09) and implemented in slice S1 on branch
`claude/submodel-s1` (`src/anysolver/submodel_transfer.py`, `tests/test_submodel_transfer.py`).
This document states the current rules; section 11 records how they changed.
Plan and evidence: `C:/Github/ANYfem/docs/handoff/submodelling-20261009/` (PLAN.md, s0/, c0/, s1s3/).

ANYsolver owns the mechanics of sequential displacement-driven shell submodelling: the
interpolation of a source solution, the constraint-reduced driven trace, the drilling and
junction rotation rules, interface forces and reactions, and the error allowance. ANYmesher
supplies point correspondence, ANYgeometry the cut, ANYfem the workflow and source admission.

## 1. Admission

- **Source result**: the caller (ANYfem) admits a converged, certified linear static solve
  with a complete six-component nodal vector. Modal, buckling, nonlinear and transient
  results need their own contracts. ANYsolver's entry points validate shapes, finiteness,
  element types and control parameters.
- **Shells, v1**: `QualifiedE4PLShellElement` (Q4) and `NativeParityE4PLS3V2DShellElement`
  (S3 V2D), linear order, by an explicit allow-list of exact classes, for sources and for
  every shell of a target model. The `element_capabilities` registry records only gaps, so
  it would admit unknown elements; the allow-list fails closed. Beams and constraint-only
  elements in a target are retained as they are.
- **Controls**: every tolerance and threshold must be finite and in range; computed
  tolerances and allowances are checked for finiteness before any acceptance comparison.

## 2. Interpolation (`interpolate_nodal_field`)

- Weights come from the source element's own functions: `compute_shape_functions` for the
  E4-PL Q4 (bilinear in `(ξ, η)`), `compute_native_surface_shape_functions` for the S3 V2D
  (`(1 − r − s, r, s)`; it forbids the legacy dispatch). Correspondence weights, if given,
  must agree with them (`TRANSFER_CONVENTION_MISMATCH`).
- Transport rule: `u(x_f) = u(x_p) + θ(x_p) × (x_f − x_p)`, `θ(x_f) = θ(x_p)`, with `x_p` the
  element map at the hit. Rigid motion is reproduced exactly.
- Alternative conforming hits supplied by the correspondence owner are evaluated too.
- This is nodal-field interpolation, not formulation-native physical recovery.

## 3. Interpolation allowance (`interpolation_allowance`)

Per component, the sum of:

- evaluation roundoff `(n_e + 1) ε max|u_i|` and propagated source allowance `Σ|N_i| δu_i`;
- position uncertainty `ρ' = ρ + 4ε max|x|` (inverse residual plus coordinate roundoff)
  propagated through the whole transport expression: `ρ' ‖∇u‖` per component, plus, for
  translations, `ρ' ‖∇θ‖ |offset|` and `ρ' ‖θ‖`. Gradients are physical, from the
  shape-function derivatives through the element Jacobian, maximum over the hit and corners;
- for each alternative hit, its value difference from the selected value plus its own
  propagated uncertainty (component-wise maximum over alternatives);
- through the transport rule, the rotation allowance times `|offset|` plus roundoff.

## 4. Driven trace (`build_driven_trace`, `apply_driven_trace`, `update_driven_trace_values`)

Constraint slaves are never prescribed directly: prescribing an element-provided coupling
slave refuses in the solver (`CONSTRAINT002`), and the trace is always emitted as reduced rows.

1. The target model carries its retained supports and internal constraints, not the trace.
   Its retained constraint map `u = T q + c` is taken from `build_constraint_transformation`.
2. One row `b` with value `g` per driven quantity: unit rows per global DOF under
   `drive_all` (P2); translations plus the junction rotation rows of section 5 under
   `release_normal_rotation` (P1). The policy is a required argument; there is no default.
3. Each row is reduced, `a = b T`, `h = g − b c`, and equilibrated by `max|a|`.
4. Rows are eliminated in deterministic order (node, then component). Every entry carries
   the accumulated magnitude of its operands; it is zero only below `16 ε` times that
   magnitude. A row that vanishes is **redundant** if its remaining value lies within its
   combination tolerance `Σ|combo_i| δh_i + 16 ε max(Σ|combo|, 1) Σ|combo_i h_i|`, where
   `δh_i` is the row's uncertainty (transfer allowance plus `4ε(|g| + Σ|b||c|)`); otherwise
   it is **inconsistent** and refuses. A surviving equilibrated row smaller than `1e-8`
   refuses as a numerically ambiguous rank decision.
5. Kept rows are emitted: single-term rows as prescribed values, others as
   `ConstraintEquation`s with their pivot as dependent. An emitted coefficient at or below
   the audit threshold `COEFFICIENT_ATOL` refuses (`TRACE_AUDIT_PRUNING`). After application
   the constraint map the solver builds is checked to enforce every trace row within its
   tolerance; otherwise the trace is rolled back and refuses (`TRACE_AUDIT_CHANGED`).
6. Binding: a trace records its model and a fingerprint of the physical retained rows
   (supports, equations, coupling records) and of the topology, geometry and activity
   revisions. Application, update and force recovery refuse another model or a changed
   retained set, and check that the trace's own supports and equations are unchanged.
7. Updates change values only, validated and computed before committing (a refused update
   leaves everything unchanged), by direct object edits without a revision bump. The session
   then refreshes the prescribed offset without refactorizing.

Carried supports touching the cut are retained: their trace rows are redundant when
consistent, and an inconsistent one refuses. The solver's own constraint map drops chained
coupling coefficients at or below `COEFFICIENT_ATOL`; the trace is exact relative to that map.

## 5. Rotations: drilling policy and junction rule

- P2 drives all three rotations. P1 drives, per incident source face with unit normal `n_j`,
  the two in-plane components `t_jk · θ`. With singular values `σ1 ≥ σ2 ≥ σ3` of all `t_jk`:
  `σ3/σ1 ≥ 1e-3` drives all three rotations; `σ3/σ1 ≤ 1e-9` releases the shared normal; in
  between refuses. Thresholds must satisfy `0 < rank2 < rank3 ≤ 1`.
- The default is not chosen in the solver. The D3 decision experiment (PLAN.md) remains open;
  S0 and S1 evidence: both policies are exact on representable fields, P2 reproduces the
  element-aligned restriction exactly, P1 changes a coupled field by about 2.5e-4 relative in
  rotation.

## 6. Interface forces and reactions (`interface_forces`)

- All multipliers come from `K u − f = Cᵀ μ` over the physical constraint rows: retained
  supports, model equations as written, element coupling records (`slave − Σ masters`) and the
  kept trace rows. Supports are unit rows, so their reactions follow as remainders on the
  supported DOFs; the other multipliers are solved per connected component of rows sharing
  unsupported DOFs, with column equilibration and a rank check. A constraint acting only on
  supported DOFs refuses.
- A retained equation or coupling is **internal** when every rigid-body motion satisfies it;
  its reaction is then self-equilibrated and not reported. Otherwise it is an **external
  restraint**, and its force `Cᵀ μ` is reported with the support reactions.
- Interface force: `Σ λ_k b_k` over the kept trace rows, the force the removed structure
  exerts on the submodel, global frame.
- Acceptance: `u` satisfies the current constraints component-wise; without a supplied
  allowance, `u` must be certified (scaled backward error ≤ `1e-10`, not inconclusive),
  otherwise `FORCE_UNCERTIFIED`; every trace row holds within its tolerance (kept rows their
  own uncertainty, redundant rows their combination tolerance); the residual not carried by
  any constraint lies within the force allowance (`FORCE_EQUILIBRIUM`).
- Free body: interface forces plus retained external reactions plus applied loads vanish.
- Resultants about a point: `interface_resultant`. Per-face and corner grouping belongs to
  ANYfem; corner nodes shared by two cut faces are separate records, never split.
- Physical and numerical (stabilisation) parts are not yet partitioned (`partitioned=False`).
- `compute_reactions` is not this quantity.

## 7. Error allowance (`estimate_static_error_allowance`, `force_allowance`)

A first-order estimated allowance, not a rigorous bound, on the operator the solver
factorizes: `K̃ = S K_red S` from `static_operator_plan()`, `y = S⁻¹ q`.

- `η̃ = ‖K̃y − S F_red‖∞ / (‖K̃‖∞‖y‖∞ + ‖S F_red‖∞)`; `κ̃ = ‖K̃‖ · est‖K̃⁻¹‖₁` through the
  solver's factorization handle; symmetry of `K̃` is asserted.
- `δq_i = S_i κ̃ η̃ ‖y‖∞`, `δu = |T| δq` plus the accepted component-wise reconstruction
  discrepancy. A model with no independent DOF has only that discrepancy, and `u` must
  satisfy its prescriptions component-wise (`ALLOWANCE_RECONSTRUCTION`).
- Inconclusive when `κ̃ η̃` exceeds the threshold (default `1e-6`).
- Forces: `Σ_j |K_dj| δu_j + γ_n (|K||u|)_d + ε|f_d|`, `γ_n = nε/(1 − nε)`.

## 8. Many cases

The structure (`B`, `T`) is fixed per submodel; only values change per source case
(`update_driven_trace_values`). Tests assert one stiffness build and one operator build
across a values-only update. ANYfem's compression guard (`solve/run.py` `_compressible`) must
see the trace as a nonzero affine offset (slice S4a).

## 9. Test specification and evidence

`tests/test_submodel_transfer.py` covers the C0 specification (slave on the cut with a cut
and an interior master; coupled beam node on the cut; redundant and inconsistent equations),
representable fields through the solve for Q4 and S3 under both policies, values-only
reuse, zero-load forces, and every review counterexample (scaled rows, support coupled
through a coupling, thin triangles, alternative hits, binding, redundant semantics,
perturbed prescribed input, unadmitted targets, invalid controls, restraints as equations,
constant-rotation transport, audit pruning, rescaled equations). The cross-repository A1
check is `handoff/submodelling-20261009/s1s3/integration_a1.py`.

## 10. Open for owner review

- Adopt the junction, rank, inconclusive and certification thresholds.
- The stiffness partition into physical and numerical forces for E4-PL Q4 and S3 V2D.
- The D3 drilling decision experiment.

## 11. History

- C0 (2026-10-09): first contract; capability-based admission, plain backward-error allowance.
- S1 review round 1 (GPT-6-Astra via Codex): no pruning, propagated tolerances, fail-closed
  validation, model binding, enforced equilibrium, factorization-based allowance, required
  policy.
- Round 2: equilibrated elimination with per-entry magnitudes, physical-row multipliers,
  Jacobian gradients, alternative hits, post-application binding, consistent redundancy
  semantics, element-map `x_p`, target shell admission, control validation.
- Round 3: rigid-mode classification of retained equations, equilibrated multiplier columns,
  full transport propagation, alternatives' own uncertainty, audit-pruning refusal and
  post-application verification, threshold ordering, this consolidation.
