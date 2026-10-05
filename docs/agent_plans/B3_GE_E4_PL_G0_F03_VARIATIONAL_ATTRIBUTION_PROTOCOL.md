# F03 saved-state variational attribution protocol

22 September 2026. Bounded Q4 matrix-action diagnostic following the
independently accepted joint-refinement evidence and its preserved
UNRESOLVED_JOINT_REFINEMENT decision. No equilibrium or Schur solve,
additional mesh level, new physical result or G0B qualification occurs.

## Inventory and meaning

Use the three P1/hybrid/enriched Q4 middle/fine state pairs from
`f03-joint-refinement-v1`, at (Ns,Ny,Nb,Nm)=(8,16,16,8) and
(16,32,32,16). Bind parent registration, adjudication, snapshot hashes,
the seven reused physical source files and dependency versions before
assembly. Read parent files only; copies must remain exactly equal.

Reconstruct physical sparse Kmiddle, Kfine, Cfine and smooth-load vectors
with the unchanged .05m pad halfwidth, physical supports, material and
section definitions. Cfine=[-Cs,Cb] remains paired with the physical
multiplier vector from that family. Its line rows and endpoint rows have
different units; do not use a raw mixed-unit gap maximum for acceptance.

Build a sparse Q4/beam prolongation P. Shell bilinear fields nest under
the exact mesh doubling. Beam axial displacement and independent theta
are P2; transverse displacement is Hermite, so its fine slopes must be
evaluated as actual derivatives of the coarse field. Do not interpolate
the storage vector as a scalar field or impose v'=theta. Preserve existing
supports exactly, including the free beam-root slope. No CST-CB nesting
claim or attribution is included.

Let v=P qmiddle, e=v-qfine and r=Kfine qfine+Cfine.T lambda_fine-ffine.
For Pi_f(q)=.5 q.T Kfine q-ffine.T q, test

    Pi_f(v)-Pi_f(qfine) = A + B + R,
    A = .5 e.T Kfine e = A_shell + A_beam,
    B = -lambda_fine.T Cfine e,
    R = e.T r.

r includes support reactions; e is exactly zero on supported coordinates,
so those reactions do no error work. Retain every signed term and its
absolute joule value. Neither A, B nor their ratios are a continuum
physical-error estimate. B identifies work associated with incompatibility
of the prolonged middle field under the fine constraint space. Do not
interpret it automatically as a constitutive or assembly defect.

## Frozen checks and normalization

Use L0=1m, F0=1MN, M0=F0 L0, U0=F0/(210e9*.07), E0=F0 U0.
Physical translational scales are U0; angular/slope scales U0/L0.
With diagonal Dc,Df define Kbar=D.T K D/E0, fbar=D.T f/E0 and
Pbar=Df^-1 P Dc. Required numerical checks are:

| Check | Limit |
|---|---:|
| Fixed-coordinate and prolongation support leakage | Exactly zero |
| Saved vs recomputed actions in declared work scales | 1e-11 |
| Relative Frobenius norm of Pbar.T Kbar_f Pbar-Kbar_c | 1e-11 |
| Infinity norm of Pbar.T fbar_f-fbar_c / max(1,norm(fbar_c,inf)) | 1e-11 |
| Shell and beam energy preservation separately, abs difference/E0 | 1e-11 |
| External work preservation, abs difference/E0 | 1e-11 |
| Potential identity defect / cancellation-safe denominator | 1e-11 |
| Fine free equilibrium in work scales | 1e-8 |
| Fine constraints / (U0 times physical row measure) | 1e-9 |
| Prolonged off-grid physical fields in coordinate scales | 1e-11 |
| Prolonged off-grid strains in their physical scales | 1e-10 |

The identity denominator is
max(E0,abs(Pi_f(v))+abs(Pi_f(qfine))+abs(A)+abs(B)+abs(R)).
Do not divide by the potentially cancelled net potential change.
Record the signed absolute-joule defect as well as its normalized magnitude.
The load contains a cosine; load preservation is a checked quadrature
result, not polynomial exactness. Retain any discrepancy rather than
silently altering loads or quadrature to obtain parity.

Check stored prolongations at the tensor product of relative Q4 cell
coordinates (.211324865405187,.788675134594813) in each middle shell cell,
and beam positions (.13,.37,.71,.91) in every middle beam element.
Evaluate each field and strain through the corresponding coarse/fine
interpolation at the same physical location. Beam strain scales for
(u',theta',v'-theta) are (U0/L0,U0/L0²,U0/L0); shell strains use U0/L0.
These observed-field checks complement sparse operator pullback and unit
tests; they do not assert an untested full native-element equivalence.

## Artifacts, review and execution

Save owned sparse CSR P,Kmiddle,Kfine,Cfine, load vectors, source q/lambda,
prolonged q, error, Kq/Ke/Cq/Ce/C.T lambda and residual actions.
Archives bind schema, exact case, array inventory, payload digest and
dimensions. Check ZIP inventory and total uncompressed size<=64MiB before
loading arrays; reject nonfinite/incorrect types, malformed CSR and aliases.
The small stored matrices remain sparse. No global dense structural matrix,
inverse, nullspace or factorization is introduced.

Reopen saved bytes for verification. Adjudication must reproduce each
reported scalar from matrix/vector actions and bind source states exactly
to the parent snapshots. Independently inspect source, actions, receipt
identities and physical terms before accepting interpretation. Merely
having a hash is not evidence of mechanical correctness.

Freeze a clean committed candidate after focused tests and independent
mechanics/code review. Execute all three family cases serially using the
existing supervisor, with all five numerical thread caps1 in supervisor
and children. Each case has900s and8GiB sampled-RSS bounds; the launch
cutoff is1200s, after which no new child starts. An already launched child
can finish inside its own bound. Cancellation preserves its receipt and
stops subsequent launches. Do not retry cases or overwrite artifacts.
Each child exclusively creates its case/registration-bound start marker
before importing the numerical implementation or assembling operators.
An interrupted or completed child cannot re-enter assembly through the
private child entry point. Bind that marker to the final artifact event.

The exact runner is
`python scripts/b3_e4_f03_variational_attribution.py --run-all --root .qualification/b3-ge-e4-pl/f03-variational-attribution-v1`.
The runner registers before action. Require the full three-case supervisor
inventory before canonical adjudication. Terminal precedence is
FAILED_EVIDENCE, FAILED_EXECUTION, FAILED_NUMERICAL_SCREEN, then
PASSED_ATTRIBUTION_DIAGNOSTIC. A pass accepts the bounded identity and
attribution only. All consumed physical refinement HOLDs and the native
full-vector/shear/drilling gates remain unchanged. The independent
continuous-primal derivation is a separate reviewed foundation, not an
executed numerical oracle or external comparison.
