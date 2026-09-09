# Successor piecewise continuum physical-spectrum reference

Parent b00fae77ad402c59a2e9a530dfd0887e1c704c27. Four additive research-only paths;
no change to production mechanics, failed sine protocol, source equations, sections,
mass, recovery, state, tolerances, API, defaults or versions.

Preserve the prior reference refinement failure:15.3103% rate change with32global
sines despite resolved quadrature. Bind its full archive manifest
57b4cc84c8b26961ccda851d09d454dab706984ce41c0339a3f05318498aadad and reuse only
its successfully checked native100digit spectra, whose exact hashes are in the
worker. Bind the previously accepted complete continuum endpoint polynomials.
Do not rerun native eigenanalysis, owner capture or nonlinear/BVP equilibrium.

## Different reference approximation, same physical problem

On the four frozen segments[-1,-.5,0,.5,1], use six independent spatial H1 fields.
For each scalar component, retain three shared internal interface hats and local
bubbles(1-t^2)P_k(t). Endpoint traces are exactly zero at both physical clamps.
Shared interface values are continuous; derivatives may jump, as allowed for
energy-admissible H1 fields. No quarterspan continuation constraint is imposed.
Preregister4,8,12bubbles per segment: scalar dimensions19,35,51; vector dimensions
114,210,306. The highest local polynomial degrees are5,9,13. These are complete
local polynomial spaces with the stated global continuity/end conditions, not
coefficient fits to native spectra. No displacement or rotation component omitted.

Test exact rational local coefficient rank and representability of
w=(1-t^2)^2 and theta=w' (a straight-reference compatibility identity only).
Check actual numeric basis values/derivatives against that separate Fraction
algebra, nested spaces, interface equality, all six components, end clamps,
arclength derivative conversion and malformed inputs. Curved finite states are
not claimed to have an exact polynomial patch solution.

Retain the existing full-spatial energy Hessian, reference-arclength measure and
physical current-rest inertia diag(I3,R diag(3e-5,1e-5,2e-5) R^T). Do not replace
physical mass by L2 norm. Integrate profiles(128Gauss,4bubbles),(128,8),(128,12),
(64,12) on the same four segments. Use the established Decimal80 spectral
postprocessor, with four fixed bordered eigenpair corrections, on each continuum
trial pencil. Keep original-vector residual, physical mass orthogonality and
bilinear Ritz checks<=1e-11; no altered solver thresholds. Roundoff-only symmetry
and Cholesky kinetic-factor rounding remain explicitly disclosed. This checks
the finite trial pencil, not an interval-certified continuum differential operator.

Keep six signed modes in every profile. Require all profile signs to agree,
8-to12bubble signed-rate difference<=0.5%, and64-to128Gauss rate difference<=1e-6.
Record every profile even when the later refinement test fails. No automatic
extension of degree, quadrature, runtime or case inventory after failure.

## Unchanged native/reference comparison

Use the saved native100digit full438coordinate mode vectors. Reconstruct physical
native velocities from nodal translations and the actual cell rotations, including
the transported parabolic half-cell offset. No nodal trace rotation mass is added.
Use the NEW polynomial coefficient basis to reconstruct the reference306coordinate
field, not the old sine evaluator. Integrate the6x6physical MAC using32Gauss points
on each of48native half-cells and the continuum spatial inertia metric. Require
deterministic one-to-one maximum-MAC matching, matching signs, signed growth/
frequency-rate errors<2%, and MAC>=0.95. Preserve mismatch data rather than tuning
coefficients, relabelling modes or weakening criteria.

## Bounded wave

After targeted tests and clean commit freeze, run positive smoke once. If the
process succeeds, run negative and both replicas in three fresh processes.
Require same-sign comparison bytes identical and every launched tree terminal
before aggregate publication. A reference numerical/refinement failure blocks the
wave; a resolved engineering/MAC mismatch is recorded as a failed comparison.
No native workers are launched and no consumed request/root is reused.

One numerical thread per child,max3concurrent,600s/24GiB child,1800s wave,existing
120s inner reference and CPU-inactivity bounds. Guard source/Python/version
identity before numeric work and after evidence generation; runtime versions are
not a complete environment graph certificate. Exclusive external profile, failure
and comparison outputs; partial or failed profiles never become accepted evidence.

Scientific scope is these six current-rest modes at the two prescribed endpoints.
No full continuum Morse index, finite-velocity dynamics, stable loading path,
independent author review, production qualification, release or activation follows.
The full beam and objective beam-shell connection goal remains open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
