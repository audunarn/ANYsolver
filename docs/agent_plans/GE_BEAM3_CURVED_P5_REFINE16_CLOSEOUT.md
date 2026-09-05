# P5 sixteen-element refinement closeout and continuation checkpoint

Recorded 2026-09-06. This is a same-author research diagnostic closeout, not
independent mechanics qualification or production authority.

## Preserved authority and execution

Frozen implementation: `a38532d467ed6e7f4646ab5949a837860c08ad58`, tree
`b181f26dd13c524be6911f1febfad34d63741c17`. The four-path scope and unchanged
scientific recipe remain in `GE_BEAM3_CURVED_P5_REFINE16_PLAN.md`. That plan,
the programs, and tests are not edited by this closeout.

Consumed request: `f6dc1c5fbe064f6d968cb1e546c54ca2`, 660 bytes, SHA-256
`85F008661F02F6DA51AF6C0790646B1650EED2D19CC5729843EEF5E428790251`.
The administrator approved its exact stored command. It ran once from the
clean frozen worktree, under the global resource lease. The preserved command
session reported exit 0 and release in its external owner's finally block.
Do not retry this request or remove its one-use central claim.

External evidence root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-refine16-20260906-d15f8495ad294494b65e402b34f07745`.
There are 38 files totaling 13,974,640 bytes, including 18 full step records.
No raw evidence is copied into or removed by this commit.

Canonical aggregate: `aggregate.json`, 1,698 bytes, SHA-256
`78B9B8353E0582F0042FFE1C1DCB38A7576468C8436F2872AC59AC577D54B8CA`.
It binds these complete worker records; each in turn binds its six raw steps:

| Worker | Complete bytes | Complete SHA-256 |
|---|---:|---|
| continuum256 | 2937 | `535B778EE75C6982F7B7A0944D0A89634CEDC51F84651AF5B4796293DBD5AB9D` |
| elements16_order8 | 3012 | `88A24B645AC6D6D4977F5CB952C47BEDE64B21FA04F080776EF0AA26BC4E679E` |
| elements16_order24 | 3014 | `1E22C8E64C994DCD71CAF85DCDE664CADB10EFFA4FA94A83B5BE77EB412E86B3` |

## Observed scientific result

Disposition: `RESEARCH_REFINEMENT_BELOW_2_PERCENT`.
Both discrete integration variants satisfy the frozen strict 2% tip-error
criterion at all six increments against the 256-step continuum history.
The following percentages are rounded displays; exact values remain external.

| Step | Load amplitude | Order-8 error (%) | Order-24 error (%) |
|---:|---:|---:|---:|
| 0 | 0.1 | 0.385166 | 0.385166 |
| 1 | 0.2 | 0.541317 | 0.541317 |
| 2 | 0.1 | 0.631581 | 0.631581 |
| 3 | 0 | 0.739303 | 0.739303 |
| 4 | -0.2 | 1.002982 | 1.003035 |
| 5 | 0 | 0.827908 | 0.827952 |

The largest relative tip difference between the integration variants is
`5.483088167438571e-7`, at reverse loading. This is not exact integration
equality, nor does it establish the general nonlinear quadrature gate.
The continuum reference is a separate implementation but not an independently
authored/reviewed multiprecision oracle. The experiment covers one height-0.4
parabolic member, one coupled directed-hardening law, and one fixed history.

The earlier eight-element errors (4.15% reverse loading and 3.42% permanent
set) remain genuine results. Refinement resolves this particular experiment;
it neither rewrites the earlier evidence nor qualifies coarse meshes.

## Process diagnostics and validation

Workers ran serially. Each exited 0. Approximate summed worker wall time was
127.03 seconds (about 128 seconds for the observed full wave), well within the
registered bounds. These are diagnostics, not paired performance benchmarks.

| Worker | Wall seconds | CPU seconds | Peak process-tree bytes |
|---|---:|---:|---:|
| continuum256 | 3.7341 | 3.609375 | 62320640 |
| elements16_order8 | 45.2943 | 45.125 | 143663104 |
| elements16_order24 | 77.9980 | 77.796875 | 146563072 |

Read-only post-run validation, performed while HEAD was still the clean frozen
commit, checked strict canonical parsing, all raw hashes, worker identities,
ordered station/force inventories, residual and local-health bounds, and
summary reproduction from raw records. Re-adjudication reproduced the entire
aggregate byte-for-byte. No mechanical solve was rerun.

The registered worker PIDs 12972, 36348 and 32072 were absent after completion;
the runner's process records are emitted only after whole-job drain. The global
lock was absent and the consumed claim remained preserved. The resource
administrator independently checked the saved record/hash/process inventory
and recorded `COMPLETED_PASS` for resource execution only. That ledger status
is explicitly not a scientific qualification approval.

The frozen pre-run test inventories remain separate: profile/runner tests
19 passed, existing assembly tests 20 passed. No new mechanics tests or second
refinement cycle were executed for this closeout.

## Resume here

Continue on `codex/ge-beam3-curved-p5-objective-lift-v1` in its existing worktree.
This closeout is a successor documentation commit; it does not replace the
run's bound implementation identity. No process remains to resume or rerun.

The next focused development task is an explicit assembled restart codec.
Keep the existing single-element schema unchanged. Bind complete connectivity,
per-element reference geometry/material triads, section identities, quadrature,
clamps, shared spatial rotation state, nested histories, and accepted origins.
Validate into a fresh isolated model; reproduce the accepted response without
Newton iteration before exposing any restored state. Reject pending, altered,
foreign, malformed or mismatched records atomically. Use small connected models
to compare uninterrupted versus restarted loading, unloading and reverse-flow
continuation, including late-element failure injection. Do not repeat this
16-element resource wave merely to implement persistence.

This proposed next gate does not itself authorize a new resource-heavy run.
Any such run needs a fresh exact request and administrator ledger approval.

The full goal remains incomplete: general nonlinear section adapters, broad
curved/slender engineering coverage, extreme coupled local failures, arc
length/postbuckling, prestressed modal/buckling and dynamics, independent
mechanics authorship/review, installed-wheel integration, and objective
eccentric/curved beam-shell connections remain open. Successful state
persistence alone will not close those gates.

`production_qualified=false` and `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
Existing B2/B3/Q4/S3 mechanics, defaults, production state/recovery and accepted
qualification evidence are unchanged. No selector activation, push, merge,
release or publication occurred.
