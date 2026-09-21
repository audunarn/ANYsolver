# F09 physical B2 definition: preparatory contract

21 September 2026. Source predecessor `3cef6909a4bcf6bc5d1c1a63738bfcd57a2c25d4`.
This is a private definition and focused verification record, **not an F09
registration, execution, or acceptance**. The existing public B2 route and
all historical selectors remain unchanged.

`_b2_physical_linear_definition.py` owns straight reference positions,
distinct model node IDs, member/source/section IDs, the declared physical
local y axis, SI convention, and a scalar or generalized sectional stiffness
from the previously reviewed local operator. It projects admitted roundoff
in the axis to an orthonormal local frame and returns fresh transform arrays.
The scalar section retains its physical inputs; a coupled generalized section
has separate identity. Reversing member direction while preserving local y
changes the local z axis, so a physically equivalent generalized section
requires an explicitly reoriented stiffness tensor. The definition does not
silently infer or transform that tensor.

Optional mass and geometric data have separate source identities. The mass
record owns a finite symmetric 6×6 kinetic matrix per unit length at its
declared local origin. Exact-rational positive-semidefinite admission of the
binary64 entries allows a massless rotation, rejects a negative direction,
and does not introduce fictitious inertia. The geometric record owns section
origin, centroid and shear-center positions; its polar datum is optional,
never inferred from static stiffness. **Neither record presently enables
modes or buckling.** Algebraic PSD does not establish that arbitrary entries
are the mass of a physical rigid section. Physical realization, axis reversal
of both records, mass and geometric operators, and spectral preflight remain
open mechanical contracts.

The private-module focused run on Python 3.13.9 passed 19/19 in 0.80 s,
including the prior local operator tests, ownership/mutation, frame rotation,
explicit generalized-section reversal, semidefinite mass and invalid inputs.
The run deliberately imported the modules without the broad package root;
it is not an installed-wheel test. Independent read-only review found the
four targeted frame, reversal, optional polar-datum and exact PSD corrections
sound at this definition layer. Subsequent SI and malformed-ID admission
checks were verified in the final focused run. No independent physical-mass
qualification or graph execution follows from this review.

F09 remains **IN_PROGRESS**. Next freeze an independent high-precision
one/two-member graph registration spanning scalar and coupled sections,
adversarial weak modes, frame changes, unit changes, station work and support
reactions. Resolve physical mass/geometry semantics before F12/B14 and public
profile admission. F03's line multiplier choice remains unresolved and bars
the production G1 route regardless of this preparatory B2 work.
