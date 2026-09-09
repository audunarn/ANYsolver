# Loaded curved-state tangent and spectra development

Parent `41cab78615643764c02a3f24d31b572231114cd7`. No native mechanics,
mass, recovery, section laws, public APIs, package metadata or defaults change.
Goal remains full straight/curved GE-B3 and objective shell coupling; this
step addresses only an independent loaded-state tangent/stability comparison.

## Separate spatial second variation

The public strain/balance context remains Bali et al., DOI10.1002/nme.6994,
[equations 6,7,10,11,15--17](https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/).
The following Exp-chart Hessian and polynomial Ritz specialization are a
same-author derivation, not independently reviewed source equations.

At a current configuration r,Q, vary r by v and Q by Exp(hat(omega))*Q.
Write r_s for the current centerline derivative with respect to reference
arclength. For e=[Q^T r_s-v0;kappa] and a linear coupled section C:

    delta gamma = Q^T(v_s-omega cross r_s)
    delta kappa = Q^T omega_s
    delta^2 gamma = Q^T(omega cross (omega cross r_s)-2 omega cross v_s)
    delta^2 kappa = -Q^T(omega cross omega_s).

In variables [v_s,omega,omega_s], H=B^T C B+G. With physical n=Q(Ce)_force
and m=Q(Ce)_moment, G has blocks:

    G(v_s,omega)=-hat(n), G(omega,v_s)=hat(n)
    G(omega,omega)=sym(n r_s^T)-(n dot r_s)I
    G(omega,omega_s)=hat(m)/2, G(omega_s,omega)=-hat(m)/2.

There is no additional load Hessian for a fixed spatial dead force. This is
an energy second variation, not a spatial residual Jacobian at an arbitrary
nonequilibrium state. Nonconservative spatial moments are not admitted.

The station Hessian is checked against separate 60-digit finite-potential
Exp/Jr series evaluation in all coordinate and pair-sum directions, at 1e-7.
Objectivity and symmetry use 1e-11. Tension/compression signs and zero-stress
reduction are checked explicitly. Ten initial unit tests passed in .31 seconds.

## Loaded continuum reference

Use the existing independently implemented planar arch BVP to resolve crown
drops .01 and .055, then allow full spatial perturbations of each equilibrium.
Use the explicit BVP9 profile (bounded 60 seconds/2000 callbacks) with newly
registered quadrature samples, never interpolation of previously saved fields.
Both ends are clamped; the crown perturbation is free. The physical section is
the nominal diag(1e6,4e5,4e5,80,100,100), with inertia
diag(1,1,1,.02,.01,.01). This is not an exact-dyadic section certificate.

The Ritz space has a continuous crown trace plus separate Legendre bubbles
on the two halves, so the point-load location does not force a globally
smooth derivative. Compare local degree12/48-point and degree16/64-point
quadrature, requiring eigenvalue agreement within 1e-7 normalized by
max(1,abs(lambda)). Reference residuals use 1e-8; native signed-Ritz and
spectral residual checks remain 1e-11. No tolerance is tuned to the results.

## Native input and interpretation

Use the preserved four-macro checkpoint, 95786 bytes, SHA-256
bcf90a0eca2923ee04ab00bf61b6e1eabdac40779671f90666bdbc2964420a1f.
Its original invocation failed serialization and remains failed. Replaying
its complete canonical accepted state chain as new diagnostic input does not
repair or reclassify that history. The new worker verifies byte identity and
native replay before deriving prefixes for drops .01 and .055.

The existing controlled-fibre spectral path holds the accepted spatial load
fixed and removes the continuation constraint. It freezes accepted plastic
coordinates for physical perturbation; no history advance or nonlinear solve
is permitted. Native and continuum loads may differ at the same prescribed
crown drop. Compare and report their eigenvalues, signs and loads rather than
pretending to have proved identical equilibrium branches or buckling factors.

## Bounded single invocation

Two new continuum equilibria, four reference spectra and two native spectra.
One child, one numerical-library thread, 24 GiB process-tree limit, 600-second
wall limit and 120-second inactivity limit; existing shorter constructors
remain bounded. Preserve partial artifacts externally, with an 8 MiB per-file
bound for dense reference matrices. No automatic retry. Canonical publication
requires complete raw artifacts and summaries, unchanged source/input and
complete process-tree cleanup. Negative roots are retained. Successful process
completion is development evidence, not qualification or a buckling-factor GO.
