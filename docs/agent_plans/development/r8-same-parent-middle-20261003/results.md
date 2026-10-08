# Larger same-parent handoff screen — 3 October 2026

**One installed pair passes with exact physical/history/checkpoint parity.**
400Q4/120B3 full-pullback generalized-point solve at fixed .01/.02 targets:

| Complete warm route | Baseline bccd4952 | Candidate bb17ecac |
|---|---:|---:|
|Seconds|192.00846|130.49511|
|Setup seconds (included)|18.04137|17.61954|
|Sampled process-tree peak bytes|304,017,408|300,412,928|

Observed time reduction32.04% is **PRELIMINARY**, not a median, memory gain,
seven-pair result or large-model G5 acceptance. Separate startup/small warmup is
excluded; construction, compilation, two increments, recovery and checkpoint
are included. Both histories have3iterations per target. Equilibrium4.88e−11,
gap2.55e−18, force1.61e−14 and moment3.61e−15 pass unchanged physical criteria.
Results, histories, preflight and checkpoint bytes match exactly.

Reused immutable runners/wheels from the
[preceding seven-pair evidence](../r8-same-parent-trial-20261003/results.md).
415candidate/414baseline solver,98consumer and13material module identities
were reverified before launch. Candidate wheel50001b03...63a3e50e, baseline
280dfa5d...1497701fe. Effective pools1/Numba1/JIT off, serial600s/1GiB per child;
both exit0, no resource limit. Owned handle73132 is terminal.

Command: `paired-run-v1.py timing middle 1 1` from the preceding temporary runner
root. [Raw checksums](raw-v1.json) preserve that runner/binding and both complete
outputs. Stop medium timing campaigns and proceed with engineering obligations.
Product admission remains restricted to the preceding retained implementation;
no API/equation/state/default/version or qualification change.
