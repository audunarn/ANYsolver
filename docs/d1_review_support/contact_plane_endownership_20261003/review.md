# Supporting Read scrutiny — fixed-plane physical-end ownership

Reviewer `/root/beam_surface_contract` inspected beam_plane.py and the new independent ownership tests without edits, tests or nested delegation. Same model family; not independent engineering acceptance.

No concrete defect found in the affine ownership certificate: both actual end gap and B3 outward derivative projection are affine; evaluating the exact root gap excludes a closed switch. Endpoint work remains R=k_end*g*n and K=k_end*n*n^T. Empty endpoints preserve the uncapped gap limiter. The lead additionally retained its exact historical arithmetic order before the final artifact.

One contract omission found: maximum_swept_subdivisions now controls cap trial cutbacks but was not restart-bound. The lead added it to the cap-only contract and verified incompatible fresh continuation rejects. The earlier artifact/source are retained.

Suggested tilted-plane discriminator was implemented for B2 and curved B3. Complete local work/tangent and force/moment covariance, closed/open ownership decisions and actual quadratic derivative checks pass. These are geometry/work checks, not finite-rotation structural admission.

An independent integrated axial-bar scalar equation checks the coupled distributed-line and endpoint force within1e-6 relative tolerance. Active fresh restart, earlier uncapped plane cases, physical junction topology, both public geometry examples and installed no-contact compatibility pass. Broader engineering/refinement, dynamic and friction claims remain open.
