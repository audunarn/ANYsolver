# P5 sixteen-element arch refinement — preregistration

This is a same-author research diagnostic, not independent qualification. The
exact implementation parent is `f6b42eabf6fae9be7b212224e1402ec546940b8f`.
The freeze adds exactly this plan, `ge_beam3_curved_p5_arch_refinement_case.py`,
`ge_beam3_curved_p5_arch_refinement_wave.py` under docs/reference_cases, and
`tests/test_ge_beam3_curved_p5_arch_refinement_wave.py`. No existing mechanics,
source authority, accepted/failed evidence, src, defaults or package changes.

## Frozen case and honest comparisons

Retain the preceding span-2 parabolic arch y=0.1*(1-X^2), clamped ends and
downward crown force. Use 16 quadratic macro-elements, 33 nodes, eight Gauss
stations per half-cell (256 stations per state), eight objective arclength
increments of 0.01, and C=diag(1000,400,400,0.02,0.01,0.02). The high yield
threshold must leave every accepted history elastic. The section law and
existing mixed/assembly/continuation/replay operators remain unchanged.

At each accepted state solve the separately implemented symmetric continuum
BVP9 at the actual crown drop. Retain its full sampled solution, physical
strain energy and load, and the full discrete trial and station responses.
This continuum solver does not import discrete mechanics, but is not yet
independently authored/reviewed qualification authority. Its symmetric branch
cannot establish complete spatial stability.

Use equation-derived Hermite interpolation of the 129 continuum samples to
compare station resultants [N,0,-V,0,M,0] in the existing physical material
basis. Compare stride-one/stride-two interpolation with relative compliance-
weighted norm at most 1e-6. Integrate discrete station resultants and strains
using the unchanged reference Gauss measures; require station energy versus
mixed potential, physical/arc equilibrium, and global force/moment balance
errors at most 1e-11. Validate accepted-origin replay and elastic histories.
Retain all stations, negative Hessian eigenvalues, and failures; no deletion,
stabilization, coefficient tuning, load replacement or reference correction.

Three development accuracy comparisons must each be strictly below 2% at all
eight states: matched-displacement load, compliance-weighted resultant error
norm, and total physical strain-energy error. Also require the accepted-state
load slope to change from positive to negative across the path. The slope is
recomputed at the accepted state, not copied from the old predictor. A load
pass cannot mask a recovery or energy failure. No threshold changes after run.

The coordinator independently recomputes scalar recovery/energy metrics from
raw samples without numerical mechanics imports. A 1e-12 normalized rounding
allowance covers NumPy versus scalar summation order, not scientific equality
or an alternative acceptance threshold. This detects summary corruption; it
does not independently reconstruct the element or continuum solution.

## Process, authority and outcomes

Freeze the exact four-path clean commit before requesting resources. Bind its
commit/tree and case hash plus executable path/hash. The Git commit binds all
unchanged inherited source files. This research runner does not claim a full
hermetic external dependency graph. Verify exact HEAD, immediate parent,
four-path extent, clean worktree, immutable request command/repository, active
owner and one unconsumed administrator APPROVED row before numerical imports
and again at completion. Never reuse the preceding cyclic-refinement request.

Create a new request and exclusive external directory, acquire only its ID
after administrator ledger approval, execute the registered command unchanged,
and release in finally. One worker only; one numerical-library thread; 24 GiB
complete process-tree memory; 600-second child wall budget (the reused safety
timer reserves 15 seconds for termination); 300-second CPU/output inactivity
watchdog. The coordinator watchdog expires at 890 seconds inside a 900-second
resource envelope. Each increment retains sixteen corrector updates and at
most 4096 mixed evaluations. No automatic retry or hidden rerun. Checkpoints
at initialization, step start/completion and worker completion remain external.

Retain a permanent one-use request claim and exclusive raw outputs. Contain
the complete child tree using the unchanged tested Windows Job Object helper.
Failed, timed-out, memory-breached or malformed runs retain only diagnostics,
never a canonical aggregate. A completed validated run emits one of:

- `RESEARCH_ARCH_COMPARISONS_BELOW_2_PERCENT` if every comparison passes.
- `RESEARCH_ARCH_COMPARISONS_UNRESOLVED` otherwise, retaining every error.

Both retain `production_qualified=false` and
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Neither qualifies or activates GE-B3.
No default changes, merge, publication or broader wave is authorized by this
research result. The 16-element arch computation has not run at plan freeze.

## Validation inventory

Small tests cover old geometry identity, explicit 16-element construction
without solving it, two-element one-step physical recovery/work, mirrored
fields, synthetic eight-record schemas, raw hashes, rehashed metric mutations,
strict JSON/exclusive outputs, authority/lease-before-import, consumed request
rejection, accuracy precedence, and simulated timeout/memory/process failure
without partial aggregate. Synthetic fixtures are not mechanics evidence.
Run the unchanged small continuum-reference regression separately. No large
refinement solve or resource-heavy memory test belongs in these unit suites.

Pre-freeze validation (separate inventories): new harness **26 passed in
2.44 seconds**; unchanged continuum reference **17 passed in 1.23 seconds**;
unchanged normal/timeout and descendant-containment checks **2 passed in
2.71 seconds** (17 other process-wave tests deselected). No large arch solve
was part of these tests. These timings are diagnostics, not performance gates.

The broader goal remains open: general nonlinear sections, curved/slender
families, full spatial critical modes, prestressed modal/dynamics, production
state/restart/interfaces, independent reviews, and objective beam-shell joints.
