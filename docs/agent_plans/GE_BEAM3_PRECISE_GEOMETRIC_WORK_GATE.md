# Expression-preserving private GE-B3 scalar work successor

Parent 7b2b017179af87cd42cc10f575b8664729453aab. Preserve the failed native
directional gate and 38-file diagnostic archive bound in
GE_BEAM3_NATIVE_SECOND_VARIATION_STATUS.md. No threshold or step change.

Source equation map: native potential Pi=p.k-Psi*, k=(z0,z1,ell endpoints),
z_c=U_c^T(x_right-x_left)-(r0_right-r0_left),
ell_cn=sign Log((U_c R0_n)^T Q_n), sign=(-1,+1).
The increment map remains Exp(delta_theta) times its committed matrix. Low
coordinate parts are included before subtraction; resultants are the actual
updated native binary64 values, not incremented twice. The actual material
conjugate high/low value is supplied, never reconstructed or replaced.

Bind unchanged source files by SHA-256:

- _ge_beam3_retained_generalized.py:
  c125567e0dfb5423abab264b868483f8802bd047b828c7851626ac34597b0f98
- _ge_beam3_mixed_ad.py:
  c71cea89056ccb671d37d3169085844b7012e7fa8b7d78545dfc45fadaec105b
- _ge_beam3_p5/compensated.py:
  0d66c81dd3820a2cc034f0383901805c87cb251d7cf31326ebee32a5d90ff0f0

Implement private arithmetic policy GE_BEAM3_RETAINED_GEOMETRIC_WORK_DECIMAL80_V1:
80-digit scalar work, one final binary64 rounding. Entire Rodrigues coefficient
series avoid 1-cos cancellation. Near-identity theta/sin(theta) uses the convergent
delta=1-cos(theta) series a_0=1, a_(n+1)=a_n(n+1)/(2n+3). Else compute
theta=2 atan(sqrt((1-c)/(1+c))) with bounded half-angle reduction and alternating
atan series. Retain proper-rotation validation and the 0.9pi relative/increment
domain. Arbitrary common rigid rotations do not use an incremental chart limit.
Every series has a finite iteration ceiling and raises on nonconvergence.

First validate the scalar function separately: independent SciPy rotation and
matrix-log checks over the admitted domain, near-zero series, exact simple work,
rigid objectivity, finite noncommuting states, direction checks against native
analytic residual/Hessian, nonfinite/dimension/domain mutations, cancellation
callback, deterministic output and unchanged caller state/context. Preserve
coupled/nonlinear material origin by consuming its actual conjugate only.

No old operator, owner, history, checkpoint, recovery or native scalar output is
silently replaced. Adoption requires an explicit successor arithmetic fingerprint
and renewed native owner/equation checks; old source-bound checkpoints must never
be relabelled. No source hash, historical proof or failed gate may be rewritten.
This arithmetic helper alone is not qualification or public activation.
Existing B2/B3/S3/Q4 mechanics and all defaults remain unchanged.

Adoption interface: private RetainedGeneralizedOperator and
NativeGeneralizedStaticElement accept an explicit arithmetic_policy keyword.
None preserves the old algorithm, identity and descriptor exactly. The new
policy changes only scalar potential evaluation; all kinematics, analytic
residual/Hessian blocks, material/history and recovery remain byte-identical.
The new operator identity binds the source identity and arithmetic policy;
the element descriptor discloses it. Capture and guard the policy. No public
factory exposes it and old hot-restart identity cannot match the new candidate.

For authentic native testing, explicitly enroll immutable original endpoint
fields as a new elastic equilibrium seed under the new model/operator identities,
binding the original full checkpoint hash as source authority. Verify virgin
origins and let the existing owner perform actual equilibrium/correction checks
before issuing a new genesis. This is not relabelling/replaying the old checkpoint
as the new candidate, nor evidence of loading from rest. Bind the original chain
and retain it intact. Test foreign seed/checkpoint rejection and new-owner
checkpoint replay. Freeze before signed endpoint runs; positive smoke still gates
replicas. Keep five points and both frozen h values, 1e-11 lift/work and 1e-7
directional gates, 600-second/24GiB child bounds, max3 workers and 1800-second wave.
