# Four-macro uniform arch accuracy diagnostic

Base 43d2dd9369eb73422c4daa783edb43548d351f91. Preserve the failed two-macro
arc smoke and its three accepted steps. This is not its restart or retry.

Use four macros, nine nodes, identical parabola, full end clamps, all interior
spatial DOFs free, generalized elastic section diag(1000,400,400,.008,.01,.01),
yield 1e6, hardening 1, cell order 4, and uniform spatial downward load density
per reference arclength. Keep the native mechanics, translation controller,
state/recovery codecs and tolerances unchanged. Prescribe exactly the prior
crown drops .0009924835187201996,.002196594350540417,.004368321784681136 through
the native translation programme at node 5 uy. This isolates mesh error from
arc-step control. Do not change the earlier failed test to pass.

First run a separate sampling/reflection/work unit inventory. The continuum
solver gains only explicit evaluation sites for its already-resolved BVP
polynomial. Default sites remain identical; equations, Jacobians, collocation
mesh/profile/tolerance and residual checks do not change. Evaluate the existing
BVP9 directly at all native reference stations, without interpolating saved
values. Include the original 129 sites in the requested union to seed the next
reference step. Reject duplicate/nonfinite/out-of-domain/missing-end samples.

Reconstruct expected physical position, section strains/resultants, material
frames and global resultants without importing producer mechanics. Axis 2 is
physical global z; planar section force ordering is [N,0,-V,0,M,0]. Uniform
loading gives ny=q F(X) on both halves; x and theta reflect, moment is even.
Independently check proper frames, reflection and virtual-work transformations.

One bounded native rehearsal must complete all three targets, exact checkpoint
roundtrip, unchanged elastic histories and native physical recovery. Save all
32 station records per target and direct continuum fields. Recompute relative
load errors and resultant-compliance field norms. Report displacement/frame
differences. The 1e-11 constitutive check is an exact linear-law consistency
test, not a relaxed engineering threshold. Do not classify the full element
from a coarse two-level comparison or claim actual limit-point traversal.

Each child: one numerical thread, 24 GiB process tree, 600-second wall,
120-second CPU inactivity. At most three workers and 1800 seconds per wave;
no automatic retries. Preserve failed output before any correction. Only if
the entire rehearsal passes, freeze the changed research paths and run two
fresh-directory deterministic replicas. No new B2/B3/Q4/S3 or shared solver
source, default, public API, package or dependency changes.

If load/field errors decrease, continue controlled refinement and bounded
objective arc cutback/step adaptation. If not, diagnose operators/branch/field
maps; do not tune mechanics against the reference. Full spatial stability,
postbuckling, practical-scale performance, all parity/mass/spectral/review/
package/joint requirements of the full goal remain open.
