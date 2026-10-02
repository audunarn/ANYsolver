# Displacement chart events and bounded branch diagnostic — 2 October

V1 snapshot framing remains unchanged without chart events. V2 adds positive
chart_events and exact generation arithmetic. Rebase retains loads, physical
configuration, displacement history, accepted/predecessor material arrays and
adaptive budgets. Endpoint replay validates mechanics; both versions then install
saved accepted histories exactly, preventing tolerance-close replay drift.
Independent review /root/bl5_shell_contract found no remaining implementation
finding after this precision correction. No checks run by reviewer.

Source initial9checks pass33.94s. Installed final24checks pass178.21s,
supervised180.17s, peak190758912bytes. Includes unrebased/rebased continuation
comparison, cancellation, pending adaptive restore, V1 framing, exact accepted
histories, and existing displacement/coupled lifecycle coverage.
Solver wheel5de06768ea58752c51b498468f983afbab6c43f9c82155009691d2f76578512a;
404modules source/wheel/site match. Installed consumer1workflow passes37.23s,
supervised39.31s, peak186183680bytes; ANYfem wheel
895f31eca0d795c7e4b165cad4bc8139c0a4eeb96ed8c56b1da802bcaa54a720,98modules match.
Onsite imports/one-thread pools/JIT-off are asserted by both runners.

## Reviewed four-probe discriminator (no continuation campaign)

One instrumented reproduction captured the previously unsaved final failed
-68um state. Failure matches5iterations/61evaluations/7solves/54rejections,
equilibrium1.62500465666. Accepted prefix unchanged. Four actual-update probes
used exactly t=+/-2^-14,+/-2^-15, with fixed material predecessors/loads/weights.
No change to target, backtrack budget or acceptance criteria. Run19.56s,
peak165806080bytes. Raw K, residuals, direction, weights and material arrays saved.

Predicted merit slope-5.227930887e-15 agrees with Newton expectation
-5.227930906e-15; weighted linear residual5.45e-7, control linear error0.
Negative probes have weighted secant error5.84e-5 and3.17e-5. Positive errors
are7.08 and4.21, with positive measured merit slopes2.70e-14 and1.39e-14.
Global generalized-beam station row7 has incremental accumulation1.26219e-10
at base, zero at both positive probes, and positive accumulation at both negative
probes. This establishes a material active-set change across the finite probes;
it does not establish a defective local tangent, singular physical branch or
endpoint reachability. Stop the four-probe batch as designed. Next decision must
address this branch transition explicitly, not automatically extend backtracking.

Archive installed-and-discriminator-v1.zip SHA256 d19fb65a4421bb36611dcfa6df2558dd0377986ff538fdf7cb97ddf8ad0c525f.
No environment dump. Full programme/scientific qualification remains open.


Independent stored-array review confirms station7 is the sole beam loading-class
change under the increment criterion; both positive probes return all six plastic
increments exactly to predecessor values. No shell station changes classification.
Mismatch concentrates at residual row87. Negative-side alpha derivative gives an
estimated first event near t=1.76e-5, not an evaluated acceptable step. The selected
next action is a bounded design for explicit branch-event-aware continuation:
expose the material loading indicator and directional boundary estimate, propose
an event-aware trial, reassemble its actual tangent and retain all equilibrium
criteria. Do not alter constitutive tangents or enlarge generic budgets to fit the
case. This is a design action, not an implemented or qualified method.
