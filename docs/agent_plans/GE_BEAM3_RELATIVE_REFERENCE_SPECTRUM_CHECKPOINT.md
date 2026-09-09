# GE-B3 relative reference spectrum V2 — 2026-09-07

Baseline `6c4baab141d5479b8009e7a80a9ac457e9c05830`, tree
`99ab3437f7276a17c29be73f7ed44de16d1457f6`. V1, the original dense solver,
all previous source/evidence and existing element mechanics remain unchanged.
Three new private modules add a numerical successor; no public selector,
default, dependency, version, state schema or quadrature changes.

## Remaining V1 error and numerical choice

The preserved V1 factor solver avoided normal-equation eigenvalues but still
used ordinary GESVD. In the one-macro slenderness 1,000,000 test, its first
two squared bending frequencies were approximately 0.7346933362 and
0.7347786383. This split exceeded the 1e-11 invariant check despite satisfying
the looser 2% engineering comparison. A small backward residual did not
establish forward accuracy of those low modes.

V2 retains the same QR trace elimination, kinetic-factor whitening, coordinates,
physical factors and full-pencil checks. It changes the final factor SVD to
DGEJSV. The source describes accuracy dependent on the scaled matrix's
conditioning, not an unconditional relative-error guarantee:
[LAPACK DGEJSV](https://netlib.org/lapack/explore-html/d6/d22/dgejsv_8f_source.html).

The option mapping was read from the official
[SciPy v1.16.3 wrapper source](https://github.com/scipy/scipy/blob/v1.16.3/scipy/linalg/flapack_other.pyf.src).
The wrapper maps CEFGAR in consecutive positions; UFWN and VJWN
are its vector-option maps. V2 explicitly selects G/U/J/N/N/N: row/column
preprocessing with an accuracy estimate, left vectors and explicitly accumulated
right Jacobi rotations, without optional column killing, speculative transpose
or structured perturbation. Driver errors and accuracy warnings fail closed;
there is no automatic driver fallback. Output shapes, finite values, scaling,
ordering, reconstruction and right-vector orthogonality are checked. Squared
frequencies that underflow/overflow are rejected rather than reported as zero
or infinity. The tested binary64 range is not a claim about every possible
subnormal or arbitrarily ill-conditioned input.

The guarded V2 native adapter accepts only exactly fresh, unloaded V4 reference
states and zero displacement. It retains model/section/inertia ownership and
post-solve guards. It rejects loaded, displaced and history-bearing states.
This positive-semidefinite reference path is NOT substituted for the signed
prestressed solver. Negative modes in that preserved solver remain intact.

## Numerical and engineering checks

The initial relative-SVD probe passed seven checks in 1.37 seconds, including
separate 100-digit Decimal closed-form two-by-two singular values and the
distinction between exact zero and a tiny positive singular value. Native V2
integration initially passed 26 checks in 6.65 seconds. The completed driver
checks also exercise deliberate error/warning, scaling, vector and spectral
mutations; each failed invocation is attempted only once.

At slenderness 1,000,000 the probe now returns first squared frequencies
0.7346938775499385 and 0.7346938775499399; the next pair is approximately
35.99999999962913 and 35.99999999962914. All three tested slendernesses
(100, 10,000, 1,000,000) pass the unchanged 1e-11 pair-equality check.
The rational one-macro thin limits remain 36/49 and 36 in both planes.
That discrete reference is not a continuum accuracy claim by itself.

Before the wider checks ran, the research test froze L/h=100 and1,000,000,
four/eight macros, the first three bending frequencies in both planes, and
the existing 2% finest engineering threshold. The section and reference
mass follow the preceding diagnostic's declared scaling. A separate continuum
Timoshenko/Simo-Reissner constant-coefficient ODE supplies the three roots in
fixed squared-frequency brackets [-2,4], [10,100] and [100,400]. No fitted
coefficients or automatic root search are used. This is same-author source
reconstruction, not independent review or interval-certified root counting.

The four engineering samples passed two tests in 5.46 seconds. At eight
macros, first/second/third bending-frequency errors were approximately:

| L/h | First | Second | Third |
| --- | ---: | ---: | ---: |
| 100 | -0.02812% | +0.42926% | +1.48016% |
| 1,000,000 | -0.02813% | +0.42945% | +1.48207% |

Both bending planes agree to 1e-11. Every error improves from four to eight
macros; four-macro third-mode errors are about 5.74% and are preserved, not
hidden or relabeled as qualification. These four small reference models have
at most 150 retained coordinates. They do not establish general nonlinear
locking freedom, coupled high-contrast covariance or curved-domain coercivity.

The final suite passed **87 tests in 71.41 seconds**, with separate inventories:
17 driver checks, ten V2 native-adapter, seven relative-probe, two new engineering,
26 preserved reference-path, 23 preserved loaded-modal and two preserved
prestress-engineering tests. The separate static inventory passed 23 checks in
0.50 seconds: six new, six V1 factor, six straight-prestress and five
loaded-modal checks. There were no test failures in this successor.
An auxiliary direct-Python inspection initially omitted ANYfileIO from its
source path and stopped at import; supplying the same path used by pytest
allowed that inspection to run. It was not a mechanics failure or formal run.

## Preservation and unfinished scope

Ten output pairs from fresh test directories are byte-identical: three relative
matrix/beam probe records, three actual native records and four engineering
records. All 20 files (7,414 bytes) were copied to an exclusive archive and
verified by bytes and SHA-256 from the normal workspace context:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-relative-reference-spectrum-20260907-afb2cbc20a24`

The canonical inventory binds eight implementation/test sources and the
Python3.13.9 / NumPy2.4.3 / SciPy1.16.3 runtime in
`docs/reference_cases/ge_beam3_relative_reference_spectrum_evidence.json`.
Original temporary outputs and historical archives remain; only verified relay
duplicates are removed. No resource request was consumed or reused.

Independent review remains PENDING. No installed-wheel check of these new V2
modules has yet run. Broader covariance and slenderness coverage, prestressed
high-contrast numerics, curved engineering qualification, general nonlinear
sections and objective beam-shell connections remain required. No production,
buckling-factor, release or default-activation authority is asserted.
