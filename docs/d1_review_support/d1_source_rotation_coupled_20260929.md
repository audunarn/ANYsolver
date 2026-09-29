# Free source-bending coupled press — bounded development result

**29 September 2026. No production mechanics change; no D1 acceptance.**

The current four-Q4/two-S3 deformable-target cycle fixes all source rotations.
Local eccentric probes verify source-director contact work at imposed poses,
but they do not show a coupled equilibrium with moving source directors.
This slice freed source `ry` at interior Q4 nodes, kept `ry` fixed at the
left source support, retained the other guide and target constraints, and
used the existing 0.3 N total force, fine nodal Q1 pressure, monolithic
active-set law and 50 µm physical-gap budget. All runs used the same
180 s / 1 GB process-tree cap and one BLAS thread.

| Source / loading | Outcome | Elapsed / peak RSS |
|---|---|---|
| 4 Q4, two force steps | First step rejected: backtracking failed | 15.00 s / 275.49 MB |
| 4 Q4, four force steps | Same first-step rejection | 15.06 s / 282.68 MB |
| 4 Q4, four steps, read-only swept trace | Last fraction zero as independent gap approached −50 µm | 14.86 s / 280.58 MB |
| 8 Q4, four steps | First-step inner active-set predictor exhausted 12 pivots before a swept trial | 6.14 s / 275.46 MB |
| 8 Q4, temporary current-active-set Newton direction | Predictor bottleneck passed; first step still rejected at the −50 µm gap wall | 56.83 s / 370.61 MB |

The first eight-Q4 attempt had a probe JSON serialization error after the
solver returned its pivot-limit result. The traceback and resource record are
preserved; the corrected probe reran the same mechanical inputs and recorded
the result. Early probe versions returned process code zero for a mechanical
`diverged` result. The current probe writes the result and then returns a
nonzero code for noncompletion. The JSON `status`, not the old process code,
is the mechanical outcome.

The four-Q4 sweep trace shows the geometric lower gap progressing from
`−4.8164e−5` to `−4.9993e−5 m`, while proposed Newton endpoints were near
`−1.8928e−4 m`. At the last iterate, weighted nodal gaps were positive and
the reported active set was empty, despite two small positive algorithmic
forces. The conservative swept gate therefore correctly forbade a step that
would exceed the declared physical-gap budget. Halving the force increment
did not resolve this.

The unmodified eight-Q4 solver returned a twelve-set `pivot_trace` with no
settled predictor. A temporary one-line patch took the Newton direction
for the *current* active set and retained the existing line search, candidate
transactions and gap gate. This advanced to 14 nonlinear iterations and
two active pressure modes, but again reached the physical-gap wall:
last swept fraction zero, current lower gap `−4.9999025e−5 m` and proposed
endpoint `−7.88228e−5 m`. The exact temporary
[patch](d1_current_active_experiment.patch) is retained; it was removed
from production source. It is not a qualified semismooth alternative.

The contact-free reduced stiffness had one near-zero mode in both the original
guided and free-interior-`ry` models. The additional bending eigenvalues
were positive, beginning at 0.225; this check does not identify an added
rigid mechanism. The coupled failures are more directly explained by the
recorded pivot and physical-gap controls. Neither the 4- nor 8-Q4 experiment
accepted a step, so no source-moment or settled-tangent claim follows.

**Decision:** stop load-step and x-only refinement on this profile. The
combination of positive weak gaps and an independent physical-gap wall needs
a contact-resolution or enforcement derivation, followed by a bounded
coupled test. The predictor pivot issue is a separate algorithmic concern;
improving it alone did not make this case admissible. Preserve the rejected
profile as a D1 gap. Do not loosen the physical-gap target or silently
discard supported pressure modes.

The [probe](d1_source_rotation_coupled.py), [four-Q4 trace](d1_source_rotation_coupled_trace_20260929.json),
[unmodified eight-Q4 result](d1_source_rotation_coupled_8q4_v2_20260929.json),
[temporary-Newton result](d1_source_rotation_current_active_20260929.json)
and adjacent `*_resource_20260929.json` / `*_log_20260929.txt` files
preserve the raw results and failures. Source base was `7e995dc0`; the
temporary production patch is explicit above. The present probe SHA-256 is
`6d59ae4a2105985b0b9e5a5f22befcc1e6cc0aa762d6e81a1e96fdb3dd85a64f`
after the reporting-only exit-code correction.
