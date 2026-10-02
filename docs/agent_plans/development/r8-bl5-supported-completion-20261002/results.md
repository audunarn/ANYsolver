# Supported completion action — 2 October 2026

The bounded diagnostic completed once using the frozen finest Fy/Mx/Mz states.
It reuses the mapped PL+HG matrix after exact shell-operator parity and protected
input checks. No element reassembly, coefficient change, new structural solve,
dense Schur operator or formal F03 execution occurred.

For supported physical coordinates p and unforced free normal-spin coordinates d,
one general sparse factor solves Ndd d_hat = -Ndp p. The saved spin state already
agrees with d_hat. The physical core has spin coupling only at subtractive
roundoff (scaled relative measure 1.18e-19).

| Saved action | Completion / shell work | Scaled free-physical action fraction | Completion constrained-shell Fy, N | Completion constrained-shell Mz, Nm |
|---|---:|---:|---:|---:|
| Fy | 0.0984317% | 7.88005% | -17.29522 | -0.2626342 |
| Mx | 0.000388530% | 1.37381% | 0.1799767 | 0.002827649 |
| Mz | 0.0972794% | 2.32963% | -1.062725 | -0.01762583 |

The wrench is the **completion resisting action on constrained shell coordinates**
about global origin [0,0,0]. It is not the total ground reaction or a
removal-induced change. Its origin must be transformed before comparison with
beam-axis-origin quantities. Other components are zero or roundoff.

All existing work controls pass, maximum 1.4051e-12 against 1e-8; sparse spin
balance is about 2e-16. Native accepted predicates and normalizations are reused.
One factor serves three actions. Effective BLAS pools each use one thread;
the seven observed process threads include infrastructure. Supervision recorded
0.5603 s and 61,796,352 bytes sampled peak process-tree RSS, within 600 s / 1 GiB.
These measurements are execution records, not performance gains.

## Decision and boundaries

Small work coexists with finite local action and substantial opposing root
partitions. This agrees with the earlier small work sensitivity and appreciable
root-transfer sensitivity. It does **not** establish drilling independence,
negligibility, or a causal fraction of the roughly 1.1% same-action US3 response
difference. The physical core and completion jointly supply equilibrium.

Retain the candidate and stop numerical-completion tuning, derivative repeats
and automatic axial/shell refinement. No changed connection law follows from
this result. The missing coupled physical comparison and growing-space stability
remain mandatory M2/F03 obligations; continue independent product delivery while
withholding those claims. Formal F03 remains UNCONSUMED.

The old component source's later derivative failure remains failed. Only its
earlier mapped-component reconstruction is reused, with the exact runner and
matrix identities recorded in raw output. No product equation/tolerance changed.

[Independent review](review.md), [raw manifest](raw-v1.json), [raw archive](raw-v1.zip).
Inputs remain in the protected endpoint and completion-sensitivity evidence
collections referenced by the raw hashes; the archive stores new run outputs,
invoked runner, launcher and execution record. Original temporary run:
C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-supported-completion-v1.
