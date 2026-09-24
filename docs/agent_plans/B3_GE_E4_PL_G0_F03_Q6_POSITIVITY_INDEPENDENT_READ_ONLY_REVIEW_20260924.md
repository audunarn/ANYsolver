# F03 Q6 positivity saved-replay read-only review

**24 September 2026. Independent diagnostic review, transcribed by the
integration owner. No formal G0 approval.** The reviewer did not edit source
or evidence. Scope was the experimental sparse positivity verifier, bounded
archive, source runner, saved-only replay and fixed X0/X1/X2 receipts.

The reviewer decoded and rehashed the three saved matrix/factor archives,
raw inverse files, and current runner/replay/proof/archive sources; checked
positive diagonals/scales, complete permutations, all inverse columns, proof
dictionary equality, supervisor completion, and parent/child measurement
identity. The exact-Fraction sufficient ratios recomputed as approximately
`1.637e-13`, `2.162e-13`, and `4.285e-13`. No false-positive path was found
for the fixed-size saved-matrix proof.

The review initially found a parent/child source-measurement race and missing
inverse-inventory checks. The replay was corrected to pass the parent's
expected measurement hash to the child, reject a mismatch before proof or
measurement output, require source attempt/start agreement, and check inverse
bytes, block count and complete column inventory. The three final replays
used this corrected code and passed. Focused affected tests passed 62/62.

Remaining findings:

1. The archived scaled matrix and displacement scale are not independently
   bound to the physical Q6 shell assembly. The proof applies to the saved
   matrix, not automatically to all physical outputs.
2. Replay uses the same experimental compiled arithmetic and certificate
   implementation. Formal independent arithmetic review, exact runtime and
   installed artifact identity, owned regular-file evidence handling, and
   one-use scientific registration remain pending.
3. Signed physical-observable error propagation and full native interface
   mechanics remain outside this positivity diagnostic.
4. The full integrated X2 resource envelope is unmeasured. Separately adding
   the X2 proof time to the earlier integrated route suggests a possible
   1,800-second limit overrun; this is a scheduling estimate, not a measured
   failure or a license to relax the limit.

**Decision:** Accept the narrow source-level three-grid saved-matrix
positivity *feasibility* finding only. Keep F03/G0B open and G1 barred.
