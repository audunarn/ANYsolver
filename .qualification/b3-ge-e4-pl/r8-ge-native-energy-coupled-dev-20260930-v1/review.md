# Independent review — native energy and coupled history

Reviewer `/root/anyfem_consumer` performed read-only solver design/code review
and artifact hashing without solver edits or numerical jobs. Root implemented
the solver change. The reviewer later authored only ANYfem tests; root inspected
their full diff and physical fixture correspondence before installed execution.

Energy formulas match the existing separate physical section entry: stored
energy minus previous hardening plus increment dissipation recovers the native
incremental material potential. Reference quadrature integrates energy per
length to joules; high/low pairs remain paired. Opt-in recovery preserves the
default response and avoids a second cell solve. Recovery is from the actual
accepted predecessor and station fields, not an elastic reconstruction.

Two V8 correctness findings were resolved before final source verification:
virgin S3 states are sealed to LINEAR only for the new fibre/J2 path, and saved
accepted S3 recovery fields are checked through complete same-predecessor
replay/sealing before publication. Generalized V5/V6 initialization and
validation remain unchanged. V8 chart-reset round-trip passes the bounded
source case; this does not establish broad finite-rotation qualification.

The final source review found no further consequential correction in the
compiled layout, counts/digest/shape checks, ownership, atomic publication,
typed history replay or bounded experimental claims. Q4 zero-alpha coverage,
simultaneous yielding and the earlier strong-yield/pure-S3 failures stay open.

The reviewer independently rehashed23/23 installed inputs, both wheels, and
all385 solver +97 consumer module entries against actual source/wheel/site:
zero mismatches. Source HEAD matched565685c1;279 imported paths existed onsite.
JUnit contains124 cases from the eight selected suites with no failed, errored
or skipped case. Two public history examples and actual thread/JIT/resource
records agree with the report. Manifest SHA256
`caeb1fa97e7306b9249f406cdde48bcaba506101ae6afada9be3c7fac39e8c0c`.

This is independent verification of the installed experimental slice, not
acceptance of G3, an untested material/attachment combination, or release.
