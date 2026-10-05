# D2 finite-penalty conditioning under fixed geometry

30 September 2026. **Development derivation, independently reviewable; no new numerical execution, qualification or release.** Source inspected at worktree HEAD `23e845e131a8ea0c3457d10d9355ecdd5d1dd28e`.

## Result and assumptions

For the selected zero-multiplier finite law, arbitrarily small **positive** cut support does not introduce an inverse-support stiffness blow-up in the fixed-geometry primal normal problem. The contact term is positive semidefinite and bounded above by the physical relative-normal displacement norm. Structural stiffness must independently be positive definite on the imposed constraint space. This is an upper bound, not a pressure-work inf-sup theorem or a physical-gap accuracy guarantee.

Freeze the represented contact domain Ω, projection/matching, normals, skin work maps and constraints. Use a positive reference surface measure dμ. On Ω let the fine P1/Q1 source hats satisfy

\[
N_i\geq0,\qquad \sum_iN_i=1,\qquad S_i=\int_\Omega N_i\,d\mu>0.
\]

Retain every such row, including tiny cuts and hats attached to prescribed nodes. Let d(x) be a square-integrable **physical both-body relative normal variation** on the frozen matching, and define

\[
J_i(d)=\int_\Omega N_i d\,d\mu.
\]

Exact integrals are assumed. Positive quadrature preserving the stated partition identities has the analogous discrete inequality. Signed hats, inconsistent measures, negative quadrature weights or a moving projection do not inherit this result automatically. In the flat guided normal-coordinate case, d=Ns·δqs−Nt·δqt; both trace bases are nonnegative partitions of unity on the same matching. Reference skins and offsets belong to that physical trace definition.

## Bound and dimensions

Weighted Cauchy–Schwarz, equivalently Jensen for the probability measure Ni dμ/Si, gives

\[
\frac{J_i(d)^2}{S_i}\leq\int_\Omega N_i d^2\,d\mu,
\qquad
0\leq k\sum_{i\in A}\frac{J_i(d)^2}{S_i}
\leq k\int_\Omega d^2\,d\mu .
\]

The last step uses 0≤Σi∈A Ni≤1 for any active subset A. S has units m², d has units m, J has units m³, and k has units Pa/m=N/m³. Thus kJ²/S has units N·m, the stiffness quadratic form/second variation of energy. This bound contains no minimum positive support in its denominator.

For the frozen relative gap h(x)=c(x)+d(x), the law is gi=∫Ni h/Si and pi=k[−gi]+. Convexity of [−h]+² also gives

\[
\sum_i S_i p_i^2\leq k^2\int_\Omega[-h]_+^2\,d\mu.
\]

If ph=ΣNi pi, partition unity implies ∫ph²≤ΣSi pi². These are support-weighted/L² bounds, not bounds on an unweighted pressure coefficient vector. With uniformly bounded pointwise h, each pi≤k‖[−h]+‖∞ and its resultant Si pi vanishes as Si→0. Without an L∞ assumption an individual coefficient can grow on a shrinking support while the weighted norm stays bounded. S=0 is outside the division formula; this argument supplies no permission to remove a positive row or impose a support floor.

## Both bodies, constraints and conditioning

With source mass Mij=∫Ni Ns,j and cross mass Hia=∫Ni Nt,a, set G=[M,−H]. Then J=Gδq, and generalized contact internal force is −Gᵀp. Physical source/target normal nodal forces have signs +Mᵀp/−Hᵀp. Both blocks are necessary for force and moment reproduction.

For fixed geometry, an active finite-penalty branch has tangent

\[
A=K+kG_A^T\operatorname{diag}(1/S_A)G_A.
\]

If K is symmetric positive definite on the constrained variables, A is symmetric positive definite and λmin(A)≥λmin(K). No full pressure-row rank or pressure inf-sup lower bound is needed for this statement. For δq=Cδz, use \(K_C=C^TKC\) and \(G_C=GC\), retaining **all** positive pressure rows while reducing displacement columns. A shared unconstrained rigid motion can have d=0; contact cannot make a semidefinite structural K positive definite by this argument.

In the stated scalar nodal normal coordinates, each M row and H row is nonnegative and sums to Si. Consequently ‖Gi‖₂²≤2Si², so an individual contact row has spectral norm at most 2kSi and tends to zero with its support. Summing gives

\[
\lambda_{\max}(A)\leq\lambda_{\max}(K)+2k\mu(\Omega),\qquad
\operatorname{cond}_2(A)\leq
\frac{\lambda_{\max}(K)+2k\mu(\Omega)}{\lambda_{\min}(K)}.
\]

This coordinate bound assumes free coordinates select nodal normal displacements measured in m. For a general constraint transform C, its contact upper bound acquires a factor ‖C‖₂². It is not a condition estimate for a mixed translation/rotation matrix with arbitrary scaling. In structural energy coordinates the cleaner statement is

\[
\operatorname{cond}_2(K^{-1/2}AK^{-1/2})\leq1+kC_T,
\quad C_T=\sup_{v\ne0}\frac{\int_\Omega d_v^2\,d\mu}{v^TKv}.
\]

A fixed finite SPD problem has finite CT. Uniformity over a mesh/geometry/constraint family additionally requires structural coercivity and a uniform physical trace bound. Neither is proved here. Increasing k can increase stiffness contrast; mesh changes, small structural eigenvalues and floating-point evaluation of W/S remain separate conditioning issues.

## Why the exact moving tangent is outside this theorem

The actual selected work uses Si>0, gi=Wi/Si, Bi=DWi−gi DSi and R=−Σpi Bi, with pi=k[−gi]+ and read-only zero algorithmic multipliers. On a smooth active branch Dgi=Bi/Si. Writing gradients as rows, its exact contact tangent is

\[
DR=k\sum_{i\in A}\frac{B_i^TB_i}{S_i}
-\sum_{i\in A}p_i(HW_i-g_iHS_i)
+\sum_{i\in A}\frac{p_i}{S_i}(DS_i)^TB_i.
\]

The final term is generally nonsymmetric; the geometric Hessian term need not be positive semidefinite. Moving overlap, matching, normals and physical skin variations enter these terms. The Jensen proof applies to Bδq=J(d) only under the frozen trace assumptions above; it does not bound arbitrary moving-cut derivatives or establish nonlinear stability. At fixed-geometry activation, generalized derivative weights in [0,1] preserve the PSD contact term. Geometric branch changes still require their actual admission and derivative checks.

For a pure cut motion at constant physical gap, W=gS gives DW−gDS=0 in that direction. With a constant negative gap, support-weighted storage changes when overlap area changes. The production projected work therefore cannot be replaced by differentiation of moving-overlap stored energy.

## Retained contrary evidence and disposition

The [D1 two-body cut-front counterexample](d1_cut_front_two_hat_counterexample_20260929.md) retains a signed pressure direction with discrete work O(θ³) and an admissible physical witness of order θ², despite coercive constrained structure. That defeats the recorded cut-uniform **independent pressure-work** lower bound. It remains a valid historical finding. Its strictly positive multiplier baseline at touching is not a zero-multiplier finite-penalty state: this selected law gives p=0 at g=0. Eliminating pressure through the finite constitutive law changes the mathematical question; the upper bound above does not repair or requalify the exact-constraint formulation, or prove accurate pressure recovery.

Retained independent fixed-geometry development results also prevent confusing conditioning with gap accuracy:

| Fixture | k (Pa/m) | Normal tangent condition | Minimum represented gap |
|---|---:|---:|---:|
| Coarse two-Q4 cut | 10⁶ | 20.462 | −31.174 µm |
| Same coarse cut | 10⁷ | 189.868 | −26.783 µm |
| Declared 4×2 refinement | 10⁷ | 28.229 | −62.713 µm |

Sources: [coarse reference](d2_fixed_geometry_penalty_reference_v1_20260930.json), [spatial prediction](d2_fixed_geometry_penalty_spatial_v1_20260930.json). The refinement changes structural stiffness and contact representation together. Its improved matrix condition with a worse represented gap is consistent with this upper-bound theorem. Neither monotone spatial improvement nor continuum failure follows from that single comparison. Weak nodal averages and finite penetration pi/k do not bound the pointwise physical minimum; represented-gap checks remain necessary.

**Discriminator:** assess constrained structural coercivity and the frozen physical normal quadratic form separately from the actual moving nonsymmetric tangent, residual convergence, geometry admission and physical gap/response. Support vanishing alone supplies no reason to remove hats, change the pressure basis or infer a finite-law primal singularity. This derivation makes no prediction of success for the concurrently owned radial continuum run.

### Inspected identities

No numerical checks were rerun. SHA256:

- `src/anysolver/general_contact/s3_patch_augmented.py`: `0b2f64f0192e72edf374e2d7d9bd5a112936f42e8861a4d884fdfaf3bae20375` — pressure projection and Jet2 projected residual/tangent.
- `src/anysolver/general_contact/s3_patch_static.py`: `8cc9776eb5d382e7e3090c51f8bba0b8c4937cadb0af8877648ad63b0ae9b99b` — selected finite-law wrapper and zero read-only multipliers.
- Historical counterexample note: `900821762892d67e7934efbe33dee8dce162bfbe1e40a607223c7de852053890`.
- Coarse reference raw JSON: `0f49ba4f9b576bc8d98698c943c812172d4e4dae516cbe306ac8639967487aae`.
- Spatial prediction raw JSON: `c88b8fdba8a31299166abd6bb98d79a76cd5f6eb54537407eae4fb43ecbe8472`.
