# S3 E4-PL V6V package and activation-gap audit

V6V audits the exact V2D candidate after the accepted V6T cache repair and
V6U Stage 4B performance successor. It does not change mechanics, aliases, or
defaults.

Build one wheel from a clean Git archive of the frozen execution commit without
build isolation. Install it with no dependency resolution into a fresh external
target, then run an isolated smoke process outside the repository. The smoke
must prove that `anysolver` originates in that target, that
`e4-pl-s3-v2d` constructs the native V2D class, and that its formulation-aware
serialization round trip is exact. It must also prove that Q4 remains `e4-pl`
and S3 remains `legacy-s3` by default.

In parallel, run the frozen focused parity lane covering offset/load/restart,
activity/contact/batching, dynamics/buckling/recovery, the V6T global cache,
and V6U authority and closeout checks. Both children have one numerical-library
thread, a 24-GiB process-tree memory limit, and a 600-second wall limit. No
automatic retry is permitted.

Two independently executed standard-library checkers must accept the canonical
audit common record and produce byte-identical outputs. The common record binds
the package artifact and logs by hash while excluding raw timings.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V6V_PACKAGE_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V6V_PACKAGE_RESTART_OR_BATCH`
3. `PROVISIONAL_GO_E4_PL_S3_V6V_FINAL_QUALIFICATION_PREPARATION`

A pass authorizes preparation of a final evidence-composition qualification
gate only. It does not activate S3. The V6P NO-GO and V6Q process incidents
remain immutable; V6R is the accepted successor decision for the corrected
25-percent spatial gate. ANYmesh is untouched.
