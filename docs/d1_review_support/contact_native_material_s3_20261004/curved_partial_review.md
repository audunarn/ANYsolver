# Curved partial angular contact — supporting Read scrutiny

Source `78c622de`; same-family `/root/curved_initial_review`. Read-only source and
equation scrutiny; reviewer ran no tests and changed no files. This is supporting
development scrutiny, not independent engineering acceptance.

## Findings and corrections

1. A zero-estimate-only axial safeguard misses a narrow pocket when a broad
   pocket also supplies negative quadrature samples. The implementation instead
   encloses the angular minimum over the whole axial band. A two-end-pocket
   independent polynomial fixture checks explicit non-success.
2. Uniformly negative angular minimum alone misses an endpoint crossing:
   `g(x,theta)=-1-epsilon+x+cos(theta)`. A second truncated arc may appear before
   the first axial station. The implemented support control also encloses both
   angular endpoint signs and the angular maximum sign. A scaled literal
   counterexample checks that this band is unresolved.
3. At exactly zero formulation-owned residual roll, its axis rotation is
   identically I, with zero derivative. Omitting that term from the work support
   derivative bound is valid. Historical whole-patch default bound is unchanged;
   nonzero/twisted reference bounds retain the full conservative expression.

The final review found the reported gaps resolved, with no further consequential
blocker in the inspected changes. The minimum, maximum and endpoint envelopes
share the same axial Lipschitz bound. Root and scalar values use the same bounded
Decimal precision, with exact binary projection before scalar conversion.

For regular contact roots, `k*g_-^2/2` and its first variation vanish at `g=0`.
Moving angular boundaries therefore add no terms through the potential Hessian.
The actual reference material measure, retained rotation work and once-only
spatial tangent conversion remain required; no condensation is introduced.

## Limits

Genuine axial onset/termination or angular topology transitions can remain
unresolved until the finite interval budget exhausts. Current admission is
partial angular contact with continuously fixed topology on each accepted axial
band. Gauss8/16 differences remain error estimates, not rigorous integration
certificates. No coupled owner, path/restart, continuum, engineering, application
or release claim follows.
