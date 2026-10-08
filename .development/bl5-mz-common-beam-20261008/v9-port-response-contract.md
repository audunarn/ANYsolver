# V9 two-sided body-port response contract (development only)

Decision sought: whether the retained native beam half-cell body has materially
different incremental cut-section compliance from a resolved C3D20 bar under
the same six-component resultant. V5's 7.24 body-work ratio does not answer
this because its native and resolved bodies have different primal spaces.
V7 established a balanced discrete solid cut port; V8 only verified a rigid
dual-work lift.

For each of two independent halves, constrain the six physical rigid-section
coordinates of its remote face. Do not constrain solid-face warping. Apply
equal and opposite cut actions with center (0.5, 0, 0.04) m, first using V7's
balanced resultant and then a pure Mz control. C3D20 side stiffness is assembled
from the saved model's unchanged local B-transpose-D-B operators. The face
coordinate is the consistent L2 projection of its Q8 trace onto rigid
translations/rotations; its applied nodal load is the exact dual of that
projection. Native side stiffness uses each virgin B3 local tangent, fixing
the remote nodal pose and loading cut translation plus that side's retained
half-cell rotation. No original V5 P0 or tip load is applied in this increment.

Check side equilibrium, remote pose, applied/strain work and the dual map.
Record each side's pose and work, and the sum as incremental relative
compliance. A large difference implicates body/retained-port compliance under
these new supports; a close response redirects investigation to V5 loading,
trace or seam work. Neither outcome numerically allocates V5's ratio or
selects a BL5 law. This six-port comparison cannot represent V7's
zero-resultant cut warping action; that limitation must be assessed before
using the result to explain V5.

Authority: user approval on 8 October 2026 covers this needed prospective
development check. One bounded batch, at most two attempts for compatible
source repair, 180 cumulative process-wall seconds with 60 seconds held for
final verification, 30 seconds per child, 2 GiB process-tree RSS, CPU0, one
numerical thread, JIT disabled, one numerical job. Each attempt retains full
stdout/stderr, receipt and output. No formal F03, external solve, V5/V6 rerun,
criterion change, multiplier choice or production qualification is authorized
by this contract.
