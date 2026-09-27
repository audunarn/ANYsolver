# D1 distributed Q4/S3 full-cycle response: independent disposition

**Disposition:** independently accepted for the registered planar elastic
distributed-force **integrated response trend and active/open/active state
sequence only**. A complete contact tangent, split restart, installed package,
general C1 and release remain open.

The candidate source was `1cde0b431568a647dfaa38c32f303a4bb8ba9474`
(tree `f80356ed5f3534a02d878f503f1af9874b7253e1`). The
[registration](general_contact_d1_distributed_cycle_response_v1.json) was
committed before execution in `80f6557f`; its SHA256 is
`95c53a979ef3b9ee5196f79aedaabfcdcde9e8685912486cd1c39adf46a00ada`.
The formal command ran once from about 18:11 UTC on 27 September 2026 and
completed in 905.791 s under its 1200 s limit:

```text
PYTHONPATH=C:\ANYworkspaceWork\ANYsolver-general-contact\src;C:\ANYworkspaceWork\ANYsolver-general-contact
python scripts/general_contact_d1_mixed_mesh_jet2_schur_press.py 24 reports/general_contact_d1_distributed_cycle_response_v1_formal_20260927.json --four-phase --steps-per-segment 3 --load-profile distributed --total-force-n 0.3 --pressure-cap-pa 250 --schur-step-cap-pa 200 --target-right-x-m 1.3
```

The [raw 12-step report](../../reports/general_contact_d1_distributed_cycle_response_v1_formal_20260927.json)
has SHA256 `f4a3942b2bf3c0112f4774b6593464a80c8da479582b586eff7962570f935815`.
The [frozen adjudicator verdict](../../reports/general_contact_d1_distributed_cycle_response_v1_verdict_20260927.json)
has SHA256 `570d70cb411b8cca16827843378af9a2410525849e48dd951d6a03df4fc880d7`;
all predicates passed. Its `independent_review: pending` field records the
automatic adjudication state. This later review does not alter the verdict.

An independent read-only reviewer verified the source tree, eight code/runner
blobs, two prior development-report hashes, the load vectors and every
adjudication gate. The accepted full-load force was 0.1038788372552249 N
and first-unload force 0.0398439616559074 N. Their 16-to-24 mesh changes
were 0.007006% and 0.001840%; frozen prediction errors were 0.11856% and
0.03360%. The pressure Gram had rank 50/50 at all twelve steps. The cycle
pressed and slid with active contact, had zero contact force at steps 8–10,
and recontacted at step 11. Worst independent gap was −0.0202 µm, maximum
multiplier change 1e−10 Pa, and all registered equilibrium, wrench,
integration and support-balance gates passed.

The frozen prediction is an inverse-mesh trend from development runs, not an
analytical force oracle. The raw runner records Python and imported module
paths; the preflight/adjudicator checked package versions and source hashes,
but the raw JSON alone does not cryptographically attest the invocation or
process environment. This review makes no claim about untested geometry,
materials, finite rotations, friction, dynamics or applications.
