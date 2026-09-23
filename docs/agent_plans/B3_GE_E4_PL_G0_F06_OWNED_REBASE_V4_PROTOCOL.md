# F06 v4 candidate: owned loaded chart rebase and restart

23 September 2026. **Proposed executable contract, not a frozen execution
registration or an F06/G0B acceptance.** V3 proved equivalent descriptions
of the same loaded Q4/S3 poses but did not issue a rebased state. V4 must
exercise an owner-controlled accepted-state transition and subsequent trial
work. A representation-only replay does not meet this contract.

## Bounded case and identities

Begin with the v3 curved S3-V2D native generalized B3 + variational-shell
fixture, including its eccentric point joint, nonzero dead loading, and two
actually accepted targets at `0.5` and `1.0`. Use a distinct third target,
provisionally `0.75` (loaded unloading); freeze its value and positive lower bounds on the
incremental shell/beam rotation, multiplier change, work and reaction change
before scientific execution. Both cursor-3 paths must actually accept a
measurably changed state. Record shell layer
strain/stress, native beam histories, physical poses, point gap, supported
force and moment reactions, shell/beam work, and the full constrained
residual at cursor 2. Freeze the source graph, third target, package imports,
case inputs, numerical scales, limits, and runner hash in a one-use
registration before any v4 qualification run.

The prototype rebase owner has a separate profile/checkpoint schema. It may
restore the legacy state as an input only through the existing validated
owner; it must not reinterpret or change legacy V1 checkpoint bytes. The
new owner owns physical poses, shell chart anchors and local increments,
the accepted shell material origin/history, beam retained variables and
histories, multipliers, accepted cursor/controller and constraint-scale
identity, and the accepted generation. Its direct accepted-state snapshot
contains these fields. An issued rebase is an atomic same-load-position accepted event,
with a new hash-bound checkpoint. The authoritative accepted head and
generation are **per owner instance**: compare the predecessor generation
with that head under the owner's commit lock. A fresh owner may intentionally
branch from the same validated checkpoint, so no process-global conflict
claim follows. Within one owner, a stale predecessor cannot commit, and a
rejected or cancelled event cannot partially issue state or advance the head.

## Required paired paths

From the identical accepted cursor-2 predecessor, run a control path with
its original chart and a rebase path whose shell anchor absorbs the current
physical rotation while the local chart increment resets. Both paths then
continue to the same third nonzero target. For the rebase path, restore the
new checkpoint directly into a fresh owner's accepted-state snapshot before
continuing; replay of the earlier complete loading history is a separate
diagnostic oracle, not the normal restore path. Every shell, beam, joint,
load, support, recovery, and trial evaluation must consume the new anchor;
substituting the old additive owner after rebase is invalid.

At rebase and after continuation, compare independently scaled translation,
rotation, force, moment, work/energy, gap and residual quantities. Require
finite values and normalized differences at most `1e-9` for the registered
well-conditioned case, with explicit absolute floors set before the run.
Compare every recovered S3 layer strain/stress and native beam section
response before and after rebase, and after the paired third steps. Shell
and beam material histories must retain their canonical accepted meaning;
compare their full bytes at the rebase and use the registered physical/state
parity criteria after continuation where byte identity is not promised.
Check the first variation and chart-transformed tangent of the actual shell,
beam, joint, external-load and assembled residual through physical-direction
perturbations at the rebased state and at a nonzero post-rebase trial.
Require the programme's `1e-6` elastic directional plateau, with the exact
perturbations and normalization frozen before the run. Physical force and
moment balances and virtual work must
meet the programme's `1e-8` scaled criteria. Check chart-domain validity,
third-step convergence, accepted cursor and checkpoint identity.

Inject cancellation immediately before rebase commit, same-owner
stale-generation commit, bad external checkpoint hash, and a modified chart
anchor with a recomputed payload hash. The last case must fail semantic
pose/state validation, rather than merely the byte hash. Each must reject
without issuing a partial state; the original cursor-2 prefix bytes must
remain replayable. A cancellation after commit may return the complete
rebased prefix, without a duplicate generation. Record typed failures, not
a generic nonconvergence label.

## Decision boundary

Focused unit tests may establish implementation sanity, but only a frozen
one-use scientific run, independent mechanics/code review, and source/artifact
identity can accept this bounded S3 case. It still would not close F06:
Q4, straight/curved variants, **native beam chart transport**, larger
noncommuting rotations, multiple
accepted rebase events, rejection/cutback during loaded continuation, and
new mixed-owner integration remain to be verified. G0B and G1 stay open.
