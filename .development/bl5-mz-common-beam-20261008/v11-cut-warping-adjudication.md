# V11 saved V7 cut-action response — development decision

**Decision:** The zero-resultant part of the saved V7 C3D20 cut action has a
small *incremental two-sided work effect* under the V9 remote six-pose supports.
The complete saved action pairs to `3.26233566576849e-5 J`; its six-resultant
work-dual lift pairs to `3.26739102749489e-5 J`. Their ratio is
`0.998452783372467`, a signed `0.155%` difference. The zero-resultant action
itself has a large nodal force norm; its positive self work is offset by
negative cross work. Small work does not mean a small action in every norm.

One V11 numerical attempt passed in `2.327402399998391 s` process wall, with
`164986880 B` sampled peak process-tree RSS. The two half-body KKT equation
ratios are at most `8.24e-12`; remote gaps are at most `2.42e-24`; the
zero-resultant wrench is at most `2.67e-15`. The runner verified effective
CPU0, one numerical thread and JIT disabled. It performed four resolved-half
RHS solves and no native, external, V5, or formal F03 solve. The cumulative
V11 allowance has `117.67259760000161 s` remaining, including its untouched
`60 s` reserve; the one successful attempt closes this specific question and
does not create authority for another diagnostic.

[Registration](v11-cut-warping-registration.json),
[receipt](receipt-v11-cut-warping-attempt-1.json),
[raw result](case-v11-cut-warping-attempt-1/result.json), and
[source](../../scripts/r8_bl5_v11_cut_warping_response_dev.py) bind the exact
saved V7 action and source. An initial invocation with the workstation's
Python 3.11 stopped before the runner started because `psutil` was missing;
the recorded numerical attempt used the installed Python 3.14 environment.
The initial launcher failure performed no numerical solve or budgeted attempt.

Independent read-only review found no blocking action-sign, reconstruction,
reciprocity, or work-decomposition defect. It confirmed the comparison is only
for split C3D20 halves under V9's remote support. The original V5 P0/tip-load
state, native retained variables, and coupled connection were **not** changed
or resolved. V11 does not causally allocate V5's `7.24284444` native/resolved
body-work ratio and does not choose or qualify a line law or multiplier space.

The saved V5 algebra also shows a direct interface pairing of
`1.15586949156334e-7 J` with native retained spins. That is a load-role term
on the already solved native state, not the compliance change caused by that
load. Further saved-vector decomposition cannot answer the remaining causal
question. The next connection discriminator must reproduce the original
P0/tip action with physically matched two-sided beam and shell responses,
including native retained traces, or identify the exact missing conjugate
reference. No automatic refinement or formal F03 run follows from V11.
