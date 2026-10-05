# C6 generalized reactions and continuous reference — 3 October 2026

Development slice on parent `7124e166`, reconciled contact branch; exact changed
source hashes and run records in
`contact_c6_reactions_reference_20261003/{source.json,raw.zip}`. No qualification,
release or installed-artifact promotion. Original numerical/resource restrictions
and failed evidence remain intact.

## Implementation and question

The prior coupled manufactured Q4 case matches independent discrete equations but
changes final plastic strain3.44% on halving dt. A cheap continuous reference
distinguishes temporal error from a wrong structural/contact work map before a
third expensive production solve. No solver/material kernel is called in it.

Independent two-mode equations use fixed affine pressure groups, uniform pure
deviatoric membrane and the constant DNV first plateau alpha<.005. Exact branch
matrix exponentials are controlled by tighter steps and separately evaluated
dimensionless DOP853 forces. Taylor/Bernstein ranges, bounded event localization,
analytical event/unloading tests and hidden-excursion controls scrutinize event
logic. Propagation controls share that logic: agreement alone does not validate
it. Floating branch enclosures do not certify all upstream propagation arithmetic.

Review corrected a right-continuity overclaim at requested exact boundary times:
the documented output phase may remain incoming within branch tolerance. Grouped
roots now each satisfy their gap/stress/velocity residual at the earliest group
state before any branch change; otherwise reference evaluation fails explicitly.
The frozen impact has5events and no unloading event; unloading has a separate
analytic no-contact check. Original20pass run is retained;4affected outcomes cover
the two fixes and rerun the frozen propagation controls. No full-suite replay.

## Numerical result and disposition

Tighter exponential agreement max7.99e-13 and DOP8531.52e-13 on declared strain,
displacement, velocity and history scales. Reference total energy defect7.62e-12J
from250J; this alone does not prove the small membrane response. Source checks
and independent equations provide that discrimination. Five contact/yield events,
no zero-time stall in the frozen case. No engineering-material admission.

At matched end.003s, saved source fields yield:

| Response | dt3e-5 relative error | dt1.5e-5 relative error |
|---|---:|---:|
| Final membrane strain |4.829%|1.379%|
| Final plastic strain/alpha/dissipation |4.889%|1.396%|
| Final membrane kinetic energy |10.451%|2.929%|

This supports timestep error as the principal discrepancy. Half dt is below2%
for the named final strain/history quantities; membrane energy and the complete
impact programme remain open. No asymptotic order or temporal qualification.
No third production refinement was run. The pre-review comparison JSON keeps its
old reference hash; corrected comparison is a separate run with the new hash.
Comparator zero-reference relative errors are null, with absolute/scaled errors
still reported. A precontact saved-field check exercises that case.

## Integrated output and state work

The new explicit `save_constraint_reactions_dev=False` default leaves old route
and checkpoint identity intact. Enabled output is structural generalized support
force `M a + internal/contact residual - external nodal load`, aligned with saved
states. A copied full residual is bound to exact candidate pose/time; acceptance
validates it before commit. No second assembly. Enabled selection is restart-bound.
Free-body centre coordinates are excluded from structural output. Physical moment
recovery still requires formulation-owned maps.

Eight scoped source outcomes pass: oblique contact support balance, unchanged
dynamics/default and restart, constant-load subtraction, strict bool selection,
unequal-load MPC reactions, ramp/sparse output, S3 descriptor equilibrium and
free-shell-sphere assembly. Read-only review found no concrete reaction defect.
One new contact-driven yielded restart test passes through separation, matches
independent discrete q/v/plastic histories, retains the exact accepted parent and
checks reactions do no allowed-mode work. Prefix at the previously saved nominal
time.0008933632224845885s, suffix through.0011s; no arbitrary gap-band END admission.

Runs remain180s/953MiB: reaction selections8.44/5.35/7.15s (see exact resource
JSON, rounded times here are descriptive), yielded restart44.92s/187584512bytes.
Reference reviewed-control run7.71s/110825472bytes. Actual imports point to this
worktree for source runs; JIT off and effective numerical threads1. Pure reference
has no ANY imports/JIT use. No speed claim or new installed/released capability.

## Next decision

Stop this manufactured timestep diagnostic branch. Retain it as a reproducible
reference for a future named qualification case. Close the next required programme
gap using bounded integrated slices. Broader geometry/materials, event-path
qualification, component work, application/installed admission and C0–C9 completion
remain required. Native grazing-friction nonpass restrictions remain unchanged.
