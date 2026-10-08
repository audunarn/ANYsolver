# Multiple explicit classical beam-plane impact — development slice

Parent: `6cb9a304`, isolated contact reconciliation worktree. Development only;
no C6 acceptance, release, changed defaults or consumed-run replay.

## Decision and equations

Question: can the existing explicit contributor sum enter shared Newmark without
losing per-pair gap/resource/transaction contracts? Reuse
`MultipleBeamRigidManager`; sum its penalty residuals/tangents on authoritative
coordinates. Add an explicit multiple-plane opt-in requiring the classical beam
opt-in. Admit fixed planes only, exact elastic B2/B3, declared round radii, no caps,
and union coverage of every structural element. Existing duplicate feature
ownership, candidate caps and deterministic interaction order remain binding.

Evaluate each pair's tensor-Bernstein Hermite enclosure with a shared remaining
subdivision budget. Accept only when every endpoint and complete-path gap meets
that pair's dimensional tolerance. A global minimum is reporting only. Bind the
opt-in, profile, pair definitions and settings into restart; no new physical
history or solver stack. All participants commit through the shared transaction.

## Bounded discriminator and outcomes

One beam moving into two coincident but distinctly identified physical planes is
a declared additive penalty fixture: independent rigid-mode scalar Newmark uses
the sum of line stiffnesses. Check each reaction, total impulse, opening and
active split restart. An orthogonal two-plane fixture exercises distinct gap maps.
Manufactured path checks discriminate per-pair budgets and aggregate exhaustion.
Reject missing opt-in, radial bodies, caps, duplicate ownership, uncovered
elements and incompatible restart. History and failure cleanup reuse shared code.
Reaction/trajectory comparisons use dimensional tolerances from the existing toy
beam fixture (1e-7 N, 1e-10 m, 1e-8 m/s, 1e-11 N s); no engineering claim.

Focused source checks: portable development runner, JIT off, threads 1,
180 s/953 MiB and fresh outputs. Independent source review checks work, path gates,
restart and shared-owner limits. One installed artifact checks the coherent slice.
Failure causes one targeted correction, not automatic budget growth. Retain logs.
Advance if these agree; otherwise isolate the mismatched contract before expansion.
