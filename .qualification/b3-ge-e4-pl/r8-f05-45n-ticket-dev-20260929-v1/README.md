# R8 F05 low-yield development ticket

Source HEAD at execution: `262f1ae2`. Runner:
`scripts/b3_e4_f05_45n_trial_diagnostic.py` (final SHA-256
`9b275b5229a5ed5bb0cd9b22631932bb547d573f06b37bbc1f88c865e6439177`).
The input is the accepted 40 N
checkpoint from the preserved R7 path; its SHA-256 is
`d3a5bd6af2cb2494c58714c9cc961bf27c2634101785b1406f3b04090d009bfa`.
The worktree's `.venv/Scripts/python.exe` ran with OpenBLAS, OMP, MKL and
Numba thread environment limits of one; the process reported two OpenBLAS
pools with one thread each. No other heavy numerical job was launched by this
ticket. The original dirty F03 script was untouched.

Reproduce from this worktree with the same input and a new output filename:

```text
.venv/Scripts/python.exe -B scripts/b3_e4_f05_45n_trial_diagnostic.py .qualification/b3-ge-e4-pl/r7-f05-low-yield-step-path-dev-20260929-v1/path-j2-5n-to50-stable.checkpoint <new-output.json>
```

Set `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and
`NUMBA_NUM_THREADS` to `1` in that process before running.

`diagnostic.json` is the first run. `diagnostic-v2.json` adds free-equation
derivative and nearby-merit measures without changing the trial. The latter
has SHA-256 `59eee47bb2b584f5b514248c6b32311884c39c4c45ba1a19af437d04b9abc262`.
Both reproduce a 45 N backtrack-budget failure after 163 assemblies and keep
the 40 N checkpoint byte-identical. At the last Newton base, merit is
0.1069403002. The smallest permitted alpha, `2^-12`, gives 0.1069406275,
while alpha `1e-4` gives 0.1069340574. The central merit slope at `1e-5`
is -0.1069642; the free-equation tangent discrepancy there is 0.001229.
The shell's count of positive stored alpha values stays seven in that
derivative check. A still smaller perturbation has worse derivative accuracy,
so this does not prove a tangent plateau to the F05 criterion.

`cutback-42p5-to45.json`, SHA-256
`d2a4f71aea033613b765b19b44201c14b035a6218b102de698793da7bb3444ba`,
records one 40→42.5 N cutback with the existing 20-iteration/12-backtrack
controls. It reached the Newton iteration limit before 45 N was attempted;
the accepted 40 N checkpoint remained byte-identical. Its `elapsed_s: 0`
was a runner reporting defect in the early-return path; the command wall
time was 27.4 s. The runner now records elapsed time for that path.

The specific disposition is an open material/driver ticket. The evidence
supports neither a physical limit point nor a material-law defect and does
not qualify the 20 kPa shell material path. The M1 elastic workflow can
advance while F05/G3 and the material branch remain open.
