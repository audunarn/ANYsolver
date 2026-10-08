Supporting independent OpenAI contract review, 5 October 2026
Reviewer: /root/nonlinear_external_scope_audit; not implementation author.
No numerical execution or different-model-family acceptance implied.

Actual elastic S3 V2D local membrane/curvature/shear strains are linear:
Km = D.T k D; G = sum(f_j Hess d_j), retaining actual local correction and
its force. Do not add standalone S3 geometric stiffness or reuse a spatial
split as coordinate blocks. Replay actual driver stable-translation policy.

Native fibre full42 blocks are [[G,B.T],[B,-S]], including hessian_low and
coupled cell compliance. Do not replace them with station-local inverses.
Nested stations[].fibres[] must each be ELASTIC with matched identities,
unchanged canonical history, actual fixed-origin flow curve and high+low stress.
CLASSICAL_SMOOTH_BRANCH alone also admits smooth plasticity and is insufficient.
Opposing fibre stresses can cancel section force while a fibre yields.
Pre-existing plastic history may unload elastically under the frozen potential;
no current plastic advancement is admitted.

Reviewer delta: no mechanical reason for a 1-unit stress floor. It changes
admission under equivalent units. Adopt r-|sigma| > 64 eps max(|sigma|,r),
finite positive radius. Subnormal metadata additionally needs a representability
or ULP check (or explicit unresolved-metadata rejection); an arbitrary 1-unit
floor does not solve that issue. Root supplied this requirement to author.

Required checks: independent bounded dense scatter; actual-update covector
Hessian, nonzero rotations/point moments, anchors/rebase, full retained equation
and constraints, high+low boundaries, opposing stresses, smooth-plastic and
changed-history negatives, mixed families, accepted-state/restart preservation.
Product and installed evidence review remains pending at this record.
