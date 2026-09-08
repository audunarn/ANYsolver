# Translation-owned physical factor capture

Parent16065cae61b90e96b71439f55112efaa22fb1782. Add a private native bridge for
the existing retained displacement controller, without changing any element,
controller, arc/force modal bridge, default, alias or accepted evidence.

A new typed TranslationPencil owns actual completed-target count, displacement
target and load factor. Its producer validates and replays the genuine complete
translation checkpoint through that controller's Context. No arc/force capsule
conversion or fabricated state. Source/model/section/inertia/state/packet guards
remain active. Conservative current-rest evaluation requires committed material
history to remain unchanged and strictly within an elastic branch; active yield
boundaries fail closed rather than receiving an arbitrary plastic modal tangent.

Use existing original compliance, kinematic, geometric and physical consistent
kinetic factors. The full accepted physical residual is reconstructed and the
actual nodal dead load subtracted exactly once. The numerical control row and
load column are excluded from physical stiffness; the controlled node remains
free for stability perturbations. Numerical nodal rotation traces retain exactly
zero inertia and their algebraic stiffness is not dropped from the factor chain.

Tests: exact virgin equality with independently issued force-owned factors;
checkpoint/program/model/inertia/cancellation/packet mutation rejection; reject
arc/force/altered controlled records; no implicit control support or invented
mass. A small actual two-macro arch at crown drop .003 checks native controlled
replay, recovery and full stationary Schur equality at1e-11. This is interface
validation, not a critical-point convergence or arch qualification campaign.

Freeze before tests. One thread/24GiB/600seconds perchild, at mostthreeworkers,
1800seconds perwave, unchanged120sCPUidle/nativeContext. No automatic retries.
Run the new suite twice in fresh directories and preserve its scientific records
byte-identically. No mass normalization, tolerance changes or spurious mode
removal. An independently anchored actual critical-point programme is a next
scientific gate, not silently executed by this bridge test. FullGE-B3 goal,
independent review and objective beam-shell connection remain incomplete.
