# F03 independent continuum comparator: exploratory v1/v2

21 September 2026. **Not registered qualification; F03/G0B remain open.**
The independent classical plane-stress Q4/CST panel and conventional
two-node Timoshenko beam use the same geometric four-sample reference
footprint, section constants, prescribed panel boundaries and smooth/sine
load families as the candidate. This is a different shell/beam operator,
not a reuse of the native B3/E4 candidate KKT. The beam stiffness is an
exact static nodal map, but the v1/v2 load and gap use *affine nodal*
interior fields and finite station equality. It is not the continuous
beam-to-shell line law or an exact interior Timoshenko continuum field.

The first exclusive screen is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-continuum-v1/`,
source commit `4d8fa98`, 32 records, JSONL SHA-256
`1280ae41523081667096a459a187465883e6889095c77757ae6033000c3f7595`.
The raw mixed-unit saddle solve reached a largest absolute tie residual
`6.54e-10` and largest relative energy imbalance `1.33e-6`; it cannot be
used as a numerically certified target. Preserve it as a failed numerical
screen.

The dual-consistently scaled source and expanded single-use runner are at
commit `7d8470e`. The second exclusive root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-continuum-v2/`:
44 JSONL records, SHA-256
`630e8e835231c93d2a53394f24574b3966aaf9aab6cda1a069f272b89a45b43f`.
Its manifest binds Python/NumPy/SciPy, source and runner hashes, the
2/4/8/16 joint series, fixed two-row panel screens, and fixed `N_b=8`
reaches at `N_s=1,8,64`. The run's largest relative equilibrium residual
was `7.77e-14`, largest absolute imposed tie gap `4.07e-20`, largest
relative work imbalance `8.91e-14`, and largest absolute two-sided trace
work discrepancy `7.11e-15 J`. The bounded row-normalized constraint Gram
eigen-ratio bottomed at `0.02987`; this is a row-rank diagnostic, **not**
a norm-scaled native signed inf-sup result. The reported discrete affine
gap maxima use all beam and shell trace breakpoints, including S3 diagonal
crossings; they are not rigorous floating-point enclosures or continuum
field maxima.

Numerical balance does not imply physical adequacy. At fixed `N_b=8`, the
coarse Q4 `N_s=1` smooth-load tip response is effectively zero despite a
full-rank row diagnostic, whereas `N_s=64` gives `2.25142e-5 m`; S3 changes
from `8.32058e-7 m` to `2.13506e-5 m`. The imposed station gaps vanish in
both cases. The joint-width Q4 smooth tip at `N_s=2,4,8,16` is respectively
`1.58512e-5`, `2.41483e-5`, `2.62181e-5`, `2.90698e-5 m`; no converged
target follows from that series. The off-station affine gaps reach order
`1e-6 m` despite tiny imposed gaps. Different Q4 and E4-PL element maps,
beam interior/load idealization and unresolved shell-width refinement
remain material sources of discrepancy.

Independent read-only mechanics/code review validated the classical panel
assembly, rigid four-sample patch and support sign/balance checks. It found
the exact-nodal-stiffness versus affine-load/trace inconsistency, cautioned
that knot maxima only certify the declared mathematical affine trace, and
requested signed stability and an independently converged physical target.
The v2 change addressed raw-unit conditioning, explicit trace work, row
diagnostics and fixed-side inventory. It did **not** remedy the mechanical
idealization or establish convergence. No candidate multiplier space is
selected or promoted from this record.
