# F03 typed cancellation: bounded prerequisite result

23 September 2026. The process-tree supervisor now raises
`SupervisionCancelled`, a `KeyboardInterrupt` carrying a validated
`SupervisionReceipt`. Cancellation before launch has no process evidence;
cancellation after launch retains the root PID, sampled peak, discovered
processes, successful kills, elapsed time and exit result. The later
coordinator can write the exclusive terminal receipt before propagating
cancellation. This batch does not create a scientific registration or launch
a scientific case.

Independent review found and verified closure of five issues: cancellation
during cleanup lost the typed receipt; interruption before psutil acquisition
could miss descendants and root-kill accounting; prelaunch receipts admitted
impossible process evidence; PID-based reacquisition could target a reused
PID; and psutil discovery failure could skip handle-owned kill/wait. A further
poll-error check prevents reacquisition when ownership status is unknown.
The root is terminated through its `Popen` handle. Successful descendant
kills are recorded as they happen, including when cleanup is interrupted.

The final affected synthetic supervisor, lifecycle, case-receipt and
adjudicator suite passed **55 tests**. The independent reviewer found no
remaining issues and reported `git diff --check` clean. No scientific case
was launched. G0B remains open and G1 barred. Read-only case replay,
cross-case adjudication and the serial coordinator remain prerequisites to
the one-use scientific registration.
