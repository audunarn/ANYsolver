# S3 minimum-angle extension — living technical note

Status: **20° and 15° each `RESTRICTED_CANDIDATE`; full default parity
`NOT_QUALIFIED`; no solver change** (decision record in §8).
Plan: *ANYsolver S3 minimum-angle extension — parallel-development and
qualification plan* (27 September 2026). Branch:
`claude/wizardly-ramanujan-pk88wc`.

This note records the live call path, the geometry envelope investigated, the
evidence gathered, and the decisions taken. Evidence produced by
`scripts/qualify_s3_angles.py` lives under `reports/s3_angles/`.

## 1. Basis (G0)

| Item | Value |
| --- | --- |
| Base commit | `be41a77a62e1cd7e1767bda6e955253af0819f91` (`main`, merge of PR #58, release 0.4.7) |
| Python / platform | CPython 3.11.15, Linux x86-64 (cloud container, 4 vCPU) |
| numpy / scipy / numba | 2.4.6 / 1.17.1 / 0.67.0 |
| Sibling packages | ANYmaterial 0.2.0, ANYmesher 0.5.0, ANYfileio 0.3.2, ANYgeometry 0.4.3 (PyPI wheels in a private venv; no editable sibling checkouts) |
| Thread settings | library defaults (no `OMP/OPENBLAS/MKL_NUM_THREADS` set) |

## 2. Live call-path map

**Finding: the current-policy S3 route does not enforce any angle floor.**

| Route | Class reached | Geometry admission actually applied |
| --- | --- | --- |
| `create_shell_element(..., 3 nodes)` with `formulation=None`, `"default"`, `"e4-pl-s3"`, `"qualified-s3"`, `"e4-pl-s3-v2d"` | `NativeParityE4PLS3V2DShellElement` (`FORMULATION_ID = CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1`) | `_geometry()` in `e4_pl_s3_v2d_element.py`: non-degenerate area (`2A > 64 eps l_max^2`), reference normal facet-normal and compatible. **No minimum/maximum angle, edge-ratio, Jacobian or normalized-area check.** |
| `create_element("TRIA3"/"e4-pl-s3-v2d"...)`, `mesh_gen._install_shells` (generated panels), `runtime` local-patch transition | same V2D element via `create_shell_element` | same as above |
| `shell_element_from_dict` with V2D `formulation_id` | V2D | same as above |
| Direct `QualifiedE4PLS3ShellElement(...)` or deserialization of `E4_PL_QUALIFIED_S3_COMPANION_V1` | historical MITC3+-class S3 | `require_qualified_s3_quality` (`e4_pl_s3_state.py`): min angle ≥ 30°, max ≤ 150°, edge ratio ≤ 4, scaled Jacobian ≥ 0.20, normalized area ≥ 0.60. Bound into `formulation_fingerprint_payload()["geometry_admission"]`. |
| SESAM/ANYfileio neutral import | `legacy-s3` (explicit) | none (legacy) |
| ANYmesher `s3_quality.DEFAULT_S3_QUALITY_POLICY` | not called by ANYsolver | 30°/150°/4.0/0.20/0.60 (mesher-side, used by ANYmesher's own S3 production/repair) |
| `runtime` local-patch mesh sizing (`local_patch_s3_quality_min_axial_div`) | mesher target | refines cylinder patches so transition triangles stay ≥ 30°; `tests/test_local_patch_transition.py` asserts it |

Reproducer (`tests/test_s3_angle_element.py::test_public_s3_route_is_v2d_and_admits_reduced_angles`):
every public selector returns V2D and builds stiffness for 20° and 15°
triangles; `...::test_historical_qualified_s3_guard_is_unchanged` shows the
historical element still rejects them with
`minimum angle is below 30 degrees`.

Consequences:

* The `e4-pl-s3` → V2D alias means the 30° constant in `e4_pl_s3_state.py`
  governs only the historical formulation. Changing it would *not* extend the
  current default, and would alter a formulation fingerprint that old
  checkpoints are bound to. **It is deliberately left unchanged.**
* V2D's state/serialization identity (`e4_pl_s3_v2d_state.py`,
  `SERIALIZATION_POLICY_ID`) contains **no geometry-admission field**, so
  no checkpoint, cache key or fingerprint depends on an angle envelope.
* The remaining work is therefore **qualification**, not a solver admission
  change (plan G0 exit rule: "do not manufacture a solver change"). The
  upstream admission mismatch is the 30° *mesher* target (ANYmesher policy
  and the runtime local-patch sizing), which is a mesh-quality preference and
  is kept separate from the solver's admissible envelope (plan §2).
* Because V2D admits *every* non-degenerate triangle, "rejection below the
  qualified envelope" (plan §11) does not exist today for any angle,
  including below 30°. Adding it would be a new fail-closed production
  restriction on the default formulation (possibly breaking existing models)
  and is a decision for the solver integration owner — see §8.

## 3. Baseline (pre-existing state of `main`)

Focused S3 suite on the unchanged base
(`test_e4_pl_s3_v2d_linear_native_parity.py`, `test_s3_v2d_default_activation.py`,
`test_local_patch_transition.py`, `test_fe_solver_triangular_shell_backend.py`,
`test_e4_pl_s3_v2d_native_state_corotational.py`,
`test_e4_pl_s3_v6g_recovery_current_eigen.py`, `test_e4_pl_s3_opt_in.py`):
**86 passed, 3 failed** in 635 s. The failures are pre-existing and unrelated
to this work:

* `test_v2d_stateless_identity_roundtrip_and_remaining_successor_gaps` —
  `git show dfe3d31…:src/anysolver/e4_pl_s3_v2d_element.py` fails in this
  shallow clone (missing history).
* `test_v6g_contract_is_canonical_and_defaults_remain_frozen`,
  `test_v6g_closes_the_frozen_v6f_readiness_inventory` — historical audit
  scripts still assert `DEFAULT_S3_FORMULATION = "legacy-s3"`, stale since
  V2D default activation.

Also observed on the unchanged base during the hygiene check:
`tests/test_release_043.py::test_publication_manifest_checks_all_accepted_runtime_files`
fails because the SHA-256 of `scripts/release_043_runtime.json` (byte-identical
to `be41a77`) does not match the pinned value in this Linux checkout. It is
unrelated to this work.

Pre-existing performance defects found while building the campaign (not
angle-related; recorded, not fixed here):

1. `assemble_load_vector` with shell pressure on a V2D model runs
   `_qualified_s3_pressure_surface_records`, whose per-element
   `internal_input_guard` falls back to the full model-wide lifecycle scan
   (the trusted constant-time guard is absent), including a V2D
   `to_dict`/`from_dict` round-trip per element: **O(n²)** (1,408 triangles:
   460 s vs 8.5 s for the same vector through `LoadCase.get_load_vector`).
2. `assemble_geometric_stiffness_matrix` / `solve_eigenvalue_buckling` on V2D
   models: also quadratic (352 triangles: 83 s for KG).
3. `NativeParityE4PLS3V2DShellElement._validate_model_scope` scans all
   registered elements on each `_geometry()` call, so any per-element
   post-processing sweep over a model is quadratic.

The campaign runner works around (1)–(3) without changing solver code: it
uses the solver's own consistent pressure integration, each element's own
geometric-stiffness operator, and per-element evaluation on a private
three-node mesh. `tests/test_s3_angle_models.py` proves the workarounds give
the same vectors/eigenvalues as the public routes (bitwise for the pressure
vector; 1e-10 relative for the buckling factor).

## 4. Geometry envelope

Normalized area `q = 4 sqrt(3) A / (l1² + l2² + l3²)`.

| Candidate (test input only) | min angle | max angle | edge ratio | scaled Jacobian | q |
| --- | ---: | ---: | ---: | ---: | ---: |
| historical_30 | 30° | 150° | 4.0 | 0.20 | 0.60 |
| candidate_20 | 20° | 150° | 4.0 | 0.20 | 0.40 |
| candidate_15 | 15° | 150° | 4.0 | 0.20 | 0.30 |

Joint-envelope arithmetic (`tests/test_s3_angle_element.py`):

* With min angle ≥ α and max angle ≤ 150°, the smallest `q` is attained by
  the obtuse isosceles triangle (α, α, 180 − 2α) — a dense sweep confirms
  `q(20,20,140) = 0.402503` and `q(15,15,150) = 0.302169`. The candidate `q`
  floors are therefore implied by the angle floor and never bind.
* Edge ratio: the (α, 90 − α/2, 90 − α/2) and right (α, 90, 90 − α) shapes
  give 2.88/2.92 at 20° and 3.83/3.86 at 15°, inside 4.0; the ratio bound
  binds only below ≈ 14.5° (14°: 4.10–4.13).
* Scaled Jacobian = sin(min angle): 0.342 at 20°, 0.259 at 15°; binds only
  below ≈ 11.5°.
* At 15° the obtuse isosceles shape sits exactly on the 150° maximum-angle
  limit.

So each candidate envelope is effectively "min angle ≥ α and max angle ≤ 150°".

## 5. Element evidence (G1)

`tests/test_s3_angle_element.py` (137 tests, ~5 s) on the public default
route, for bands 30/25/20/17.5/15° (plus a 10° diagnostic band) and five
shapes per band (acute isosceles, right, asymmetric acute, asymmetric obtuse,
obtuse isosceles), `t/L ∈ {1e-1, 1e-2, 1e-4}`:

| Check | Result at every band incl. 10° |
| --- | --- |
| Symmetry (dimensionless) | exact (0.0) |
| Rigid-body residual `‖K R‖ / max diag K` | ≤ 3.5e-16 |
| Elastic rank | 12 (six rigid modes only); smallest elastic eigenvalue / (t/L)² ≥ 4.6e-3 |
| Linear membrane patch (with matching drill) | relative energy error ≤ 2e-15; PL energy ≤ 1e-16 × membrane |
| Kirchhoff constant-curvature patch | relative energy error ≤ 2e-13; transverse shear energy ≤ 2e-13 × bending |
| Node-order covariance (all 6 permutations) | ≤ 1e-12 × max\|K\| |
| Global-frame objectivity (3 seeded rotations + translation) | ≤ 1e-11 × max\|K\| |
| Scale covariance (×1e3 geometry and thickness) | ≤ 1e-11 relative |

Geometry-caused conditioning (dimensionless, rigid complement, `t/L = 1e-2`)
grows smoothly: obtuse isosceles 1.4e6 (30°) → 2.0e6 (25°) → 3.1e6 (20°) →
4.1e6 (17.5°) → 5.7e6 (15°); no cliff. Right/acute shapes are ≈ 2× better.
Conditioning scales with `(L/t)²` as for any thin-shell element.

Classification: no admission-only, numerical-implementation or formulation
failure observed at the element level down to 10°.

## 6. Assembled-model campaign (G2/G3)

Runner: `scripts/qualify_s3_angles.py` (formal mode, 4 shape-preserving
refinement levels). The infrastructure and the acceptance criteria
(`ACCEPTANCE`) were committed in `5671c8f` **before** the formal runs.
Evidence (manifest with source/dependency identity, raw `results.json`,
`verdict.json`, `SUMMARY.md`):

* `reports/s3_angles/5671c8f73c69/formal-t20/` — clean tree, 2,828 s.
* `reports/s3_angles/5671c8f73c69/formal-t15/` — clean tree, 3,736 s.

Reproduce: `python scripts/qualify_s3_angles.py --target 20 --levels 4 --mode formal`
(and `--target 15`). The exit code is non-zero when a required criterion
fails.

All references are analytical. None uses legacy S3 or coarse Q4 as ground truth:

* **Membrane:** Timoshenko–Goodier plane-stress cantilever field (cubic, exact
  equilibrium), prescribed on the whole boundary. The metrics are the energy-norm
  error `sqrt((U_h − U)/U)`, the max nodal displacement error, and the L2 error
  of the raw Hammer-station membrane resultants against `t σ`.
* **Plate:** hard simply-supported Mindlin plate under uniform pressure. The
  reference is the Navier double-sine series (301 odd terms), giving centre
  deflection, compliance, and the L2 error of the raw station moments
  (rotated to global).
* **Vibration:** SS Mindlin plate without rotary inertia, matching V2D's
  translational lumped mass.
* **Buckling:** SS plate under uniaxial `N_x`, with Mindlin-corrected `k(m)`.
* **Nonlinear:** corotational cantilever strip under a 1 rad end moment with
  ν = 0, compared against the exact circular arc.

### 6.1 Results summary (finest level unless noted)

| Family | 45° baseline | 20° | 15° |
| --- | --- | --- | --- |
| Membrane energy-norm rate (all families) | 1.00 | 1.00 | 1.00 |
| Membrane N L2 error, right / obtuse families | 0.118 | 0.076–0.104 / 0.047–0.048 | 0.069–0.104 / 0.045–0.051 |
| Plate w_c error t/L=1e-2, right / obtuse | 1.4e-4 | 4.6e-4 / 1.4e-4 | 5.4e-4 / 2.1e-4 |
| Plate w_c error t/L=1e-3 (locking probe) | 2.3e-4 | 6.2e-4 / 2.8e-4 | 7.4e-4 / 4.1e-4 |
| Plate compliance rate | 2.2–2.7 | 2.0–2.5 | 2.0–2.5 |
| Plate raw-moment L2 error / rate | 3.9e-2 / 1.00 | 2.0–3.1e-2 / 1.00–1.02 | 2.0–2.9e-2 / 1.00–1.02 |
| First frequency error | 6.5e-5 | 2.4e-4 / 8.5e-5 | 2.9e-4 / 1.3e-4 |
| Buckling factor error | 9.3e-4 | 1.3e-3 / 7.5e-4 | 1.4e-3 / 7.9e-4 |
| Corotational end-moment tip error (level 2) | 5.1e-5 | 5.1e-5 / 1.4e-3 | 5.1e-5 / 4.6e-3 |
| Newton iterations (8 steps) | 56 | 53 / 40 | 51 / 40 |

There is no locking trend: t/L = 1e-3 converges at rate 2.0 for every family.

Mixed Q4/S3 panels (t/L = 1e-2, finest level). "Layout at 30°" is the same
placement with 30° triangles, which isolates the angle effect from the
S3-versus-Q4 accuracy difference.

| Pattern (S3 fraction) | w_c error 20° | 15° | layout at 30° | all-Q4 |
| --- | ---: | ---: | ---: | ---: |
| isolated (0.6%) | 3.2e-4 | 2.5e-4 | 5.4e-4 | 1.8e-4 |
| chain (7%) | 8.2e-4 | 6.8e-4 | 1.05e-3 | 1.8e-4 |
| boundary fill-in (7%) | 8.4e-4 | 7.0e-4 | 1.08e-3 | 1.8e-4 |
| cluster at plate centre (11%) | 1.16e-3 | 1.17e-3 | 4.1e-4 | 1.8e-4 |
| quarter (24%) | 9.0e-4 | 1.20e-3 | 8.6e-4 | 1.8e-4 |

S3 raw-moment L2 errors in mixed panels range from 0.4% to 3.2%. The
mixed-panel first frequency is within 0.09%. The cluster pattern sits exactly
at the measurement point; its error is 2.8× the 30° layout but still 0.12%,
converging at rate ≈ 1.9.

### 6.2 Criteria outcome

| Target | Criteria passed | Failed criteria |
| --- | --- | --- |
| 20° | 72 / 73 | `membrane_right_x_resultant_vs_regular_at_equal_dofs`: 1.503 (limit 1.5) |
| 15° | 71 / 73 | the same criterion for `right_x` 1.752 and `right_alternating_x` 1.647 |

**Diagnosis of the failed criterion.** The check bounds the membrane-resultant
error per DOF relative to the 45° family. The failing families are
right-triangle meshes whose cells have aspect `1/tan α` with the long side
along the depth, where `σ_xx` varies. Their error per refinement level is
*lower* than the 45° family's (0.104 vs 0.118), and their rate is 1.00. They
simply spend DOFs in the direction that does not reduce the constant-strain
error.

The control `reports/s3_angles/5671c8f73c69/independent/membrane_aspect_control.txt`
shows that the ratio tracks cell aspect, and is already above 1 inside the
historical envelope:

| angle (aspect) | right | right_alternating |
| --- | ---: | ---: |
| 30° (1.73) | 1.22 | 1.02 |
| 20° (2.75) | 1.50 | 1.36 |
| 15° (3.73) | 1.75 | 1.65 |

Classification: a formulation-accuracy property of the unchanged CST membrane
on anisotropic cells (mesh efficiency), not an implementation defect and not
new to sub-30° triangles. Under the plan's rules the frozen criterion is **not**
relaxed after the fact. Accepting this behaviour requires a recorded, justified
change of qualification scope by the solver integration owner (§8).

### 6.3 Independent reproduction

`reports/s3_angles/5671c8f73c69/independent/reproduce_plate_20deg.py` rebuilds
the 20° right-triangle plate (352 elements) with separate code and solves it
through the public pressure `LoadCase` route. Its centre deflection is 0.93%
off a hand-coded Kirchhoff Navier sum; the campaign reports 0.98% against the
Mindlin reference, the difference being the shear correction. The Timoshenko
table coefficient 0.00406 agrees. The same author wrote it, so it is **not**
the plan's independent-reviewer reproduction (G5).

### 6.4 Cost of low-angle meshes

These are geometry-caused costs; no solver code changed, so there is no
implementation overhead to attribute. The pure-S3 families need more
elements to cover the same domain at the same short edge. At the finest
level a 45° plate has 6.5k DOFs (static solve plus post-processing 4–5 s),
a 20° right plate 17.6k DOFs (18 s), and a 15° obtuse plate 47k DOFs (98 s).
Newton iteration counts were equal or lower (§6.1). Element conditioning at
t/L = 1e-2 grows from 1.4e6 (30°) to 3.1e6 (20°) and 5.7e6 (15°).

## 7. Capability matrix (V2D, isotropic homogeneous elastic section)

| Capability | Below 30° evidence | Status |
| --- | --- | --- |
| Element contract (rank, rigid body, patch, covariance, objectivity) | §5, 10–30° | executed |
| Linear static membrane / bending / thin (t/L 1e-3) | §6 | executed |
| Mixed Q4/S3 panels (0.6–24% S3) | §6 | executed |
| Modal (lumped translational mass) | §6, direct route cross-checked against `solve_free_vibration` | executed |
| Reference buckling (uniform membrane-compression policy) | §6, direct route cross-checked against `solve_eigenvalue_buckling` | executed |
| Corotational elastic nonlinear static, consistent tangent | §6 (1 rad) | executed |
| Restart equivalence (bitwise) | `test_corotational_restart_is_bitwise_equivalent_on_a_15_degree_mesh` (2 elements, see §3) | executed (small model only) |
| Generalized `A/B/D/As` sections, layered J2/Hill plasticity, initial fields, offsets | none at < 30° | **not executed** |
| Follower pressure, arc length, von Kármán kinematics | none | **not executed** |
| Transient, contact, activity/erosion | none | **not executed** |
| Curved/faceted shells, connected/stiffened plates, beam–shell coupling | none | **not executed** |
| External (CalculiX) comparison | none | **not executed** |

## 8. Decisions and outcome

**Outcome labels (plan §11)**

* **20°: `RESTRICTED_CANDIDATE`.** Within the executed capability scope of
  §7, flat isotropic homogeneous-elastic V2D meshes with minimum angle ≥ 20°
  (max ≤ 150°) meet every frozen criterion but one. That one is the membrane
  per-DOF efficiency on cells with aspect > ≈ 2.7 misaligned with the stress
  gradient (§6.2). Full default parity is **`NOT_QUALIFIED`**: the
  capabilities marked "not executed" in §7 lack sub-30° evidence.
* **15°: `RESTRICTED_CANDIDATE`**, assessed separately from 20° with its own
  formal run and the same scope. The same membrane efficiency criterion fails
  for two families (aspect 3.7). Full parity is **`NOT_QUALIFIED`**.
* Neither `GO_20` nor `GO_15` is claimed. Nothing is `READY_TO_MERGE` as a
  production extension. The additive test infrastructure, runner, evidence
  and this note are landable on their own (plan G5, first deliverable).

**Mechanics changed:** no. No file under `src/` was modified. The old envelope
is therefore bitwise-unchanged by construction, and the performance budgets
(§9 of the plan) hold trivially.

**Decisions for the solver integration owner**

1. *Admission semantics.* The default V2D route already accepts every
   non-degenerate triangle, including below 15° (§2). "Supporting 20°"
   therefore means documenting a qualified envelope, not relaxing a check. If
   the owner wants rejection outside the qualified envelope, that is a new
   fail-closed restriction on the default formulation. It could break
   existing models (10° triangles are accepted today). The place for it is a
   V2D-owned admission policy with a versioned identity, not the historical
   `e4_pl_s3_state.py` constants.
2. *Membrane efficiency scope.* Either accept the documented CST per-DOF
   penalty on anisotropic cells as a mesh-design property (redefine the
   criterion against the same layout at 30°, recorded as a new scope), or
   keep the 1.5 bound. The latter implies an aspect-dependent restriction that
   the 30° envelope itself only barely meets (1.22).
3. *Mesher target.* ANYmesher's `DEFAULT_S3_QUALITY_POLICY` and the runtime
   local-patch sizing keep a 30° *preferred* target. The plan keeps that
   separate from solver admission, and no change is proposed here.
4. *Remaining capability evidence.* Run the §7 "not executed" rows at 20°
   (then 15°), reusing `tests/_s3_angle_fixtures.py` and the runner's mesh
   families.

### 8.1 Decision (28 September 2026): the solver serves the mesher

The integration owner's direction: the mesher keeps aiming for good meshes, and
the solver fails only when that is truly required. Consequences:

* **Solver admission stays degeneracy-only (no change).** A probe of the
  public V2D route beyond the campaign bands (right and obtuse-isosceles
  shapes, t/L = 1e-2):

  | smallest angle | result |
  | --- | --- |
  | 10° to 1° | exact to ≤ 1e-11 (patch tests, rigid body, 12 elastic modes) |
  | 0.1° to 0.01° | patch errors ≤ 5e-8; conditioning 1e11 to 1e13 |
  | 0.001° | bending patch error ~1e-5 |
  | 0.00001° | patch errors up to 6%, still admitted |

  The existing degeneracy check fires only near 1e-12°. The only floor that
  might be called strictly required, around 0.001°, is far below anything a
  mesher produces, so no solver guard is added. The accuracy envelope
  qualified by this note is 15° with a maximum angle of 150°.
* **Mesher admission follows the solver floor.** ANYmesher branch
  `claude/s3-two-tier-admission`, off `main`, kept separate from the ongoing
  `claude/anymesher-050-release-4xztmm`:
  * `S3_ADMISSION_FLOOR_POLICY` (15°, q ≥ 0.30) becomes
    `DEFAULT_S3_QUALITY_POLICY`.
  * The former 30° envelope stays as `S3_TARGET_QUALITY_POLICY`. Bounded
    repair and `prepare_qualified_s3_mesh` work towards it and report any
    shortfall instead of raising.
  * Shape limits are compared with a 1e-12 tolerance.
  * The admission contract ID `ANYMESHER_QUALIFIED_S3_ADMISSION_V1`, which
    ANYsolver pins in `production_readiness.py`, is unchanged. The production
    preparation record becomes `..._PREPARATION_V2`.
* **ANYsolver's runtime local-patch sizing keeps its 30° target.** It only
  refines to reach good triangles and never fails, which matches "always try
  to get good meshes".

This settles decision 1 above (no fail-closed solver restriction) and decision
3 (the mesher target stays 30°, while mesher admission moves to the 15° floor).
Decisions 2 and 4 remain open.

**Working-tree condition.** Only this task's branch
(`claude/wizardly-ramanujan-pk88wc`) in this cloud checkout was used. No
worktrees were created and no other branch was touched.
