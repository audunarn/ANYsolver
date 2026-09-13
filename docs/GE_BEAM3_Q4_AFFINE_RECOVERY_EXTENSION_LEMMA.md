# Registered affine-recovery extension lemma: source derivation

Status: IMPLEMENTATION DERIVATION PENDING INDEPENDENT ACCEPTANCE. This is not
numerical evidence, a general geometry theorem, or full MO16/G3c qualification.
It supplements the accepted three-fixture exact certificate and the numerical
design contract. The implementation starts at 8767dbaaf4003daa24369628a1e6e119a642e0bf,
tree e8292d1d5e56647107a1ec4372e7a7a7d27fa922. The source hashes and accepted exact
certificate identities are those in GE_BEAM3_Q4_AFFINE_NUMERICAL_RECOVERY_CONTRACT.md;
none is replaced here. No mechanics was executed to prepare this derivation.

## 1. Statement and limited domain

Let X be one of the exact square, rectangle or rhombus fixtures, and form an
ideal registered reference by a positive scalar lambda in {1/100,1,10}, a proper
isometry X -> X W^T+a, and a registered D4 permutation. Thickness stays 1/10,
E=100, nu=1/4; the material is scalar, homogeneous and virgin. The graph pair
is the square, while the graph loop is the rectangle translated by (0,1/2,0).
Graph renumbering and insertion order do not change the physical reference;
their prescribed rigid transformation and connectivity reversal are covered
by the same identities. Physical director reversal is a separate involution,
not connectivity reordering.

The proposed conclusion is that, on the centered symmetric-covariance image
of the proper-polar chart, the physical energy difference

    Phi(d) = 1/2 sum_g w_g (M_g d+n_g(d))^T C (M_g d+n_g(d))
             - U_source,physical(d)

vanishes for these ideal recipes, with the original 35-variable source
stationarity, not a changed operator. The proof below reduces its linear,
cubic and quartic parts to source identities and the already certified
three-fixture restricted cubic identity. It does not infer an unrestricted
affine theorem from those specimens. Independent acceptance of each algebraic
step is a prerequisite to numerical acceptance.

## 2. Original linear stationary identity

Write the source 35 equations as

    H = [[0,F^T],[F,G]], b = [B_sigma;0],
    F = -sum w N_e^T N_s, G = sum w N_e^T C N_e,
    H [beta;alpha] + coupling^T T^T d = 0.

Thus M_g d=N_e,g alpha and stationarity in alpha gives
G alpha = -F beta. The beta equations give the compatible weak constraint.
Multiplying both equations by beta and alpha proves that the stationary
quadratic energy is 1/2 alpha^T G alpha. Consequently

    K_physical = sum_g w_g M_g^T C M_g

as a full 24-coordinate identity wherever the unchanged source stationary
system is invertible. This assertion is algebraic stationarity, not a claim
that N_s beta equals C N_e alpha at each station. The latter remains an old
mixed-equilibrium diagnostic. No PL/hourglass coefficient enters H, G or C.

For the scalar section, C=diag(A,D,As). Membrane, curvature and transverse
shear columns occupy separate row families in both source field matrices;
there is no membrane/bending material coupling. Only the membrane part of
n is nonzero. Therefore the energy difference has no new bending/shear
nonlinear term, and its quartic part cancels identically between new and old
potentials. Its sole possible nonlinear difference is

    Phi_3(d) = sum_g w_g [(M_g d)_mem - B_m,g d]^T A n_g(d),

with the center-to-numbered engineering frame transform applied consistently.
The accepted exact certificate establishes this cubic polynomial is zero
on each of the three 18-dimensional chart images.

## 3. Positive scale, including fixed-thickness bookkeeping

Let Q_lambda have lambda I3 on each translational block and I3 on each
rotational block. For X_lambda=lambda X and d_lambda=Q_lambda d, reference
frames do not change. Bilinear geometric coefficients xr,xs,yr,ys scale by
lambda; Jacobians and every station measure scale by lambda^2. r_bar,s_bar
and jc/J stay unchanged. The tensor-transform matrix scales by lambda^2,
and the shear-transform matrix by lambda.

Explicit source-field column rescalings are

    D_s=diag(I8,lambda^2 I4,lambda I2),
    D_e=diag(I8,lambda^2 I4,lambda I2,lambda^2 I7),
    N_s,lambda=N_s D_s, N_e,lambda=N_e D_e.

These nonsingular basis changes preserve the actual spaces and stationary
constraints. The compatible operator obeys

    B_lambda Q_lambda = R_lambda B,
    R_lambda=diag(I3,lambda^-1 I3,I2).

The separate row families and scalar block-diagonal C imply the corresponding
stationary solution has

    M_lambda Q_lambda = R_lambda M.

This follows by substitution in each membrane, bending and shear block of
the transformed stationary equations; no rescaling of physical thickness or
material is made. Constant and varying columns within each row family are
changed by D_s/D_e, and row-family R_lambda commutes with C. Uniqueness of
the stationary solve fixes the transformed solution.

Thus membrane and shear energies for correspondingly scaled translations
carry lambda^2; bending energy carries lambda^2*(lambda^-1)^2=1. This is
coordinate/response scaling, not units conversion. In particular, the
membrane nonlinear slope Gw,lambda Q_lambda=Gw is unchanged, so n is unchanged.
The cubic difference is precisely lambda^2 times its base value, and the
quartic cancellation remains exact. This reduction concerns Phi, not a
single common scalar scaling of the whole bending-plus-shear stiffness.

The six image constraints are mean translation zero and
skew(sum d_i Xc_i^T)=0. Under Q_lambda they scale by lambda and lambda^2
respectively. Their kernels are related by Q_lambda. If Z and Z_lambda are
the deterministic RREF nullspace matrices, there is an invertible 18x18
coordinate change B with Z_lambda B=Q_lambda Z. One obtains B by taking
the free-coordinate rows of Q_lambda Z because those rows of Z_lambda are
the identity. Hence polynomial vanishing on image(Z) transfers to
image(Z_lambda), independently of which leftmost pivots RREF selects.

## 4. Translation and proper coordinate re-expression

Reference centering removes a exactly. Under X' = X W^T+a, x'=x W^T+a,
the fit is R'=W R W^T and local deformation transforms with nodewise W.
The physical direction and normal also transform with W. In a numbered
material frame, scalar C is unchanged; in global tensor components,
strains and stress resultants transform T' = W T W^T, shear vectors v'=Wv.
Engineering shear and tensor shear factors are inverse work-conjugate
conventions, so their contraction and station energy are unchanged.

The original source field matrices are expressed in the transported
numbered frame. Their component polynomials and station measures are
unchanged. Thus their stationary equations and M are related by the
nodewise external W change, and the same holds for B_m,Gw and n. Image
constraints transform by nonsingular mean-vector and axial-vector maps;
their RREF coordinates change as in section3. This proves invariance of
Phi on the ideal rigid orbit, not literal bitwise invariance of rounded
floating-point arithmetic.

Active common motion is different: X is held fixed, x'=W x+a,
Q_a'=W Q_a and eta'=W eta. Exp(eta')Q_a'=W Exp(eta)Q_a. Its fit satisfies
R'=W R, so d and recovered numbered physical fields are unchanged. Spatial
wrenches and tensor outputs rotate with W. An additive rotation-chart
Hessian is compared through its coordinate connection, not raw equality.

## 5. D4, physical polarity and station order

Each registered D4 action permutes bilinear shape functions and the four
Gauss stations through an orthogonal signed permutation of (r,s). Derivatives
and xr,xs,yr,ys use that same change. The source constants, linear r/s terms
and rs enrichment are transformed together; the r/s exchange swaps their
associated columns. The stress/engineering tensor transforms supply the
dual row transformations. Substitution in the displayed source N_s/N_e
formulas gives nonsingular internal changes of basis and a station permutation,
so H/coupling transform by congruence and M by the corresponding row/external
maps. The compatible operator and quadratic slope tensor transform by the
same physical tensor rules. This is why the actual eight source substitutions,
not a hand-selected station index ordering, must be checked numerically.

For reflected numbering, the source physical-director maps are
E=diag(1,1,sigma), K=sigma E, H_s=sigma diag(1,sigma). All are orthogonal
involutions and act on conjugate strain/resultant components together. They
preserve work with the separately transformed physical frame. Physical
director reversal changes sigma without changing connectivity; curvature
and shear pseudofields are transformed by these source maps, rather than
pretending it is a D4 reorder. Scalar zero-offset C remains invariant under
these block maps. Nonzero offsets, B-coupling and history are not admitted.

## 6. Numerical boundary and obligations

The registry evaluates the exact listed arithmetic recipe in binary64 and
fingerprints the resulting bytes; it never projects/snap-corrects coordinates.
The ideal results above do not say a rounded passive orbit is exactly affine.
The numerical gate must evaluate those actual rounded inputs, retain their
source station measures, and compare all registered energy/force/Hessian,
station/tensor/work and transport quantities with the contract's relative
scales and tolerances. It must not introduce a new exact rank/PSD check on
the third polar singular value, which can have tiny signed roundoff.

Differentiating the identity Phi(d(q))=0 gives D^T grad(Phi)=0 and
D^T Hess(Phi) D+sum_i Phi_,i Hess(d_i)=0. These are the required derivative
sentinels; off-image local force/Hessian equality is not asserted. For the
new 64 station variables, the block inverse and Schur identities follow
from w[[C,-I],[-I,0]] with inverse w^-1[[0,-I],[-I,-C]], and the complete
external Hessian includes both Hess(n) through D and (M+Dn) Hess(d).

Independent review must either accept the foregoing source substitutions
and extensions, or block numerical acceptance pending separately reviewed
exact per-context prerequisites. No specimen may be omitted to avoid that
obligation. General references outside the finite registry, solved graph
histories, nonaffine geometries, generalized/history sections, G4/G5 and
public integration remain open parity obligations. Numerical success alone
cannot erase them or change existing qualification/defaults.
