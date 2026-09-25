# C3 development owner: one native B3-GE beam on one elastic S3 interior

`NativeRetainedRoundS3Analysis` couples one retained native B3-GE beam and one
elastic S3 V2D shell element in a single nonlinear static Newton system. It
keeps all native internal coordinates, all shell model DOFs and the native
material trial origin. The shell's exact elastic stiffness and physical-skin
work map come from the admitted S3 formulation. The owner adds the contact
residual and all beam–shell tangent blocks before reducing constraints. Its
native rotation block uses the existing spatial Jacobian correction.

The admitted development input is deliberately narrow:

- One native generalized beam with a retained nodal force program and one
  separate S3 V2D model. Their numeric node and element IDs may coincide.
- One ordered S3 skin, one declared round centreline radius, frictionless line
  penalty and an explicit physical rim clearance. The whole Q2 Bézier hull
  must remain in the certified triangle interior.
- Isotropic elastic S3 material, no section override, no shell activity,
  shell load cases or multipoint constraints. Shell supports are simple zero
  displacement/rotation values. A remaining static mechanism is rejected.
- Native force-control targets from the existing program. The shell is loaded
  through contact and remains deformable. No shell prescribed motion or
  external force route is admitted here.

Initial interference is rejected. A candidate step must pass the dimensional
gap tolerance and a bounded swept check for both normal gap and physical rim
clearance. The check bounds rotation-dependent native Q2 motion and the
linearly changing shell triangle, including its normal and edge directions.
It uses a positive Bernstein lower bound on the oriented triangle area and
Lipschitz bounds between checked poses. Ambiguity or an exhausted subdivision
budget rejects the candidate. A large valid shell rotation can be rejected by
this sufficient certificate; the owner never flips the physical side.

Every structural/contact candidate evaluates from the last accepted native
material history. The owner stores a new history only after coupled equilibrium
and endpoint gap pass. A failed solve returns the prior accepted state. There
is no restart schema yet; no failure or cancellation recovery beyond this
in-memory transaction is claimed. The current result reports the contact
kernel's forces, moments, gap and integration counters, plus retained native
and shell displacement states. It is not a supported public contact route.

`examples/general_contact_native_s3_static.py` is the runnable development
case. Its curved beam and S3 patch pass two force targets, producing nonzero
native internal contact work and shell displacement. Focused checks cover
coupled equilibrium, action/reaction, the assembled cross tangent, a curved
retained-cell result, initial interference, unsupported shell material and
mechanism rejection, definition mutation, and failed-solve rollback. These
are local Level-A checks. Independent C3 acceptance still requires broader
geometry/pairing, restart, prescribed motion, refinement and review.
