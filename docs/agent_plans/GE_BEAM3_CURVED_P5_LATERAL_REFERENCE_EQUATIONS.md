# P5 continuum lateral second variation — development equation map

Parent: `09d7fb1cfeb73620efc2afe8882684bc7c2e7ca2`, tree
`ab3265ab0f63ab7bfcd468b4e6e681dd1cdb1c85`. This is a separately reconstructed,
same-author research reference, not independent review or qualification.
Existing discrete operators and completed nonlinear proofs remain unchanged.

The continuum starting point is the material strain/curvature and quadratic
rod energy in [Bali et al., DOI 10.1002/nme.6994](https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/),
equations 10-15, with spatial balance 6-7. The HTML equations were inspected
again. No new PDF hash authority or reproduction of the paper's discretization
is claimed. The following lateral specialization/second variation is derived
here, not copied from the discrete beam or claimed as an equation in the paper.

## Spatial perturbation and exact quadratic form

Use reference arclength s. On the planar base state, the physical director
columns are (cos(theta),sin(theta),0), (0,0,1), and
(sin(theta),-cos(theta),0). Write r'=(vx,vy,0), spatial force (Fx,Fy,0), and
spatial moment (0,0,M). The base is the existing separate planar continuum BVP,
not interpolated discrete coordinates or discrete recovered resultants.

Let the lateral perturbation be delta r=(0,0,z), spatial rotation w=(a,b,0),
with D(epsilon)=exp(epsilon*hat(w))*D and r(epsilon)=r+epsilon*delta r. The
initial curvature is fixed. Differentiating material strain and curvature:

    delta e = D^T (delta r' - w cross r')
    delta2 e = D^T (w cross (w cross r') - 2*w cross delta r')
    delta k = D^T w'
    delta2 k = -D^T (w cross w')

The exact second derivative of stored energy is the elastic quadratic form
in the first variations plus N dot delta2 e + material-M dot delta2 k.
Spatial dead forces contribute zero second variation. For diagonal sections,
only lateral shear G, torsion T and lateral bending B enter its elastic part:

    g = z' - vy*a + vx*b
    Q = G*g^2 + T*(cos(theta)*a'+sin(theta)*b')^2
        + B*(sin(theta)*a'-cos(theta)*b')^2
        - Fy*vy*a^2 - Fx*vx*b^2 + (Fx*vy+Fy*vx)*a*b
        + 2*(Fy*a-Fx*b)*z' - M*(a*b'-b*a')

Do not drop the prestress or moment terms. Axial and in-plane bending
stiffnesses still affect the base state; they are not removed from the rod.

For u=(z,a,b), write Q=u'^T A u' + 2*u^T B0 u' + u^T C u.
The derivative block A is diag(G, rotated diag(T,B)). All unspecified entries
of B0,C are zero; indices below are component names:

    B0[a,z]=-G*vy+Fy; B0[b,z]=G*vx-Fx
    B0[a,b]=-M/2; B0[b,a]=M/2
    C[a,a]=G*vy^2-Fy*vy
    C[b,b]=G*vx^2-Fx*vx
    C[a,b]=C[b,a]=-G*vy*vx+(Fx*vy+Fy*vx)/2

Define p=A*u'+B0^T*u. The zero-second-variation (Jacobi) equations are

    u' = A^-1*(p-B0^T*u)
    p' = B0*u'+C*u

Their 6x6 first-order matrix must be Hamiltonian; preserve its symplectic
bilinear form. Integrate across each half separately, with continuous u,p at
the crown. The original crown force is spatial dead, so its second variation
adds no jump term. Both ends impose z=a=b=0. Starting with u_left=0 and three
independent p_left columns, the upper-right transfer block maps to u_right.
A singular block is a candidate lateral neutral state; its determinant sign
alone is not a complete inertia count or proof that this is the first root.

## Straight checks and bounded development scope

For an unstressed straight line of length L, the transfer boundary block is

    [[L/G-L^3/(6*B), 0, -L^2/(2*B)],
     [0, L/T, 0],
     [L^2/(2*B), 0, L/B]]

For straight compression P, stretch lambda=1-P/EA, the clamped bending neutral
condition derived from these equations is
P*(1+P*(1/G-1/EA))=4*pi^2*B/L^2. It tends to Euler as shear/axial stiffnesses
increase. Verify this limit and the sign change, not merely a successful IVP.
Verify the quadratic form separately through rational vector/cross-product
first/second variations, including unequal T/B and nonzero M,Fx,Fy.

Use bounded DOP853 binary64 transfer integration, registered profiles IVP9 and
IVP11, a callback cap and cooperative wall guard. These are independent
accuracy comparisons, not retries of failures. Check constant coefficients
against a separate matrix exponential and retain the symplectic error.
Reconstruct the mirrored base with Hermite slopes from its continuum ODE;
compare stride-one/stride-two interpolation. No discrete mechanics imports.

Initial development evaluates the two preserved last-step crown displacements
0.03717258569148828 and 0.044820372353098756, using freshly solved continuum
base states. A determinant sign change may support a later bounded root
location, but must not be reclassified as full spatial buckling qualification.
Any failure is retained; no automatic retry or extension to a large campaign.
The original resource request and all input proofs remain untouched.

## Pre-root observations and explicit interval extension

The small straight critical-load test initially failed because the reporting
code divided each transfer boundary column by that column's current norm. A
column approaching zero at a neutral state was thereby amplified, concealing
the singularity. This was a diagnostic normalization defect, not a change to
A,B0,C or the rod equations. Replace it by one common nonvanishing matrix scale
and add zero/near-zero column mutation tests. The corrected suite passes.

Both initially selected continuum arch states have positive boundary
determinants. At d=0.044820372353098756, IVP11/stride-one gives approximately
0.00020536863336, rather than a neutral state. The separate endpoint d=0.05 was
then explicitly evaluated once and gives approximately -0.00090595055156.
No existing failed test was retried and no discrete path was recomputed.

Preregister the next small diagnostic as exactly twenty bisections inside
[0.044820372353098756,0.05], with a whole-operation cooperative limit of thirty
seconds. Recompute each continuum base with BVP9; use IVP11 and separately
compare stride-one/stride-two interpolation. Require an observed sign bracket
and final width at most 1e-8; never search outside the interval or extend a
failed budget automatically. Retain all scalar iteration records and both
endpoint continuum fields/transfers. A failed operation retains its completed
trace and no completed root record. This is numerical root location, not a
rigorous interval enclosure, uniqueness proof or accepted element gate.

Every output remains research-only, production_qualified=false, with
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. General 3D sections, initial spatial
curves, dynamics, production parity and independent review remain open.
