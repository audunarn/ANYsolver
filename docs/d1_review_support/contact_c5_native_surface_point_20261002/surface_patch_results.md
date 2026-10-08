# Fixed native swept-surface patch — development result

2 October 2026. Base 902bf5ff plus hashes in surface_patch_results.json.
Raw selections, imports/runtime, resources and output: surface_patch_raw.zip.
No C5 acceptance, installed native verification or release is claimed.

## Implementation

The reference rule integrates the actual surface x(xi,alpha)=r(xi)+R(xi)rho(alpha),
including the native reference lift and frame derivative. Area uses the norm of
the cross product of its two parameter derivatives. The outward sign is checked;
reference weights remain fixed during deformation. Gauss rules split at native
cell boundaries, carry stable material identities and have an explicit point cap.

The patch sums complete already-spatial point residuals/tangents and keeps separate
point histories. Existing structural assembly, one chart conversion, equilibrium
driver, atomic commit and canonical V2 replay remain authoritative. Definition
binding includes rule resolution, weights, coordinates, target material points and
all laws. This adds no second normal contact law or independent solve stack.

## Checks and retained failure

- Cylinder area and curved-parabola sweep area agree with independent analytic/
  scalar-integral references. Both native cells are represented.
- Deformed curved surface parameter tangents agree with independent finite
  differences; the physical normal differs from the radial direction under shear.
- Existing contact integrated using the derived area weights reproduces the
  analytic cylinder-patch normal force on both bodies.
- Four independent material points solve active friction and deformable-S3
  equilibrium. Same-load history rebase is equilibrated; full/restarted active
  continuation is identical. Foreign history and last-point mutation reject.
- Existing single-point active owner/restart still passes after transaction changes.

The first area run had four passes and one failed pressure fixture: its selected
patch crossed the existing triangle's real boundary. The test now declares an
interior xi interval and changes its analytical reference length accordingly.
No ownership guard or mechanics tolerance was relaxed. That targeted case passes.
The initial patch-owner selection passed two checks in 8.06 s. The final orientation
selection passed four checks in 12.24 s, including both patch checks and the existing
single-point owner. A later test rename/comment correction changes no execution.
Resource measurements and effective runtime settings are in the retained records.

## Independent scrutiny and boundary

Independent OpenAI source review found that endpoint source-orientation checks
could admit inversion inside an exponential path. A tilted-axis rotation gives
positive signed area at both endpoints but negative area internally. The added
certificate bounds signed area/radius squared using the affine chord and exponential
director path; finite-budget midpoint Lipschitz enclosures cover whole intervals.
The counterexample rejects before history evaluation. Follow-up source review found
no concrete defect in this correction. Review did not run tests and does not supply
cross-family or engineering acceptance.

Orientation is certified only at the rule's fixed material samples. Between-sample
regularity/gap, integration refinement, rotating release/recontact, work/step
convergence, target-boundary clipping, partner transfer, caps and general surfaces
remain open. The fixed target adapter has explicit material coordinates per point;
this does not qualify arbitrary sliding across facets.
