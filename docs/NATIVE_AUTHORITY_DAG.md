# Native authority matching

The native source guard retains its original per-64-element cancellation safe
points and its checks around caller observations. It validates the same class,
MRO, descriptor, function code/default/keyword-default/closure and global-binding
facts. Numerical recovery, probes, eligibility and tolerances are unchanged.

Captured expected callable facts are immutable tuples. Identical nodes are
interned using identities, including each child predicate and generation-counter
flag; identity-only cyclic leaves remain separate from full function predicates.
No captured object's equality or hash method participates in interning.

Each native guard allocates a fresh matching memo. It validates the optimized
matcher with the unchanged literal boundary predicate before using it, then
checks every original helper's globals. Actual proof results and live metadata
are discarded on return. The existing response binding also rejects replacement
of the captured helper-plan tuple. There is no persistent actual-proof cache or
new trusted execution span. As before, no guarantee is added to observe every
transient cross-thread mutation inside one private validator invocation.

The new matcher also records absent global names, including references inside
nested code objects, so injected builtin shadows cannot alias memo keys or skip
predicates. The same complete presence policy applies to reachable new matcher
functions in the existing response checks around callbacks. Existing helpers'
global-binding policy stays unchanged. Memo entries retain strong references to
both the actual callable and its expected node.

The adopted repair follows a physical 129-member profile retaining original
E4808 geometry, IDs, section and loads. Its profiled export attributed 3.586 s of
4.293 s to native-authority validation, versus about 0.083 s for HDF callbacks.
Profiling changes absolute timing; these figures establish attribution, not
unprofiled throughput or scale acceptance. Failed readiness evidence is retained.
Focused differential tests use the unchanged boundary predicate as oracle.
Independent review, full-scale performance and final acceptance remain separate.

The final isolated wheel repeats that physical profile with unchanged guard
counts (100 native checks, 64 numeric-tile checks). Profiled export took 2.289 s;
native validation accounted for 1.592 s. All 16 case records, 224 float64 field
arrays (41,280 values), 14 association tables and six geometry arrays matched
the preserved original-source archive exactly through the public reader.
The remaining validation cost is material; no full-scale performance claim is
made. Source and installed focused checks include builtin-shadow injection,
callback mutation/restoration, cancellation and atomic refusal. OpenAI owns
this coupled guard/consumer integration under root's explicit source contract;
Mistral was unavailable and prohibited for this task.
