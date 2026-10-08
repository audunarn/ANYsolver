# BL5 saved-density body-port development discriminator

This distinct ordinary DEV probe uses the immutable installed native wheel
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291` and
the saved weak C3D20 response. It does not replay either coupled native calibration
or CCX. Historical integration `fdd5c9dd` defines applicability; changing working
product source is not represented as the imported solver. Physics and scientific
acceptance remain reserved to the root owner.

The specimen, +1 N global tip Fz, shell clamps, section data and virgin physical
fibre material are unchanged. Four .25 m P0 supports integrate five channels.
Position rows have units m² and director rows m; their densities have units N/m
and N. Native gap polarity is opposite continuum polarity. At saved continuum
algebraic density lambda_r, physical body loads are
`ell_ref = f - C_ref.T lambda_r` and
`ell_native = f + C_native.T lambda_r`.
The action identity is checked on the previously proven globally representable
supported affine/material-director/rigid bar-section subset. It does not assert a
mapping of arbitrary broken native cell rotations into the continuum field.

Recover continuum shell/beam paired work and energy from saved full K/U, plus all
eight Gauss point face gaps. Zero P0 integrated gap does not imply zero point gap.
For native, solve one RHS per body with the complete unchanged mixed operators.
The shell retains original clamps. The free beam must first have zero work on all
six physical rigid fields, including retained cell spins; otherwise withhold the
solve. Use the explicit gauge `G q=0`, `G=R_rigid.T`, in an indefinite KKT system.
No load projection, artificial stiffness, physical beam support or condensation
is allowed. Reverse congruence scales into physical q/gauge covectors.

Compare body work `W=ell.T q`. Native beam section energy is recovered from the
actual virgin section at retained p after verifying reference-linear material
stationarity `J q_pose = grad Psi*(p)`. The mixed potential `p.k-Psi*(p)` and raw
negative resultant subblocks are not physical stored energy. The finite pose
law is not evaluated as though a reference-linear increment were a finite state.

Before execution, criteria are fixed: original scaled equilibrium and relative
work <=1e-8; physical wrench and gauge covector <=1e-8 at 1 N/1 Nm floors;
work denominator `max(abs(ell.T q),1e-12 J)`; material compatibility and pose gauge
<=1e-9 with reference length1 m. Actual material domain guards remain active.
Full unscaled residuals, physical q, gauge reactions, retained p/strain/resultant
fields and failed calculated diagnostics are preserved. Resource bounds are
600 s/2 GiB process tree, affinity1, effective pools1, JIT off, unforced backend.

Excess beam-port work directs beam/section/trace inspection; excess shell-port
work directs shell/body/trace inspection; comparable work suggests interface
redistribution requires examination. These are effective port compliances, not
isolated constitutive laws. No coupled native response, accuracy, convergence,
inf-sup, release or different-family scientific acceptance follows from this
discriminator. No automatic refinement or new interface basis selection follows.

## Executed outcome: implemented, discriminator obstructed

The five prerequisite controls passed in V1: immutable saved identity/body work,
changed-input refusal, specimen/units, signed supported common work and six-mode
physical balance with a nonzero-load negative. V1 then calculated the shell once
and failed the original active-row equilibrium gate (ratio .01516407975), before
any beam RHS. Its work error3.2803e-12 did not override that failure.

An affected arithmetic repair retained original K, loads, physical q and criteria.
It computes original binary64 K/q/load products with a64-digit reduction and uses
three original-operator physical residual corrections through the same sparse LU.
The ordinary CSR residual is also saved. A separate exact cancellation control
passed. The unchanged five prerequisite functions and original helper identities
are source-verified in `reuse-v2.json`; only full-load output was added to prepare.

V2 still failed, so no further arithmetic attempt or beam solve was launched.
At free shell slot51 (node9, physical theta_x), load is
-4.635199597672408e-12 Nm and the64-digit original-operator residual is
1.4004742064981811e-14 Nm: ratio .0030213892131019282 exceeds1e-8.
The ordinary CSR residual is -2.3490502684057926e-14 Nm. Stored q is binary64
(slot51=-2.75060443017849e-16 rad); no high/low pose or certified whole-chain bound
is claimed. Relative work error2.1568e-16 does not establish equilibrium.
This is failure after one compatible arithmetic repair, not proof that no
higher-precision representation could solve the same mathematical system.

The scalar shell paired work9.818197493163906e-7 J is **CALCULATED_NOT_VALIDATED**.
It must not be published as accepted compliance or used to localize the2.5x gap.
Native beam energy/stationarity/gauge and the completed discriminator remain
unverified; they were withheld by the shell prerequisite failure.

Saved continuum work recovery did pass: shell1.8827514105613064e-7 J and
beam3.20302491928913e-7 J; stored energies are half these pairings to the saved
body-work errors7.4534e-11 and7.0475e-11. Eight point gaps are preserved separately
from zero integrated gaps in `results-v1/saved-fields-preflight.json`.

Compute inventory: two shell calculations (one per V1/V2, each with three residual
corrections), zero native beam RHS, zero coupled calibrations, zero external runs.
One V2 harness filename failure occurred before any child launch; its source and
failure record are preserved. V1 has5PASS/1FAIL; V2 has1PASS/1FAIL/5deselected,
with the five source-identical prior passes reused. All failed evidence remains.

V2 fail-fast and final runtime records verify imported immutable wheel/CI4:
NumPy2.5.3, SciPy1.18.1, Numba.68.0, llvmlite.50.0; actual loaded pools1,
affinity[0], JIT off/Numba1, unforced backend. Supervisor3.9058 s, sampled tree
peak182673408 B/numerical-or-unresolved max1 are sampled measurements, not peak
resource qualification. V1 and an aborted other-owner material launch raced;
root explicitly reported the shared-slot incident. V1 therefore supplies no
single-job serialization/resource-pass claim. V2 followed explicit terminal
release and exclusive allocation. The numerical slot has now been released.

Next decision belongs to root: the exact quiet-load relative gate remains an
obstruction for this binary64 candidate. Do not project/symmetrize saved densities,
zero quiet channels, fit a floor, accept work closure instead, or infer the cause
of the response difference from the rejected shell calculation. No additional
execution authority is implied by this handoff.
