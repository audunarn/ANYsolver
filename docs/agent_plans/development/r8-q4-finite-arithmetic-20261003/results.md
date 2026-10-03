# Finite Q4 precision correction and physical work decision

Development evidence, 3 October 2026; **not G0/F01/G5 acceptance**.
Library commit `1a620808`, solver wheel SHA256
`3e6e0691879203a57c7bf84ab2a7974b713156a535a45afd83291e54fb4a824b`.
414 Python modules match source, wheel and installed site. ANYfem remains at
`4d6d4d0`, pinned consumer wheel
`5f5c203cea8af60e285df8835cf27210e74718c4bbf1bf916711eb8751fd223a`.
No ordinary formulation default, element equation, physical tolerance or version changed.

## Delivered numerical correction

The 24-Q4/32-B3 mixed-force finite route previously exhausted backtracking after
213.741s without an accepted increment. A bounded follow-up localized the
1.39e-7 residual to shell arithmetic; actual-update directional derivatives
passed the existing 1e-6 criterion at two steps. At the saved state, stabilizing
rotation-minus-identity permits one Newton correction to 1.61e-11; recentering
alone leaves 3.43e-8. This is not a timing comparison or general tangent acceptance.

For a proper SO(3) frame, A=(R-R.T)/2 and c=(trace(R)-1)/2 give
R.T-I=(A+A@A/(1+c)).T. The expression recovers quadratic small-rotation terms
without subtracting nearly equal diagonal entries. For c<=.5 or a nonfinite,
improper/nonorthogonal frame, historical subtraction remains. No frame, tangent,
constitutive predecessor or physical connection law changes.

Fresh flat/all-Q4/historical point force-control owners use the correction;
ordinary corotational callers, curved/mixed-S3/algorithmic/material-shell/fibre/
line/footprint routes retain their existing contracts. This intentionally repairs
fresh experimental stepping, **not** an ordinary solver default. Four distinct
binary checkpoint kinds bind the arithmetic to elastic/generalized-material
histories, with/without shell charts. Old snapshots force old arithmetic before
mechanical validation and continue emitting their original format.

24 installed tests pass, no skips/failures: SO(3)/invalid-frame checks, moderate
and actual-update derivatives, the failed panel's .01/.02/.03 sequence and exact
restart, cancellation/rejection, four-kind restoration, valid-digest unsupported
schemas, generalized yielding/reversal, mixed/S3/J2 routes and ordinary legacy
900N response. The combined chart/material test exercises nonmonotone zero-plastic
history layout; **active-plastic chart qualification is not claimed**. A fixture
from the previous verified wheel `cd481416...ca2c58` continues with exact legacy
arrays/bytes. Source checks and their repaired fixture failure remain retained.

## Physical decision: use the existing full pullback

The historical ANYfem 8-Q4/12-B3 sequence and exact restart completed, but its
current-configuration moment ratio **2.23035e-8 fails 1e-8** (force 1.27035e-11).
Reaction frames, indexing, current positions and load measures were checked.
At the saved .02 prefix the shell's internal moment ratio is 1.54519e-8 with
both old and corrected arithmetic. The existing full algorithmic pullback gives
6.36017e-16 at the same held state. The historical force is E f_local;
its consistent tangent differentiates that force, whereas the full adapter
uses D.T f_local plus chart mapping and the complete derivative. A tangent
check therefore does not establish rigid-rotation work/physical moment balance.

Keep this inherited failure and F01 open. Forward physical nonlinear workflows
explicitly select `Q4_ALGORITHMIC_PULLBACK_V1`; historical defaults and identities
remain. Same ANYfem geometry, laws, supports, loads and .01/.02/.03 targets then
pass save/reopen, checkpoint, restore and exact continuation: equilibrium
4.21627e-10, compatibility6.64530e-18, force1.25913e-11, moment1.09835e-10.
The new runnable public example is
`python -m scripts.experimental_stiffened_ge_finite_panel`.
It verifies physical balance and exact restart on this admitted point fixture;
it does not qualify line torque, drilling, capacity or the complete connection law.

## Bounded scale result and next action

The existing 400-Q4/120-B3 geometry, with six stiffeners and 66 eccentric
six-row point ties, completes .01/.02 using the explicit full Q4 pullback.
6 physical/retained arrays plus reactions and a checkpoint are retained.
Two generations, three Newton iterations each; 7,398 mixed rows;
reference structural nnz344,016. Equilibrium4.88153e-11, compatibility2.55348e-18,
force1.61174e-14 and moment3.61219e-15 pass their unchanged limits.

The cProfile route is 352.056s supervised, 301,043,712 sampled peak bytes:
setup20.131s, profiled solve330.424s, 14 full assemblies. One numerical thread,
JIT off, 600s/1GiB bound; effective settings verified. This is a **profile**,
not a production timing or optimization claim. Overlapping cumulative costs:
5,600 Q4 responses263.519s, constant linear correction103.378s,
1,680 native beam evaluations58.655s. Do not sum overlapping times.
Target dependency-correct reuse of the constant Q4 correction before attempting
10k nonlinear execution. No automatic larger/refinement run follows this result.

## Evidence, failures and review

[Summary](summary-v1.json) and [archive identity](archive-v1.json).
Whitelisted immutable raw archive:151files,2,988,520bytes; SHA256
`01d8aa1573d662d490a6f6e561de158f27eb1bf8fc53ae1405f9258aac4b47bc`.
It includes fixed inputs/scripts, observed settings, the final wheel/import binding,
raw numeric outputs, checkpoints, profiles, adjudication and available failures.
Initial script-name shadowing, unpacking/report-field errors, source no-point
fixture mismatch, the historical moment failure and example ID-access error are
preserved. Source development runner stores selection/runtime/resource records;
its full console traces are in the chat, not an independently captured log.
The superseded build has its identity/logs retained but was not the final execution.
No protected historical credential archive or complete environment was copied.

Independent OpenAI Read scrutiny found no remaining implementation correctness
finding and confirmed the physical interpretation. This is a separate developer,
not different-model-family scientific acceptance. Full G0B/F01, G5/M5,
nonmatching/plastic/large nonlinear, external/platform/consumer and release
obligations remain open. Formal F03 is unconsumed; pressure amendment unchanged.
