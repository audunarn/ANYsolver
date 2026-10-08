# Actual hemisphere caps on a deforming S3 skin — development

`JET2_B2_B3_HEMISPHERE_SUPPORT_DEFORMABLE_FIXED_DIRECTOR_S3_STATIC_DEV_V1`
is implemented and installed-tested. It has no independent engineering acceptance,
normal application admission or release.

Run `examples/general_contact_deformable_s3_caps.py`. Select
`beam_end_cap_work="hemisphere_support_dev"` and
`beam_shell_geometry="jet2_deformable_s3_dev"`, explicit hemisphere radius,
line stiffness (N/m²), endpoint stiffness (N/m), gap tolerance and radius-covering
physical-face clearance. One elastic concentric B2 or straight-reference B3
contacts one qualified S3 V2D physical interior. Target translations and plane
normal deform; shell rotations remain exactly zero. Physical sides/offsets use
the existing formulation-owned skin work map.

For endpoint centre c, actual outward tangent d and moving skin normal n, define
h=(c-p)·n and β=d·n. The actual hemisphere minimum gap is h−R for β≤0 and
h−R√(1−β²) for β>0. It is C1 at β=0; its Hessian is one-sided there.
Each active endpoint has potential ½ k_endpoint min(g,0)², distinct from the
existing reference-length line potential. Existing Jet2 differentiates every beam
and physical skin coordinate, including B3 midnode/tangent, moving anchor/normal
and cross-body blocks. Both potentials are summed before WᵀG/WᵀHW assembly.
Skin offset couples and full physical forces/moments follow that same work.
Only genuine all-material-node physical ends receive endpoint contributions.

The inherited whole-radius moving-plane/face-interior sweep contains every cap,
with actual curve regularity checked separately. It can conservatively reject a
safe cap step. Parallel nonunique rim support is admitted only as open, without
a smooth-contact claim. Finite face rims, corners, multiple faces, target rotations,
material-surface spin/friction, native contact and dynamics remain outside this row.

## Checks actually run

Private installed suite: **31 passed in 14.242 s**, **351,694,848 B** peak tree
memory, JIT disabled, effective pools/Numba one thread; 217 loaded modules and all
504 package files match candidate bytes. Tests cover independent scalar support
and energy, all-coordinate 10⁻⁵ tangents/cross blocks, both orientations, B3 midnode,
rigid covariance, seam branches, offset couples, true ends, gap cutback and explicit
unsupported selection rejection. The actual guided deformable-target fixture has
contact-gradient relative error **5.871×10⁻¹²** against the independent scalar
oracle (10⁻⁶ target). A separately bounded linearized structural reference differs
by **4.399×10⁻⁶** (10⁻³ development target); it does not qualify the full nonlinear
structural model. Minimum gap −3.814×10⁻⁷ m meets the explicit 10⁻⁵ m budget.

Force control, matching 32-increment displacement control, completed split JSON
restart, incompatible law/settings rejection, actual cancellation/exception replay,
uncapped S3/B3 routes, state lifecycle and lazy no-contact checks pass. A coarse
first displacement trial remains rejected. The driver now assembles and seals only
the accepted origin when qualified S3 state is initially absent; it preserves the
original non-success. Failed checkpoints remain noncontinuable.

[Evidence](d1_review_support/contact_deformable_s3_caps_20261004/summary.json)
retains seven measured runs/51 records, including the original state defect,
fixture errors and cache-denied first wheel build. Supporting source scrutiny of
integration/driver is not independent acceptance of the worker-authored geometry.
No performance savings or full-programme completion claim is made. The uncapped
line profile, historical cap laws/defaults and frozen evidence are unchanged.
