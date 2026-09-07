# GE-B3 installed covariance counterexample and arithmetic diagnosis

Status: **DEVELOPMENT INCOMPLETE — supplied-factor covariance**.
Independent review: **PENDING**. No public integration or qualification.

Frozen candidate: `a36baf8be16f4cac0c2c8f43060e66493bdafa49`, tree
`2fcba00faf7ab4077d24dd00426e38c3b6b29af2`. This checkpoint adds research,
package tests and evidence only. All existing source, including B2/B3,
Q4/S3, the accepted straight beam and the private V5 mechanics, is unchanged.

## Genuine failed package gate

The wheel was built once from the frozen Git source archive, using the
preserved UTF8-LF source checks and an explicit CRLF installed-text fixture.
An offline fresh virtual environment installed the wheel and hash-bound
dependencies. Its isolated worker checked 83 private source bindings and
forbade research imports and repository search paths.

The package test failed in **43.159 seconds**. Seven cases completed:
straight compression/tension, coupled curved pair, elastic unloading with
plastic history, free curved rigid modes, and extreme curved reference
E/R90 cases. The next case, reference general rotation at L/h=1,000,000,
failed its mode-shape covariance check. Two off-diagonal mass-correlation
entries reached **1.0179947345281053e-11**, outside the unchanged
rtol=atol=1e-11 gate. Eigenvalues passed the comparison.

The two finite-load contrast cases were not executed. The second worker was
not launched. No canonical result or successful receipt exists. Saved partial
case outputs are diagnostics only; they do not qualify the package. Each
subprocess had a 180-second wall limit and process-tree termination on timeout;
this was a small correctness test, not a resource/performance campaign.

Private wheel: `anysolver-0.4.2-py3-none-any.whl`, **1,429,058 bytes**, SHA-256
`1ef86122b5d35f9ccd35e3edf1e923c367cfcc4c284bef63223a9afdd3663e51`.
It must **never be published or replace the released 0.4.2 artifact**.

## What the diagnosis establishes

The installed fixture rotates each coordinate vector individually. The
earlier passing source fixture used a batched matrix product. A new tiny
diagnostic retained both calculation orders in both runtimes:

| Runtime | Per-node correlation error | Batched correlation error |
| --- | ---: | ---: |
| NumPy 2.4.3 / SciPy 1.16.3 | 1.01799823e-11 | 8.36466588e-12 |
| NumPy 2.5.2 / SciPy 1.18.1 | 1.01799473e-11 | 8.36464455e-12 |

Both use Python 3.13.9. Thus the discrepancy is reproducible in source and
installed environments; changing the numerical-library runtime is not the
primary explanation. Choosing the favorable coordinate-construction order
would hide the counterexample, not resolve it. Both remain in scope.

A new same-author standard-library Decimal audit reconstructs full mode
vectors from supplied material and kinetic factors, including exact-float
conversion, massless-trace elimination, mass Cholesky whitening and cyclic
Jacobi eigenvectors. It does not import production mechanics or numerical
libraries. Four known-pencil/import tests and two captured-factor audits
passed (**6 tests**, separate from the failed package inventory).

For each E/general and per-node/batched factor set, 60- and 90-digit lowest
six roots and full mode columns agree to absolute 1e-30 after sign alignment.
The native modes match the audited supplied matrices to at most
**6.661338147750939e-16** in mass correlation. Nevertheless, the audited
per-node matrices have covariance error **1.0180001934860438e-11**. The
audited batched comparison gives **8.364610433838844e-12**.

This separates the current failure from the numerical eigensolver: the
sensitivity already exists in its supplied matrices. It does not yet isolate
which reference/kinematic/constitutive construction operation causes it, prove
a physical formulation defect, certify intervals, or constitute independent
mechanics review. Precision agreement and a correct arithmetic reconstruction
must not be relabelled as beam qualification.

## Preservation

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-reassembled-installed-failure-20260907-1ef86122b5d3`.
It contains **62 files, 5,274,537 bytes**. Every file was checked against its
original and then rechecked in the ordinary workspace context. The canonical
evidence binds the six new sources, both JUnit reports, frozen source zip,
private wheel, source map, subprocess logs, partial case files, runtime
captures and Decimal audits. Original temporary evidence, build and installed
environment remain. Only verified relay duplicates may be removed.

A staging path-list expression briefly selected a directory instead of the
audit JUnit file. The new empty staging directory was removed and the actual
report copied; no test or scientific artifact was rerun or modified. The final
inventory is verified file-by-file. No resource request or ledger was changed.

## Next gate

Investigate representation of the common kinematic map and constitutive
factors before expanded floating-point rows are formed. In particular, test
whether retaining the factor chain avoids losing small coupled terms when
large axial/shear coefficients multiply shared kinematic rows. This is a
diagnostic hypothesis, not an accepted correction.

Keep both coordinate orders, the same tolerance, original evidence and failed
package harness. Any numerical successor needs expanded source checks before
another frozen artifact gate. No second failed-wheel run is authorized by this
record. Broader curved/slender stability, nonlinear sections, V5 continuation
parity, objective beam-shell connections and independent review remain open.
