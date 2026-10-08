# G0 F03 registered signed weak-mode diagnostic v1

21 September 2026. Register one bounded, source-level **exploratory
mode diagnosis**, not a multiplier selection or F03/G0B qualification.
Source `scripts/probe_b3_ge_e4_pl_g0_f03_weak_mode_v1.py` imports the
frozen native retained fixture, shell trace, exact coupling rows and
trace-dual/signed-normalization helpers. Its nine source/helper hashes,
imported ANYsolver path and numerical dependencies enter a manifest.
Exclusive output root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-weak-mode-v1/`;
use a separate explicit writable Numba cache and one BLAS thread.

Run the same ten Q4/S3-V2D planar meshes as trace-dual v1: joint
`(Nb,Ns)=(4,4),(8,8),(16,16)` and fixed Nb=8 with Ns=1,64. Evaluate
K4 and the genuinely different local-discontinuous-dual row span, for
twenty signed modes. The bounded dense KKT has at most 1,200 rows.
No physical load is applied: this is an operator singular mode, not a
displacement solution, limit point or observed instability.

The primary multiplier Gram is the same exact **discrete trace-image**
`R=C_s G_s^+ C_s^T` at relative graph-eigenvalue cutoff `1e-12`, with
the same kernel-annihilation and full-rank checks. Use the signed native
retained factorization `K=T^T diag(K_e,K_rr) T`, with positive primal
metric `H=T^T diag(K_e,abs(K_rr)) T`, and full constraint/dual whitening.
For the real symmetric normalized saddle, select the eigenpair of
smallest absolute eigenvalue. Its absolute eigenvalue must agree with
the frozen trace-dual v1 minimum singular value within `1e-9` relative
(absolute floor `1e-12`); the normalized eigen residual must be ≤`1e-9`.
Failure is recorded as a failed case, not repaired in the same run.

Report normalized physical, positive-retained, negative-retained and
multiplier coefficient fractions that sum to one; reconstruct the physical
variables using the inverse
factorization, retaining the `C_r` trace. Report scaled shell/beam physical
coordinate amplitudes separately (these are **not** additive energy
fractions), the broken graph and constraint gap norms, native yaw jump
amplitudes, nine material-station gap samples, and rowwise multiplier
alternation for x/y/yaw. For the KKT multiplier component and separately
the smallest-absolute signed-Schur eigenvector, split `B^T y` into
positive and negative retained action squares and report their difference
and cancellation ratio. Compare the signed saddle floor with the
all-positive saddle's `(.5*(sqrt(1+4 beta²)-1))` floor based on its
positive constraint inf-sup `beta`: a signed floor smaller than beta
does not alone prove negative-mode cancellation. Orient the otherwise
sign-ambiguous eigenvector
by its largest physical coordinate. Inspect all of these together to
form a mode hypothesis. Degenerate or nearly repeated weakest eigenspaces
require subspace analysis; a single vector does not define a unique
physical mode.

At native cell boundaries a reported station sample follows the fixture's
one-sided cell convention; the separately reconstructed jump is essential.
Multiplier row amplitudes are in units of the declared force-density
scale `F0=1 MN/m`, not display-ready spatial wrenches. Validate the
predecessor hashes and ten-case inventory before creating the exclusive
root. Check both the normalized eigen residual and the pullback of the
reconstructed scaled variables against the same eigenpair at `1e-9`.

Preserve every case and manifest. Post-run review checks source hashes,
case completeness, previous singular-value parity, eigen residual,
mode partition and trace/jump computations. A decreasing signed floor,
even with a localized mode, is finite evidence; no mesh-local multiplier
norm, uniform inf-sup proof, independent converged response or six-channel
torque/shear qualification follows. The adverse physical gaps of K4/local
dual remain. Do not register a new production mortar candidate merely
from modal appearance.
