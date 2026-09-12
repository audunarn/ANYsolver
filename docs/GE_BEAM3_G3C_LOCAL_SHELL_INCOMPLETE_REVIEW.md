# Independent private local-shell review: incomplete required coverage

Subject c1d571a143d0b3b62eafd3aa240a1a84cc7c298f,
tree cf1bd7f21502000767cf5571a7175c1029575d7f, exact four new paths from
44c1574516b8f2c257db1c675b99c76e7fc33012. Reviewer
`/root/g3b_independent_review`, separately approved independent agent.

I read the complete private module, test, bounded runner and implementation
document against the accepted matrix-shell equations. No source was modified
and no reviewer mechanics run was launched. The author reported two smoke
passes and 26 full-lane passes; those outcomes are preserved, not turned into
mechanics failures by this review. They do not close missing required tests.

## Findings

SH-01: the purported snapshot mutation regression at test lines 223–228 mutates
the original u and qa, but the tested call receives fresh copies. A no-copy
implementation would still see unchanged passed arrays. This is a concrete
test-logic failure, not merely a request for more tests. Use named passed_u and
passed_qa arrays, pass those very objects, then mutate them in the callback
after capture. Confirm kinematics, chart/spatial force/tangents, channels and
candidate reflect the pre-mutation snapshot. Preserve the re-entry check.

SH-02: the frozen D4/D3/director/station transport obligation is incomplete.
The numbering test at lines 144–156 checks only aggregate energy/force/Hessian;
the common-motion/rebase test at lines 108–141 likewise does not validate the
separate station work-channel diagnostics. Incorrect station ordering, frame,
tensor or derivative-column maps can therefore coexist with all 26 passes.
The implementation document honestly lists full station tensor transport as
remaining work, so it cannot simultaneously be treated as full completion of
the frozen 13-category inventory.

Add all required source station correspondences for four shapes, all D4/D3
operations, physical director reversal, passive coordinate re-expression,
common pi/1.4pi motions and same-pose rebase. Include reference/current physical
station positions, quadrature weights, engineering strain/resultant fields,
global tensors, and strain differential column conventions. Current
strain_differential arrays map local extraction-deformed d; do not apply chart
P to them as if their columns were eta. Numerical PL/hourglass stay separate.
Per-channel force/tangent and station invariance should accompany aggregate
checks, preserving source station/physical-director authority.

## Other reviewed points and remaining boundaries

No separate algebra defect was found in the full matrix D/S pullback, P
connection contraction or signed source-force construction on this read-only
pass. The runtime explicitly checks actual Q4 weak mixed work and channel
force/tangent sums, and S3 actual station weak work. Source ownership uses fresh
private family objects and virgin origins. Finite guards protect returned
arrays/aggregates and detached bytes; direct write/delete and ordinary re-entry
are rejected. This is not a substitute for the missing regression coverage or
for a final independently verified corrected execution.

The retained local inventory otherwise maps as follows: independent values,
actual reference rank/nulls, complete directional map/force/Hessian/energy,
signed Q4 sums/sentinels, source S3 work, top-gap/Log guards and old-map matching
poses are represented. Numbering/common/rebase station transport is partial;
the ownership snapshot subcheck is ineffective. The broader conventional
finite Q4 PHYSICAL_RECOVERY limitation is correctly left unresolved, not counted
as a new defect of this local candidate or silently waived.

Correct the two findings under a new frozen successor and preserve this
checkpoint and author raw evidence. Then review the complete corrected source,
run its own bounded local lane and independently adjudicate it. No historical
mechanics rerun, public Q4/S3 change, graph authority or full G3c acceptance is
granted by this review.
