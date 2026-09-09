# Separate spatial continuum comparison

Parent2e03bd0f2aa93dc65d581e50e1c13c91861a051a. Research only; no src,
mechanics, state, recovery, defaults or historical evidence changes.

The starting theory is Bali et al., DOI10.1002/nme.6994, equations6-7,
10-11,15-17. Publisher HTML inspected2026-09-09:
https://onlinelibrary.wiley.com/doi/full/10.1002/nme.6994
PMC mirror returned a browser challenge; publisher equations were accessible.
No PDF/source packet freeze or independent author review is newly claimed.

## Derived reference, not the published FV discretization

Let D be absolute director rotation, n,m spatial internal force/moment, q its
scalar-first unit quaternion. Reference curve r0=(X,.1(1-X^2),0), with first
director its tangent, second+z, and right-handed third. J0=sqrt(1+.04X^2),
initial material curvature k0=(0,-.2/J0^3,0). With unchanged section diagonal
C=(1000,400,400,.02,.01,.02), compute N=D^T n and M=D^T m. Derived ODE:

    r_X=J0 D(e1+N/C_axial_shear)
    q_X=(J0/2) q*(0,k0+M/C_torsion_bending)
    n_X=0
    m_X=-r_X cross n

The first two express material strain/curvature; the latter two enforce
spatial balances. Quaternion multiplication is independently written here;
no ANYsolver rotation, element, tangent, recovery or cache imported. All four
quarter intervals are simultaneous13-state blocks in SciPy collocation.

Left end fixes3positions and4quaternion components. Right end fixes3positions
and3relative-quaternion vector components. At quarter interfaces, all13states
are continuous except the crown force jump n_right-n_left=(0,P,0). Moments
remain continuous. An extra z(-.5)=amplitude condition determines P, with no
external lateral force. These53conditions match52state functions+1load unknown.
Unit quaternion norm, boundary and off-mesh differential residuals are checked.

Saved discrete fields ONLY initialize the collocation iteration; they do not
define its ODE, accepted reference fields or force. Input archive42-entry
manifest ed4f312a75fd6f91e6e7ead0634235a376950aa750ba76bd8cfcfc36ec462d9c
binds all four prior signed-amplitude diagnostic solutions, immutable.

## Bounded verification

Equation tests: curved stress-free shape, explicit planar specialization,
spatial force/moment first integral, arbitrary rigid spatial covariance,
boundary/jump dimensions/sign and no discrete-mechanics imports.

First one positive-small BVP7 smoke. If resolved, separately run BVP9 and both
amplitudes/signs as accuracy comparisons, not retries of a failed profile.
BVP7:tol1e-7,max1025collocation nodes; BVP9:tol1e-9,max4097. Each operation
max2000callbacks and60seconds. Outer processes600seconds,24GiB,one numerical
thread,max3workers,1800seconds/wave. No automatic retries/extended bounds.
SciPy's numerical collocation Jacobian belongs only to the continuum reference;
it never replaces the production analytic tangent. Binary64, not multiprecision.

Check off-mesh ODE and quaternion norm within10*profile tolerance, boundary
residual<=1e-11, and64/128energy quadrature relative agreement<=1e-8. Compare
load, full nodal displacement, all160station resultants in the section energy
norm and strain energy. Report each error and whether all are below2%; a false
flag is not rewritten or hidden. No discrete operators are rerun or adjusted.

Two profiles agreeing is not an exact or interval certificate, branch uniqueness
or independent authorship review. Physical loading-path/continuation authority
and full postbuckling qualification remain open even if comparisons pass.
Full GE-B3 programme remains ACTIVE including beam-shell connections.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. No public selection, merge or release.

## Preserved validation-grid incident

Initial4d10de1 BVP7/BVP9 solves and tight replicas completed, with all four
engineering comparisons below2%. Same-author review found the fixed257-site
differential check sampled only collocation nodes/midpoints when BVP9 refined
to384intervals. Its near6e-14residual therefore is not independent off-mesh
validation. Original solutions, comparisons, receipts and old audit are
preserved as initial diagnostics, not promoted as corrected validation.

Successor changes ONLY validation sampling: two interior Gauss sites in every
actual collocation interval, fractions(1+/-1/sqrt(3))/2. These are explicitly
not nodes or midpoints. Test uniform64/384interval and nonuniform grids.
All ODE, boundary equations, solver profiles, source fields, tolerances and
engineering comparisons remain unchanged. Metadata names this validation
policy and exact site count. Use new frozen source/exclusive output directories;
never edit original output or rerun a consumed helper in place.
