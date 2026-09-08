# Retained force research convergence correction

The c1f51b5c5ed8a4f6bf3c4b7a482b5c1e3e8b1763 smoke had three passes
and one genuine failure. Both full-operator comparisons passed, as did the
straight solution comparison. The curved solution's resultant difference was
1.2703647241156206e-11 against the unchanged1e-11 field gate. The prototype
stopped after two Newton corrections with residuals around6e-12; residual-only
stopping does not ensure a sufficiently small remaining mixed-coordinate step.
No higher-ratio lane was launched.

Preservation archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-force-initial-c1f51b5-20260908`.
It retains original logs, failing JUnit, both solution outputs, full-operator
comparisons and frozen research programs. This failure is not reclassified.

The numerical successor adds an a-posteriori Newton-correction stopping check
in addition to both existing residual checks. Compute the complete constrained
mixed Newton step from the current Jacobian. Require the maximum of translation
norm divided by reference length, nodal angular norm, cell angular norm, and
resultant correction norm divided by max(1,current resultant norm) to be at
most1e-11. This is a research convergence control, not an error-bound theorem.
Apply further Newton steps if it fails; all existing iteration and process
bounds remain. Do not loosen the field, equilibrium or compatibility gates.

Only the research driver and this disclosure change. Frozen native mechanics,
source equations, material, geometry, loads, tests and historical evidence
are untouched. A new frozen smoke must pass before the high-contrast tests.
No automatic retry of the previous frozen invocation is authorized or performed.
Production qualification remains false and independent review PENDING.
