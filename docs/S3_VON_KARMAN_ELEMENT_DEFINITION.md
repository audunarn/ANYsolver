# S3 V2D element under the von Karman law (S3_V2D_VK_R1)

Status: description of the code as merged at `a0781c0bc` plus this branch. Derived from the code
(`src/anysolver/e4_pl_s3_v2d_element.py`) and checked against an independent derivation
(`tests/s3_vk_element_oracle.py`, validated in `tests/test_s3_vk_element_oracle.py`). Not reviewed by another
model family. SI units (m, N, rad, Pa); `E`, `nu` isotropic elastic constants, `t` thickness.

## 1. Kinematics
* Flat three-node triangle in 3-D, six dofs per node: translations `(ux,uy,uz)` and rotations `(thx,thy,thz)` in the
  global frame (18 dofs, external node order).
* Local frame (`_geometry`, line 671): the nodes are ordered internally so that `(p1-p0)x(p2-p0).n > 0`
  (`order`), `ex = (p1-p0)/|.|`, `ez = n` (the reference normal, which must be the facet normal), `ey = n x ex`.
  Local dofs per node are `(u,v,w,tx,ty,tz)` = `Rᵀ`-rotated translations and rotations
  (`_local_component_transform`, `_block_permutation`); `local_u = transform @ u`.
* P1 shape gradients `G_i = (dN_i/dx, dN_i/dy)` (constant), area `A`.
* Linear strain measures (stations are three equal-weight points, weight `A/3`; membrane and curvature
  operators are identical at all stations, the assumed shear operators are not):
  * curvature `kappa = p*(dty/dx, -dtx/dy, dty/dy - dtx/dx)` (`p` = `director_polarity`),
  * membrane at the reference surface `(du/dx, dv/dy, du/dy+dv/dx)` (engineering shear),
  * membrane at the mid-surface `eps_m = eps_ref - offset*kappa` (`_effective_station_operators`, line 831;
    `offset = reference_surface_offset`),
  * transverse shear `gamma` (assumed field, `B_s`), drilling and PL stabilisation (`pl`): linear, unchanged by the law.

## 2. The von Karman law
`w` is the local transverse displacement of the reference surface, affine on the triangle (node values `w_i`,
local dof 3). `(wx,wy) = sum_i w_i G_i`. The law adds, at the mid-surface level and at every station,
`eps_vk = (wx²/2, wy²/2, wx*wy)` to the membrane strain (engineering shear: `wx*wy`, not half)
(`_native_trial_response`, lines 2127-2134). Nothing is added to curvature or shear. Rotations enter `w`
only through the linear `-offset*kappa` part of `eps_m`; the slope `(wx,wy)` uses the node translations only
(not corrected by the reference-surface offset - an approximation, see 6).

## 3. Energy and internal force (layered elastic section)
Section: symmetric Lobatto layers about the mid-surface (`qualified_s3_lobatto_layers`, exact for a section
linear in `z` with >= 3 layers) so membrane and bending decouple:
`N = t Q (eps_m + eps_vk)`, `M = t³/12 Q kappa`, `Q = E/(1-nu²) [[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]]`.
Energy (element-local, per unit, no external work):
`U = A [ ½ eps_totalᵀ tQ eps_total + ½ kappaᵀ (t³/12 Q) kappa + ½ gammaᵀ phi² H gamma ] + ½ uᵀ pl u`.
Internal force `F = transformᵀ dU/du_local`; implemented as `force_local += combinedᵀ resultant * A/3`
over the stations (lines 2155-2230) with `combined` containing the VK-augmented membrane operator
`J = B_m + [wx gx; wy gy; wy gx + wx gy]` (lines 2131-2134, `gx,gy` = rows of the `w`-gradient operator).
Hence `F_vk = F - K u = A (Jᵀ tQ eps_total - B_mᵀ tQ B_m u)`, with rotation-dof entries coming only from the
`-offset*kappa` part of `B_m`.
Non-elastic layered materials use `plane_stress_return_map` per layer/station; the same `eps_vk` is inserted
before the return map (not covered by the oracle). The generalized-section branch (`shell_section`) inserts
`eps_vk` identically using the generalized constitutive matrix (not covered by the oracle).

## 4. Consistent tangent
`T = combinedᵀ C_alg combined A/3 + A/3 sum_stations gᵀ [[N_x,N_xy],[N_xy,N_y]] g` with `g` the `2x18`
`w`-gradient operator (material part with the VK operator, lines 2210-2230; geometric part from the membrane
resultants, lines 2266-2272), symmetrised at line 2282. It is the exact derivative of `F` for the elastic
section (checked, section 7).

## 5. Exact versus approximated
Exact (to roundoff, checked): force = dU/du, tangent = dF/du, the 18-dof excess for any flat triangle
orientation, offset, polarity, thickness, `E`, `nu` and 3 or 5 Lobatto layers.
Approximations / modelling choices: (i) `eps_vk` is evaluated from reference-surface translations only;
(ii) VK strain is not objective under finite rigid rotation (membrane strain from `w` slopes), measured
moment-balance drift 1.2e-6 N·m vs 1e-6 budget in triage; (iii) linear shear/drilling/PL are the pre-existing
E4-PL parts, not re-derived here; (iv) initial prestrain/resultants are added after the strain (not covered).

## 6. Where each term lives
| Term | Location |
|---|---|
| frame, order, `G`, area | `e4_pl_s3_v2d_element.py:_geometry` |
| curvature, membrane, shear operators | `_operators` (`e4_pl_s3_v2c_element.py:1578`), `_effective_station_operators` (831) |
| elastic section constants | `_elastic_baseline_constitutive` (738) |
| `eps_vk`, VK operator | `_native_trial_response` (2127-2134) |
| force, material tangent | `_native_trial_response` (2155-2260) |
| geometric tangent | `_native_trial_response` (2266-2272) |
| solver entry (`kinematics="von_karman"`) | `nonlinear_static._assemble_nonlinear_system`, calls `compute_nonlinear_response(..., von_karman=True)` (2752) |
| state marker | `trial["experimental_von_karman_law"] = "S3_V2D_VK_R1"` (2287) |

## 7. Independent check
`tests/s3_vk_element_oracle.py` rebuilds `F_vk` and `T_vk` from sections 1-3 without calling any production
element code. `tests/test_s3_vk_element_oracle.py` verifies by complex-step differentiation that its force is
dU/du and its tangent dF/du, and compares against production on random triangles/states
(see the test for the stated tolerances and measured maxima).

## 8. Known limits
Layered elastic isotropic; non-flat facets are refused by the element; VK is not rigid-rotation objective;
reference-surface slope only; the rate recovery in `transient.py::_consistent_s3_descriptor_rates` uses the VK
tangent, whose directional curvature was a finite difference before this branch's analytic replacement.

### Known limit: large in-plane slide of a pressed S3 patch (2026-10-24)
Under the VK default, imposing the 0.55 m slide of the partial-overlap friction-replay fixture in ONE step refuses with the typed outcome
`stopped_at_limit` / `contact_gap_exceeded` (no number is produced): the pressed source element carries compressive membrane resultants
N = (-69, -20, -55) N/m, the geometric stiffness `g^T N g` is buckling-type negative (element tangent lowest eigenvalue -50.7; reduced tangent -48
against -0.54 pre-VK), Newton stagnates (residual 32.1, 31.09, 31.07 vs 32.1, 6.5e-4, 1.6e-9 pre-VK) and the admissible-step fraction collapses
(1, 0.031, 0.0005, 0). The element tangent is consistent (central finite difference 1.4e-7 on a 3949 scale; first-principles oracle 1e-15).
The same load path in >= 2 equal increments converges (5-6 Newton iterations per step, tangent positive, lowest nonzero eigenvalue 22.8-26.5) and its
final state is path independent (2/4/8 increments agree to 1.3e-11). Pre-VK vs VK at the end of the slide: max |du| 8.7e-6 (0.55 m scale);
pressures 3.96922/3.56505/3.33933 -> 3.96821/3.56326/3.33844 Pa (2.5e-4..5e-4); reaction (0.0749835,-0.2496361) -> (0.0749610,-0.2495583);
slide dissipation 0.045009 -> 0.044581 J (-0.95 %, first half-step -1.8 %, second -0.04 %). Consequence for the qualified S3 claim: qualified
statics/contact paths that slide a pressed S3 patch over lengths comparable to its own size must be run in increments; the single-step case is a
documented typed refusal, not a wrong result. Test schedule: tests/test_general_contact_s3_friction_replay.py (slide in two increments;
regenerated reference separation_full_v1_vk_s3r1_checkpoint.json, provenance next to it).
