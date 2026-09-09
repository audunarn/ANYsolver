# Native spectra checked; continuum reference refinement failed

Frozen implementation 10f79f3c5a96c4e45dd1dc44cd83ea253deba9e4,
tree 66e28943f24ab3877194425e1d256104fb95780d. Six research-only paths;
no native beam/shell mechanics, section, state, recovery, mass-policy, defaults,
public API or version changes. Twenty targeted tests passed in4.41seconds.
Diff check passed. Full comparison gate did NOT pass; no aggregate exists.

## Successful native worker results

All eight native workers completed: both signed +/-0.0065 endpoints,80/100digits,
two replicas each. Original binary64 L,R,H,B factors were assembled in Decimal,
then the141positive algebraic rotational traces were eliminated without inertia
or mode deletion. All285physical coordinates retained. Each returned full438
coordinate mode was checked against the original matrix/factor work, not merely
the rounded condensed pencil. Trace residual and Schur symmetry met1e-60.

All eight workers returned the same six eigenvalues, in order:

    -0.2816297982974668
     0.02185533753263586
     0.08230288168585821
     2.401485482213977
    12.848431430813601
    15.697089644463004

The first is an unstable current-rest mode, not a real oscillation frequency.
Worst original full-vector normalized residual6.759172800047098e-12 passed1e-11;
mass orthogonality and original bilinear Ritz checks also passed1e-11. No
unrelated maximum stiffness was used to normalize these modal residuals.
80/100 signed-rate differences were exactly zero. Same-sign/profile full outputs
were byte-identical. Opposite-sign full vectors are not claimed byte-identical.

These are accurate spectra of the captured native discrete pencils only. They
do not establish comparison to a converged independent continuum spectrum.

## Genuine reference-refinement rejection

The positive continuum reference and its replica both completed all four profile
calculations, but failed the frozen refinement gate. Their complete diagnostic
records were byte-identical. The24-to32global-sine signed-rate discrepancy was
0.15310299158900031 (15.3103%), above0.5%. The64-to128Gauss discrepancy was only
2.8391289319529278e-11, below1e-6. This isolates inadequate trial-space convergence
in this reference calculation rather than a quadrature failure.

For example, the second eigenvalue estimates were0.0836458263425055 (16sines),
0.050360137052897 (24), and0.0378748311705501 (32). The six-mode reference is
not sufficiently resolved to classify native errors or evaluate the planned
physical MAC gate. Do not compare these values against native spectra as a
qualified engineering discrepancy. No tolerance was relaxed, no mode removed,
and the successful first negative-work diagnostic remains historical evidence.

The global sine displacement and rotation spaces need not efficiently represent
the near-compatible axial/shear kinematics of these weak modes. This is a
mechanistic hypothesis, not yet a separately verified causal proof. The next
reference discretization must be validated independently rather than fitted to
native values or accepted by agreement alone.

## Bounded process disposition

Twelve processes planned; ten launched. Eight native workers succeeded; two
positive-reference workers exited1 with
`ValueError: reference refinement/quadrature not resolved`. Negative-reference
jobs were cancelled from the executor queue before process launch; no output is
fabricated for them. All launched process trees are terminal and empty. Coordinator
session85791 ended exit1 after propagating the genuine reference failure.

Native runtimes6.940-7.446seconds; reference runtimes9.254-9.355seconds. Total
launched wave30.700seconds. Peak459571200bytes. One numerical thread each,
max3concurrent;120sinner,600s/24GiB child and1800s wave bounds retained.
No timeout, memory failure, automatic retry, owner capture or equilibrium rerun.

The saved-data audit separately verified exact launched inventory, terminal
receipts, native precision/replica equality, native numerical metrics, genuine
reference rejection and absence of aggregate/accepted reference records. It did
not redo the mechanics or claim independent author review.

## Immutable archive

C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-physical-spectrum-10f79f3-20260909.
71manifest-bound files plus manifest; exact extent, bytes and SHA-256 verified in
exclusive staging and external copies; original TEMP retained.
Manifest9611bytes SHA-256
57b4cc84c8b26961ccda851d09d454dab706984ce41c0339a3f05318498aadad.
Saved audit2929bytes SHA-256
464dc8eeac48e326230edb52c0fa488111635e3a210fe4d1c6bf3f9c06a27b9c.

Positive80 native65595bytes SHA-256
77832187b1fc3ad35b019f92d0467b8c63eebc05773b24ed047009298adfe71e.
Positive100 native68459bytes SHA-256
9b4fcbc0f3f0243ad0af8e73eb3ed3d9cb04d672c021bf811ab886e53c217132.
Negative80 native65494bytes SHA-256
e9d19c1a147f19e8341b57e3c53851f8c3a3aa956bbba9c8eb2cbd91d0f6d33c.
Negative100 native68358bytes SHA-256
e47a7031226e527313433bee3761c7f626b85e09954612aef2ca7c4580cbb01f.
Failed positive reference diagnostic3379806bytes SHA-256
5dc8c14c71871a133111bd4cb79e28689b514081df67f4f6d59328af63830110.

## Next safe successor

Preserve this failed gate. Reuse its checked native spectra; do not rerun them.
Develop a separate continuum reference using continuous piecewise-polynomial
six-component fields on the four already frozen continuum segments, with exact
endpoint clamps and shared interface traces. A candidate construction is linear
interface hats plus local(1-t^2)Legendre bubbles, with derivative-consistency and
completeness tests before selecting/freezing refinement profiles. Keep the same
physical inertia, energy density, six modes, sign handling, accuracy, refinement,
quadrature, engineering-error and MAC gates. Do not modify the production beam
interpolation, mechanics, coefficients or admitted geometries to fit reference data.

The overall goal remains open: full reference comparison, broader geometry/
slenderness, nonlinear/state/material/solver parity, independent review, installed
explicit selection and objective eccentric/curved beam-shell connections.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
