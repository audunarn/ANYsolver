# Independent F06 development review — 30 September 2026

Reviewer `/root/anyfem_consumer`, read-only, no implementation or numerical jobs.

V1 pre-run review found the stated consequence measures appropriate; actual
admission then exposed the fixture's interpolation/tangent mismatch. The reviewer
verified from original logs/reports that both failures preceded owner/equilibrium
and coverage. For v2 the reviewer independently checked that the global quadratic
arc and its analytic derivative are exactly representable on each Q2 segment,
with the shared tangent (1,0,0), proper triads and unchanged native `1e-11` frame
tolerance. No missing prerequisite blocked that one development execution.

Post-run independent disposition: **FAILED fixed development discriminator;
F06 remains OPEN.** Supervision reports exit 1, 2 cases/2 failures, zero
errors/skips, 25.256 s / 220,409,856 bytes within 600 s/8 GiB.

Q4 reached .25/.5/1 plus reset, direct restore and continuation. All seven saved
states report completed status, free equilibrium <=5.84e-9, independent gaps
<=1.38e-16 and force/moment balance <=6.19e-10 / 1.63e-10. Continued comparison
maxima include support 5.54e-14, retained resultants 3.86e-14, point work 7.98e-15;
predecessor invariants are true. But actual rotations .0056971595 / .0051054986
and commutators 7.2134e-8 / 3.3023e-8 miss the frozen .05 / 1e-5 coverage bounds.
The first coverage assertion failed, so favorable observed invariants are not
a complete predicate pass. All-S3 stopped at first .25 with `finite mixed Newton
iteration limit`, no accepted branch or coverage. Native total energy remains
unmeasured. No formulation failure or scoped F06 acceptance follows.

Preserve both versioned runs; no automatic load/iteration/tolerance retuning
or refinement follows this outcome. Other ready programme work may proceed.
