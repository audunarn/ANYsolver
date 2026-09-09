# GE-B3 P5: distributed dead-line work and load-parameter condensation

## Status and extent

Development prerequisite for native load integration, not qualification or a
new public workflow. Parent is `326ad849ba29f8fc9f0a40ca7da6483f97f55d40`.
All production sources, existing elements, defaults and previous qualification
records remain unchanged. The centered native V3 package remains frozen and
unqualified; its independent review is still pending.

The new research adapter and separately coded analytic oracle check uniform
spatial dead force **per unit reference arclength**. They do not implement
distributed couples, material/follower loads, current-arclength loading,
gravity-density conversion, native load scheduling, restart of loaded states,
or a public load selector. No canonical formal qualification is generated.

## Work and derivative contract

For each half-cell the physical position is the nodal linear interpolant plus
the rotated Q2 reference lift. With cell rotation U, reference lift d0, nodal
displacement u and force f, load work is

`W = integral f . [I u + (U-I) d0] ds0`.

Nodal translations contribute the integrated linear weights. There is no work
on the independent nodal trace rotations or moment multipliers. Cell rotations
contribute `cross(U*c, f)`, where `c = integral d0 ds0`. The spatial second
variation of this work is

`sym(f outer (U*c)) - dot(f,U*c)*I`.

The independent oracle reconstructs Q2 positions and derivatives directly from
the supplied nodal floats using rational shape functions. It integrates the
registered Gauss stations and uses the closed-form derivatives above. It
imports only the standard library and NumPy, not ANYsolver, its reference
geometry, automatic differentiation, beam mechanics, or the producer adapter.
This is an independently implemented load identity check, **not an independent
human/agent review or continuum quadrature-convergence certificate**.

The producer evaluates only the load terms using the preserved centered
reference evaluator and analytic SO(3) automatic differentiation. It never
subtracts two material potentials to recover a small load contribution. The
initial prototype used that subtraction; inspection identified its cancellation
risk and it was replaced before recording the diagnostic. Tests compare the
load-only derivatives with both the analytic oracle and the difference of full
frozen mixed operators at ordinary load scale. Separate relative-error checks
retain load force, work and Hessian at scale `1e-20`; zero force is exactly zero.
A separate witness shows that subtracting the two complete mixed potentials
does return zero at that tiny scale while the directly accumulated work is
nonzero. This is a representation check, not an assertion that a full solve can
resolve arbitrarily small load changes against an unrelated large force.

Let p multiply the fixed spatial force, let q denote the external 18 coordinates,
and let z contain six internal cell rotations plus twelve moment coordinates.
For `L(q,z,p)=V(q,z)-p*W(q,z)`, at fixed accepted material origins and stationary z:

- `z_p = inverse(H_zz) W_z`;
- `g_p = -W_q + H_qz z_p`;
- `Pi_p = -W`;
- `Pi_pp = -W_z dot z_p`.

The signed stationary saddle block is solved directly. No pivot clipping,
stabilization, empirical load correction, fictitious mass or tolerance change
is introduced. Material origins are fixed through every local evaluation;
the diagnostic never commits a state. Parameter finite differences compare only
the same smooth active branch, not a yield-switching derivative.

The tested curved cases have a nonzero internal correction of approximately
0.004 in the chosen fixture units. The straight cases have zero correction
because the reference lift vanishes. Consequently a naive nodal projection is
not a sufficient general curved-element distributed-load interface. These
numbers characterize the registered examples, not a universal relative error.

## Checks and evidence

An initial test fixture accidentally supplied the historical research section
class where the frozen core requires its exact packaged section type: seven
tests passed, two failed and twelve setup errors occurred in 1.81 seconds.
Only the fixture was corrected by constructing the exact class with unchanged
section coefficients. All 21 checks then passed in 3.93 seconds. After adding
direct load-only AD and tiny-load regressions, **28 passed in 3.82 seconds**.

Checks cover straight/curved geometry, coupled elastic and directed-hardening
plastic sections, fixed-origin load-parameter derivatives, force/work/Hessian
agreement, load condensation, noncommuting cell spins, rigid rotation covariance,
exact translations by `2^30` and `2^40`, tiny force, invalid input rejection and
oracle import independence. They remain small development checks; there is no
large model, benchmark or consumed resource-request retry.

The deterministic diagnostic has four ordered records, each with 16 stations.
It binds its source files and the preserved 36-module centered native source
map, checks the bindings before mechanics import and again after execution,
and records full-response hashes for three identical-geometry translations.
Two fresh processes produced identical stdout records in 3.64 seconds each.
Their canonical result is `ge_beam3_centered_line_load_evidence.json`. It sets
`production_qualified=false`, `native_load_integration_complete=false` and
`independent_review_status=PENDING`. No timing is used to classify the result.

Final regression, including the explicit subtraction-loss witness: **73 passed
in 7.81 seconds**. The inventory is 29 new load checks, three static evidence
checks, 14 unchanged centered local-operator checks, six preserved centered
native checkpoint checks and 21 existing straight P3 opt-in checks. The
preceding 72-check regression passed in 7.76 seconds before the last witness
was added. No failed mechanics result was discarded or reclassified.

## Next native integration gate

Introduce an explicit load-state contract that binds the force measure, spatial
direction and current load/program parameter. Supply that parameter to each
local stationary solve and replay it at commit/restart. Do not store it as an
unchanging preloaded section or infer it from a global nodal force vector.

Global Newton must use the loaded stationary residual and tangent without
double-counting the nodal part of W. Displacement/arc-length controls need the
consistent condensed load-parameter derivative above. Loading/unloading,
rejected steps, cancellation, restart, recovery, work and reactions must be
checked together. A loaded-state modal/buckling path must bind and differentiate
the same load potential at the converged state.
Spatial residuals, Hessians and parameter derivatives must also pass through
the native rotation chart, including its connection terms; a raw spatial
potential Hessian is not automatically the solver's chart Jacobian.

Only after those interfaces are implemented and independently reviewed should
the corresponding native workflows enter engineering qualification. Existing
Q4/S3 and B2/B3 remain unchanged; broad section parity, standalone qualification
and the separately qualified objective beam-shell connection remain open.
