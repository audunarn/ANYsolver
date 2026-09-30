# Native beam energy and coupled shell material history — 30 September 2026

**Verified experimental integration; no scientific or aggregate gate closed.**
Solver product `565685c1ea6fa1a42509f132a8bd4396977ca709`;
ANYfem tests `933d4e5d201afc9c752af631cd6401fcff2a71b0`, runtime unchanged
at `a615c4b299e603264f67d292c8a4415168b1b9c6`.

The existing finite point owner retains shell and native beam material
predecessors and accepted histories together. Distinct V8 binary snapshots
carry compiled numeric layouts, native S3 states and predecessor chart bindings.
Restore re-evaluates the saved update and validates material/recovery fields
before publishing. V7 and generalized-only formats retain their contracts.

Native fibre energy is captured optionally from the same converged Decimal
station strains and accepted predecessor. Paired recovery records contain stored
material energy, previous hardening energy, last-increment dissipation and
incremental material potential in joules. They do not represent cumulative
dissipation, external work or total coupled-system energy. Default native cell
responses and legacy station recovery remain unchanged.

## Executed checks

- Focused source: **10/10**, 87.27 s. Native energy against the separate section
  entry, default payload parity, owned recovery, coupled histories, rejection,
  cancellation after recovery, corrupt/forged snapshot rejection, restart and
  S3 chart-rebase round-trip. The earlier energy screen passed7/7,32.41 s.
- Fresh installed solver: **124/124**,362.54 s, no skips/errors/failures,
  plus two public history examples. Includes affected native cell/retained
  operator checks and existing finite/linear/checkpoint regressions.
  Supervisor387.6940203 s,245346304 B peak process-tree RSS,exit0.
- Installed ANYfem: **7/7 selected**,5 unrelated deselected,73.23 s;
  four existing physical-fibre inputs plus three new coupled-material inputs.
  Supervisor76.7021729 s,218615808 B peak process-tree RSS,exit0.
  Public save/reopen, solve, V8 restore and resumed/uninterrupted continuation
  preserve raw native definitions and actual recovery. This remains the
  separate experimental input format, not ordinary native-project persistence.
- Actual Python3.14.2; one BLAS/Numba thread, JIT disabled. NumPy2.4.6,
  SciPy1.17.1,Numba0.65.1,pytest9.0.3,ANYmaterial0.2.0,ANYmesher0.5.0,
  ANYfileio0.3.2. **385 solver +97 consumer modules** match source/wheel/site;
  all279 solver-run and270 consumer-run imported modules resolve onsite.
- Solver wheel SHA256
  `b0f15d3ebc5b261f7baf620f7bcbf6866cd6a090b77760b503cfd20131f9dc87`.
  Unchanged consumer wheel SHA256
  `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.
- Independent code/mechanics and artifact inspection: no consequential finding
  remains within this slice. Parent separately reviewed consumer-author tests.
  See [review](review.md), raw logs, XML, identities, inputs and wheel bytes.

## Retained findings and limits

The first coupled source probe failed an **active-shell coverage assertion**:
the Q4 solve completed with fibre yielding but zero shell plastic accumulation.
Its original log remains; it is not simultaneous-yield evidence. V2 passed3/3
after correcting that interpretation and sealing only the new path's virgin S3
predecessor. V3 adds full forged-response rejection and chart/rejection checks.
Early probes retain logs and known inputs; no exact original full-source catalog
is claimed for each early probe. No material parameter, increment sequence,
equilibrium tolerance or scientific criterion was relaxed.

Review found and repaired first-step UNBOUND S3 predecessor restoration and
insufficient validation of ancillary accepted S3 recovery fields. V8 compares
the entire saved accepted S3 blob with the replayed, sealed native response.

Positive cases cover Q4 pure/mixed partial-fibre yielding with shell-J2-defined
elastic response, and mixed-family all-S3 active shell J2 with elastic fibres.
Simultaneous active shell/fibre yielding, strong full-section yield, pure-fibre
S3 robustness, total-system energy, broad chart/history coverage, attachment
families, external/scale/platform and final consumer/release acceptance remain
open. Passing truthful-failure tests does not qualify a failed physical case.

Initial evidence-directory creation was denied by the sandbox; the authorized
byte-copy was repeated with filesystem escalation. Numerical runs were not
repeated. Formal F03 authority and unrelated dirty work were untouched.
