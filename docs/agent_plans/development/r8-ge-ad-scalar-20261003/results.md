# Shared native Jet2 scalar arithmetic — scoped development result

3 October 2026. Retain library `bccd4952c697f1f52ace205fc2580be5afe7fd0f`.
Baseline library `0d494d1a`; unchanged consumer `4d6d4d0`.
This is an incremental development optimization, not programme qualification.

## Decision and implementation

The saved complete-route profile located substantial cost in shared Jet2
arithmetic. A read-only installed operand census showed only18,016 of321,910
multiplications have raw scalar operands, while32,615 of33,225 divisions do.
Constant Jets are distinct from raw scalars; the census did not justify
shortcuts based on mutable derivative arrays or a change to Jet x Jet products.

The candidate specializes scalar multiplication/division for the ordinary
binary64 derivative layout. It avoids constant Hessian/outer-product buffers
while retaining zero products, original addition order, signed zero/nonfinite
propagation, observable scalar conversion and reciprocal exception behavior.
Returned derivatives own their memory; subclasses and malformed layouts use
the generic route. Jet x Jet formulas, equations, tolerances, defaults,
checkpoint formats, guards and package version are unchanged.

The three-pair development screen showed3.15% median improvement and two of
three favorable pairs, meeting the recorded3% triage threshold for extending
to seven. Smaller gains are retained honestly; this is not a10% gate claim.

## Installed correctness and complete-route measurements

135 installed checks pass, zero failures/errors/skips:130 arithmetic, native
core, variational Q4/S3, guard/ownership/material/rejection/restart checks plus
five actual-update line/work/objectivity/shear checks. Source repair/affected
mechanics campaign:24passed; preceding source campaign59passed/3fixture failures.
Independent OpenAI static Read review found no actionable product issue. It
is development scrutiny, not different-family scientific acceptance.

| Case | Pairs | Baseline median | Candidate median | Reduction |
|---|---:|---:|---:|---:|
|24Q4/32B3, two accepted increments|7|25.026384s|24.374265s|2.61%|
|8Q4/12B3 easy control, same increments|7|9.151017s|8.797285s|3.87%|

Serial alternating installed-wheel pairs. Warm route includes fresh owned
definition/actions, compile, .01/.02 solve, recovery and checkpoint creation;
imports, tiny warmup, checks, output writes and close are excluded. Full Q4
algorithmic pullback is explicit. All pairs match physical arrays, accepted
history, preflight and checkpoint bytes exactly; physical equilibrium,
compatibility and force/moment criteria pass.

Timing variability is retained: screen ranges24.839–27.942s baseline and
24.079–27.826s candidate; one paired screen regression11.08% and one improvement
12.53%. Six of seven pairs favor the candidate in both cases. Easy control's
worst paired regression4.15%; its median improves. No unmeasured broader
speedup, large-model speedup or reduction in peak memory is claimed.

ANYfem native save/reopen, .01/.02 solve, restoration of the PRECEDING wheel's
checkpoint and .03 continuation pass with exact state/re-encoded bytes. Moment
balance1.09835e-10, force1.25913e-11;19.909s supervised/176.4MB sampled tree RSS.

Separate small profile reuses the unchanged baseline profile only for work
counts:16assemblies,8physical updates,204native beam evaluations,255point
evaluations,136shell responses and16constant corrections match. Profiling is
not timing evidence; counts do not themselves prove a gain.

## Artifacts, runtime and failures

Candidate wheel SHA256:
`280dfa5db8977cc1ed7c86f814d323ff2212e5c4a864286e2ddd32f1497701fe`.
Baseline wheel:
`ad81df530f1eb8759b556af20adc125f464767939510dbd5aaab200d71683253`.
414solver source/wheel/site modules and baseline wheel/site hashes verified;
98consumer and13editable material modules bound before and rechecked after
this campaign. Actual imported paths are saved. Windows11/Python3.14.2,
NumPy2.4.6/SciPy1.17.1/Numba0.65.1/ANYmaterial0.2.0. Effective numerical pools
and NumBa threads1, JIT off. Child-tree600s/1GiB ceilings, serial numerical
execution. See raw bindings/resource records for machine and dependency details.

Preserved failures: two fixture assertions assumed Linux overflow wording,
and a subclass test's custom coercion mishandled Jet inputs. Focused rerun
captured all three, then corrected fixtures passed. First installed collection
missed a reference helper in its isolated copy; it was added and all130checks
passed on a new run directory. No failed evidence was overwritten.

Raw archive:265 explicitly whitelisted files/5,879,548bytes; SHA256
`658dbf623624af1611f58263d60a9579dc8fe17869c61edc4be5853b84b6db25`.
[Manifest](archive-v1.json), [samples/results](summary-v1.json),
[static review](independent-development-review.txt), [raw archive](raw-evidence-v1.zip).
No configuration/environment dump, repository history, protected historical ZIP
or unrelated work is included. Original live outputs:
`%TEMP%/r8-ge-ad-scalar-installed-v1`; census/source failures:
`%TEMP%/r8-ge-ad-census-v1`.

## Remaining development decision

The modest gain leaves10k nonlinear feasibility unresolved. The census shows
107,077 right-constant and26,209 left-constant Jet products versus149,550 both
varying products. Evaluate a bounded acceleration of the EXISTING local matrix
operation, preserving ordered products/sums, ordinary-layout admission,
owned outputs, exceptional behavior and generic fallback. Do not tag mutable
Jets as constant, remove observation guards or change mechanical operators.
A complete-route screen decides whether it is worth retaining; if it has no
material effect, stop this approach and address the larger element-map cost.

All mandatory open G0/F01/G5/M5, external/platform/material/attachment/scale
acceptance obligations remain open. Formal F03 is UNCONSUMED; pressure amendment
and release authority unchanged. No push, merge to main or publication.
