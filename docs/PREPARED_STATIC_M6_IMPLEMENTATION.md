# M6: reduce acceleration preparation work

Implemented on the isolated prepared-static candidate. This is an implementation
and correctness result, not a performance screen or release qualification.

The only product delta from the frozen M4 source is
`src/anysolver/prepared_static_loads.py`. The unused global acceleration basis is
removed. Native mass matrices are captured once into immutable private storage;
the independent native full-load oracle remains. The three unit-axis capability
checks now apply the captured matrices instead of assembling native mass again.
Runtime `evaluate_load_vector` and `_verify_maps_against_oracle` are text-identical
to the baseline. No default API, pinned formulation or factor ownership change.

On the focused acceleration-only beam fixture, code-event instrumentation counts
two native mass evaluations (capture and independent oracle) and one full native
assembly. The old five mass passes are established from source, not a timed run.
This does not establish an end-to-end speedup.

## Correctness and review

Independent review found and resolved one refusal regression: invalid mass could
escape from later oracle verification and prevent otherwise usable nodal loading.
The repair preserves the original unit-load finite-output boundary using captured
matrices, including NaN/Inf and finite-matrix accumulation overflow. It does not
add a stricter blanket matrix rule. Failed evidence and expected warnings remain.

Worker checks (NUMBA_DISABLE_JIT=1, single-thread):

| Attempt | Test executions | Process-wall seconds |
| --- | ---: | ---: |
| m6-solver-01 | 6 passed | 3.7410248 |
| m6-solver-02 | 65 passed | 22.6023992 |
| m6-solver-03 | 31 passed | 14.4853677 |
| m6-solver-04 | 9 passed | 3.6899692 |
| m6-solver-05 | 18 passed | 5.6500886 |

These are 129 passing executions, with repeated selections, not 129 distinct tests.
Total worker correctness charge: 50.1688495 / 120 seconds.

Root independent checks (NUMBA_DISABLE_JIT=0, single-thread): first attempt had
2 passed and 2 failed in 15.8935433 seconds. Both failures were a test-harness API
error (`mesh.add_point_mass` instead of `model.add_point_mass`), before numerical
execution. Corrected two checks passed in 4.1538067 seconds. Total root charge:
20.0473500 / 60 seconds. All four independent checks now pass. The two unchanged
passing checks were not repeated.

Independent coverage includes full-load binary equality for Q4/beam and S3 cases,
all signed acceleration axes and a general vector, mixed pressure/nodal loads,
structural and case-added masses on constrained DOFs, source mutation/deletion,
canonical governing envelopes across blocks 1/8/32 and restart, independent output
selections, constrained reaction truth and returned-data mutation.

Final source SHA256:
`52e00c5fa62244b2e2597418d4ba92a078d772630116465387445ac8650cfef3`.
Independent bounded Read review reports no unresolved finding. Source identities
were stable during checks. Existing interpreter startup warnings are preserved in
stderr; successful child execution and JUnit results are recorded separately.

## Evidence and remaining work

Relative to `C:/ANYworkspaceWork/prepared-static-20261008`:

- `evidence/M6_IMPLEMENTATION_RESULTS.json`: source delta, runtime/oracle identity,
  exact check commands via run records, counts and accounting.
- `evidence/checks/m6-*`: complete attempt logs and machine-readable records.
- `solver/.prepared-static-evidence/m6-solver-handoff.md`: selections and handoff.
- `fem/.prepared-static-evidence/prepared-m6-independent-review.md`: finding/repair.
- `m6-baseline/solver/src`: preserved pre-change M4 source.

No M6 benchmark ran. The requested new 120-second benchmark allowance remains
pending explicit response; the prior representative ledger stays stopped at
117.3583302 / 120 seconds. No measured performance or 10,000-case claim. M5 remains
inactive with its failed evidence preserved. No commit, merge or push performed.
All work remains in the isolated candidate; unrelated main-checkout work is intact.

### Subsequent benchmark update

User renewed120seconds after the implementation report. The bounded screen is now
complete:108.6796952seconds used; see PREPARED_STATIC_M6_SCREEN.md. Earlier pending
status above records the implementation handoff, not the current authority state.
