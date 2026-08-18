# E4-PL-Q1A exact local algebra

## Frozen stationary system

Let `p=T5^T*q` be the twenty physical coordinates and
`d=QD^T*q` the four nodal drilling coordinates. The source-ordered WG fields
are `z=[sigma_hat_1..14,epsilon_hat_1..21]`; the multiplier fields are
`tau=[tau_0,tau_r,tau_s]`. With thickness `t`, the complete element functional
is

```text
Pi(q,z,tau) = 1/2*z^T*D*z + p^T*Q*z
            + tau^T*B*q - 1/(2G)*tau^T*M*tau
            + epsilon_hg*G*t*A*(gamma*d)^2 - q^T*f.
```

`D`, `Q`, `B`, and `M` are assembled at the same four positive source Gauss
stations. The internal ordering is exactly 35 WG fields followed by three PL
fields. Its block and external coupling are

```text
D38 = diag(D,-M/G),
Q38 = [T5*Q, B^T].
```

The source block has `rank(D)=35`. Positive Jacobians make `M` positive
definite, and `G>0`, so `rank(D38)=38`. Stationarity gives

```text
z*   = -D^-1*Q^T*p,
tau* =  G*M^-1*B*q.
```

Eliminating those fields from the same functional gives

```text
K0   = -T5*Q*D^-1*Q^T*T5^T,
K_PL =  G*B^T*M^-1*B = G*C^T*M*C,
K_hg =  2*epsilon_hg*G*t*A*H^T*H,
H*q  =  gamma*d,
K24  =  K0 + K_PL + K_hg.
```

The exact reference constructs `D38` and `Q38`; direct Schur elimination
equals `K24`. This establishes stationary energy, residual, virtual-work, and
symmetric-tangent parity without an appended post-condensation matrix.

## Four-mode completion and physical Schur theorem

Collect the numerical mismatch rows as

```text
L(p,d) = A*p + R*d,
A = [C*T5; 0],
R = [C*QD; gamma],
W = diag(G*M, 2*epsilon_hg*G*t*A_area),
K_num = [A R]^T*W*[A R].
```

The first three rows of `C*QD` are the first three scaled Q1 Hadamard rows,
independent of geometry. The WT gamma row is the fourth Hadamard row plus a
linear combination of the first two nonconstant rows. Equivalently,
`gamma*h4=1` while the first three rows annihilate `h4`. Hence

```text
rank(R)=4
```

for every source-admissible positive-Jacobian planar Q4; no observed rank or
benchmark selects a coefficient.

Because `W` is positive definite and `R` is square and nonsingular,

```text
Kdd = R^T*W*R > 0.
```

In `(p,d)` coordinates the complete condensed tangent is

```text
Kpp = K5 + A^T*W*A,
Kpd = A^T*W*R,
Kdd = R^T*W*R.
```

Using

```text
R*(R^T*W*R)^-1*R^T = W^-1
```

gives the exact local identity

```text
Kpp - Kpd*Kdd^-1*Kdp = K5.
```

Thus free local drill coordinates introduce no physical Schur stiffness. This
does not yet prove assembled non-intrusion when supports or MPCs constrain
drill coordinates; that is a Q1B question.

## Rank, nullspace, and positivity

The WG core is PSD, has rank fourteen, and has exactly six physical rigid
modes in twenty coordinates. Its 24-coordinate embedding has those six modes
plus four coordinate-drill null directions. `K_num` is a Gram form and has
rank four on that ten-dimensional core kernel because `R` is nonsingular.
Therefore

```text
rank(K24)=18,
nullity(K24)=6.
```

The six null vectors are the three translations and the three matched rigid
rotations. For the in-plane rigid rotation, translation-only spin and common
drill have opposite constant mismatch; their sum is exactly null. The
alternating drill is invisible to the three PL rows and is controlled only by
the WT gamma row. No seventh drill mode and no negative numerical-energy mode
remain.

The independent exact reference evaluates all matrices in
`Q(sqrt(3))`. For each frozen geometry it proves:

```text
rank(F,Gq,H,D,K5) = (14,14,21,35,14),
rank(C,R,D38,Kdd,K24) = (3,4,38,4,18),
nullity(K24) = 6,
LDL(Kdd) has positive rational pivots,
Schur_d(K24) = K5,
Schur_(z,tau)(uncondensed system) = K24.
```

The unit-square `F`, `Gq`, `H`, `D`, and `K5` values exactly equal the
accepted E4-0 matrices. The affine-skew control and both non-affine probes pass
the same identities. Numerical SVD is neither used nor needed to classify.

## Loads, supports, reactions, and recovery

Eligible physical loads have `QD^T*f=0`. Primary support/MPC rows satisfy
`a*QD=0`; a full six-coordinate clamp is only a separately reported hostile
case. Direct drill moments and prescribed nonzero drilling rotations are
excluded.

At stationarity, only `z*` enters WG physical resultant and stress recovery.
The following are kept as separate records:

```text
WG physical N/M/Q and stress,
projected total reaction,
projected PL/hourglass reaction,
tau, C*q, gamma*d, U_PL, U_hg.
```

The last line is numerical diagnostic data and cannot enter material history,
yielding, fatigue, or a DNV code check. The material interface consequently
requires only the existing elastic material data and thickness; density is
metadata unused by Q1A.

## Q1A boundary and retained component ledger

The exact algebra closes the element-local rank, nullspace, positivity,
stationarity, physical-patch, support-projector, and recovery-separation
screens on the two G0 controls and two fixed G1 probes. Those passing component
results are retained even though the later exact covariance gate fails.

Under the preregistered fixed-common-frame D4 action, K5 and K24 each pass all
eight operations on the unit square and tapered-skew probe but only four on the
affine-skew parallelogram and trapezoid. The independent complete-orientation
reversal fails on the same two asymmetric cases. Therefore the scientific
terminal is `NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE`, not a provisional Q1B GO.

No continuous G1 domain, mesh-uniform coercivity, refinement non-intrusion, or
locking work is authorized. Production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
