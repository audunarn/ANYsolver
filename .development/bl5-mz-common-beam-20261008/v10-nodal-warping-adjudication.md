# V10 nodal-frame response and saved warping-action adjudication

V10's second attempt completed in 2.4909969 s process wall, with sampled peak
process-tree RSS 163,192,832 B. It imported ANYsolver and the GE compiler
from this worktree's `src`; their actual paths and hashes, together with the
fixture origins, are in the [result](case-v10-nodal-warping-attempt-2/result.json).
The [receipt](receipt-v10-nodal-warping-attempt-2.json) records CPU0, the
one-thread/JIT-off child environment, hashes and exact timing. Both attempts
used 4.8932763 s, leaving 115.1067237 s including the 60 s reserve; the
two-attempt registration is closed and grants no further run. Attempt 1's
saved-state branch failed because it indexed V5's beam-only coordinate vector
as a full shell+beam vector. Its receipt, stderr and original registration
remain preserved. The source repair and amended registration are versioned.

| Incremental cut action | Native nodal-frame work | Native retained-spin work | C3D20 rigid-face work |
|---|---:|---:|---:|
| V7 six-resultant Fy/Mx/Mz | 4.16580771546019e-5 J | 4.07707809202245e-5 J | 3.26739102787352e-5 J |
| Pure unit Mz | 1.48809523809524e-5 J | 9.92063492063492e-6 J | 1.48809523822698e-5 J |

For pure Mz, native nodal-frame/C3D20 work is `0.999999999911` under the
declared remote section-pose restraints. The retained-spin/C3D20 ratio is
`0.666666666608`. These are separate applied/observed generalized ports;
the native nodal frame and cell orientation are independent coordinates.
Under nodal-frame loading, the left retained spin is `5.58035714285714e-6`
versus the nodal-frame spin `7.44047619047619e-6` rad. V9's 2/3 response
and V10's 3/4 observed-spin ratio therefore do not contradict each other.

This excludes a **gross local nodal-frame Mz bending-stiffness mismatch** in
the two isolated half-bodies under these incremental supports. It does not
prove that all native bending or body behavior agrees in V5: the original
problem uses distributed P0 and tip actions, a free-body gauge, mixed
channels, retained traces and an interface. The V7-resultant native
nodal-frame/C3D20 ratio is `1.274964545`, so its combined force/couple
response still differs in this bounded model.

V7's saved full nodal cut-port work is approximately ±`1.56688671014e-7 J`
per side. Its rigid six-resultant lift contributes approximately
±`1.56341917005e-7 J`, leaving zero-resultant cut-action work
±`3.46754008839e-10 J` on that **saved conforming displacement** (about
0.22% of the absolute full work). The remainder's nodal force norm is
`9.76481644 N`, so its response on a new two-sided displacement is not
known; the Euclidean norm is descriptive, not a mesh-invariant dual norm.
Zero resultant and exact work decomposition passed at roundoff.

Read-only source/mechanics review found no concrete source defect and agreed
with this limited interpretation. V10 is development evidence, not an F03
or BL5 law decision and not an allocation of V5's 7.24284444 loaded-body
ratio. The next discriminating comparison is the original free-body P0/tip
load projection through nodal versus retained work paths, including the
zero-resultant warping response where it can affect that solution. Do not
start another pure-Mz or classical axial refinement to reproduce this result.
