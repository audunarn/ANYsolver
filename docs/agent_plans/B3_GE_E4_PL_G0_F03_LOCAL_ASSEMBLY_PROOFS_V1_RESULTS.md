# F03 classical sparse assembly: bounded proof results

22 September 2026. **The new assembly, exact transfer, work identities and
synthetic condition probes passed their bounded checks and independent
review. G0B remains open; no scientific reference run is authorized yet.**

Source: `66b6e109516296bbf8c4ff4155f2aa96c3701d1a` on
`codex/b3-ge-e4-pl-integration`. This builds on the accepted local operator
foundation at `7cb7b774`; its source and completed proof archive are unchanged.
All new implementation is private classical research tooling in `scripts/`.
It does not change native element equations, public APIs, defaults or version.

## What is now implemented

The sparse assembler combines the membrane stiffness and the same exact
finite-pad trace beam energy:

```
K = K_shell + integral B_trace.T diag(EA,GAS,EI) B_trace ds
B_trace q = (u', v' - theta, theta')
C q = A q(0)
KKT = [[K, C.T], [C, 0]]
```

Exact free-coordinate moment polynomials are formed on each positive station
interval before floating evaluation. The root has three independent pose
rows and an independently free transverse-slope row. The held `J/gamma`
convention remains. The transverse physical line load is pulled back through
the same area trace, using the fixed 48/64 load rules for checks.

Beam polynomial integration uses `p+3` Gauss points, with `p+4` as the
alternate check; exact coefficient-pair integrals provide a separate oracle.
The assembler creates sparse global matrices from bounded local blocks,
performs no factorization and computes no physical equilibrium. Its factory
owns the result; public matrix/vector properties return fresh copies and
diagnostics are immutable. Exact trace coefficients that cannot be represented
as nonzero finite binary64 values fail rather than disappearing.

The exact sparse transfer admits a target space only when all source cuts
are retained and target degree is at least source degree. It supports Q2
to Q3 despite their different nodal locations, as well as admitted conforming
refinement. It rejects refined Q2 as a complete-space replacement for Q3.
Checks cover full sparse `P.T K_f P = K_c`, `C_f P = C_c`, and
`P.T f_f = f_c`, separately for membrane/beam energy, as well as exact
physical trace values and first/second derivatives of manufactured fields.

The independently authored work oracle verifies cell divergence, both
interior jump orientations, supported/free edge work and force/moment lifts.
It retains `j=(T_plus-T_minus)n`, both endpoint atoms, the eccentric moment
arm and represented rigid yaw factor. Its current load domain is constant
line-density triples plus two atoms; general recovered polynomial/cosine
functionals are still open.

## Numerical-certification progress and limits

`B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_ADMISSION_DRAFT.md` derives two possible
2-norm condition upper bounds: a complete inverse-column residual certificate
and a factor-comparison certificate with a verified factor residual. Both
preserve the old `1e10` condition and `1e-8` amplified-backward thresholds.
The backward-error denominator uses a lower matrix-norm bound, so it cannot
artificially reduce the reported upper error.

The new executable comparison uses exact rational residual arithmetic on
synthetic matrices with a hard **64-unknown limit**. It exercises symmetric
and nonsymmetric three-root saddle systems, permutations, inaccurate factors,
singularity, pessimistic bounds and backward-error failure. It includes
synthetic linear solves; it does not solve the physical reference problem.
Dense arithmetic here is a bounded mathematical probe, not the scalable
sparse certificate implementation. Neither method is selected for science.

Independent review found that a sparse canonical-format flag did not ensure
valid storage. Five regression cases failed before correction, safely stopping
at mocked native traversal. The corrected probe copies and validates bounded
CSR/CSC buffers, pointer ranges and strict index ordering before conversion.
The failed and corrected logs are retained.

Resource fields are construction estimates. They do not certify actual
process memory, sparse factor fill, certificate workspace or archive growth.
The transfer's construction budgets also do not independently bound its
exact-vector application storage. Those remain numerical-protocol duties.
Extreme-value outward square-root conversion can fail conservatively; it
cannot return an uncertified bound as a pass.

## Verification and independent review

All **37 distinct current tests pass**:

| Group | Passed | Final log |
|---|---:|---|
| Sparse assembly, ownership and representation | 10 | `local-assembly-representation-53598cf3de98408fbd3a705da46f3688.log` |
| Exact transfer and complete sparse operator identities | 6 | `local-prolongation-operators-b4116bb863b6486686d94e8f76a3a7ec.log` |
| Manufactured exact work oracle | 7 | `f03-local-work-final-20260922.log` |
| Corrected condition probes and sparse input validation | 14 | `local-condition-structure-fixed-3df34a512f264b1c802563018f0994ab.log` |

The intermediate integrated 22-test run and later affected checks overlap;
they are not summed. Parent numerical test commands fixed the five numerical
thread caps at one. These are correctness tests, not performance measurements.

`finite_pad_axis_review` independently accepted the assembly, transfer,
work oracle, condition-probe mathematics and final corrected source bindings.
`f03_port_mechanics` independently reviewed the numerical-admission derivation.
The parent reviewed the certificate formulas and added three-root and
malformed-buffer adversarial tests. The final reviewer found no remaining
blocking issue within this bounded scope. Its decision leaves scientific
numerical admission and physical acceptance open.

The first work test also had an incorrect expected reaction that omitted
panel edge length/free-edge traction. The failed expectation and its correction
are preserved; no physical law changed to satisfy that test.

## Preserved evidence and next step

Root: `.qualification/b3-ge-e4-pl/f03-local-assembly-proof-v1`.
It contains ten source/contract/test copies, fourteen raw development logs,
the manifest and review record: **26 bound files plus the inventory itself**.
All listed sizes and hashes were verified. Do not extend this completed root.

- Inventory SHA-256:
  `d02087acd268b0c55cf173582ff0d08a79d20cf71b9b4f7cbb1cc1fd4bfdbf46`.
- Manifest SHA-256:
  `92ddda029971910b6a5116994c1b1c4f3b6192527fa5705f26cc67d3aa0c2021`.
- Review SHA-256:
  `cca25c1145932e5fb47d0bbad27155e7b4808f09465e0117abf41ddbeaf8b530`.

Next implement the scaled sparse solve and a defensible sparse positivity/
condition certificate, with bounded saved verification data. Extend physical
recovery to the full piecewise functional and independently verify stress-jump,
support-reaction and endpoint bookkeeping for that general recovered load.
Then select and freeze the conforming nested case family, integration,
conditioning method, resource limits, archive and adjudicator in an independently
reviewed numerical protocol before a new scientific registration.

The original physical settling criteria, 45 scalar observables and full-H1
functional criteria remain unchanged. All old failed or consumed evidence
remains unchanged. No external comparison, practical-scale run, installed
qualification, native capability acceptance, main merge or release occurred.
Main was observed clean at `be41a77a62e1cd7e1767bda6e955253af0819f91`, matching
the locally cached `origin/main`; no fresh remote fetch was performed.
