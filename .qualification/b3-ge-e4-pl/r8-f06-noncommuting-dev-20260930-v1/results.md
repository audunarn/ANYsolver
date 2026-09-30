# F06 noncommuting loaded-history discriminator — failed development case

**F06 remains open.** This fixed case failed its purpose; it does not establish
a formulation failure. No criterion, load, iteration budget or coverage floor
was adjusted after a physical outcome. No acceptance or speedup is claimed.

Product remains `0da6cd12b755ab78b9634e2a4b5b880058f2e457`; base integration
commit `abfd69be4137e70ecbf5b4f999c4b90c95022257`. Both installed runs reuse
the byte-identical solver wheel SHA-256
`314ea0dffd9c5fa7f70b80538373e42ffd10b5083f231b69a8bd4784773b1a2d`.
Each has exact input/test/runner hashes, prospective active note, original
log/junit, dependency/import/settings records, supervision and two raw reports.

V1 stopped at reference admission: analytic sine triads did not match the
native Q2 interpolant tangents, whose shared derivative was discontinuous.
It performed no equilibrium calculation. Original source and raw errors remain.
One independently reviewed setup correction replaced only the reference arc
with the globally quadratic `(x,-.5+.08*x*(2-x),.1+.12*x*(2-x))`, exactly
represented by both native elements and C1 at their shared station. Native
frame guard, load, thickness, section, supports and all thresholds stayed fixed.

| V2 outcome | Selected Q4 | All S3 |
|---|---|---|
| Accepted physical factors | .25, .5, 1 | None |
| Failure | Insufficient rotation/commutator coverage | First .25 Newton iteration limit |
| Maximum shell / beam rotation | .005697 / .005105 rad | Not measured |
| Maximum shell / beam commutator | 7.2134e-8 / 3.3023e-8 rad | Not measured |
| Frozen coverage bounds | .05 rad / 1e-5 rad in both domains | Same |

Q4 reached actual reset, direct restore and continued states with small observed
differences (largest continued normalized comparison ~5.54e-14), preserved
predecessors/history and observed physical balance. Its coverage assertion
failed before later predicate assertions; favorable raw values are not a complete
test pass. Native total strain energy is explicitly unmeasured. S3 has no accepted
branch or coverage. The v2 inventory is 2 failures, zero errors/skips, 25.256 s
and observed peak process-tree RSS 220,409,856 bytes; one thread/JIT off.
V1 took 3.610 s and 211,488,768 bytes. Both stayed below 600 s/8 GiB.

Decision: retain the unresolved loaded-history obligation, stop this fixed
fixture investigation, and advance ready B2 consumer mass/modal persistence.
Do not automatically scale loads, add iterations, shrink coverage bounds or
launch a refinement sweep. A future F06 action must name a discriminating
equation/capability/reference, not rename the same failed investigation.

The exact v2 source is retained as an explicitly selected development diagnostic
at `scripts/diagnostics/b3_e4_f06_noncommuting_history_dev.py`, SHA-256
`f50925608bb202cd9d16fbd5541c7ce7094761a37a9395d95bfc6b606016f0c6`.
It is not an ordinary passing regression, nor hidden as an XFAIL or skip.
Frozen test-input copies remain the actual run sources. Historical one-use
F06/F03 authorities were not executed. Main and existing product defaults are
unchanged.
