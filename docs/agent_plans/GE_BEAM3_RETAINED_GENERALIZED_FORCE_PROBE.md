# Retained generalized distributed-force research successor

Base `dc53d4c77120ad9b8c0bb5736c58a234b098e06e` preserves two genuine
high-contrast failures of the native nested force path. This successor adds
only a research driver and tests; it changes no production operator or state.

Retain the same18 nodal DOFs, six cell rotations and18 generalized resultants
through the Newton solve. Assemble the existing generalized potential,
conservative reference-line work and spatial distributed couples, including
their existing unsymmetric spatial Jacobian. Fix all six root coordinates.
Keep the constitutive origin virgin and reject any plastic-history update in
this first elastic-only research probe; do not claim a native state commit.

Solve parameters0.5 and1, maximum24 Newton iterations each and nine line-search
fractions, with equilibrium and compatibility individually below1e-11.
Use compensated positions and multiplicative nodal/cell rotation updates.
There is no internal static condensation, extra physical stiffness, tolerance
relaxation, material fitting or change to the source equations. Retain failed
trial and accepted state separately. The120-second cooperative bound supplements
the external600-second/24GiB/one-thread child and1,800-second wave limits.

Before high contrast, compare full residual/Jacobian at both saved moderate
native states and solve both moderate cases. Require physical positions,
nodal and cell frames and generalized resultants to agree within1e-11. Then
test unchanged ratios10,000 and1,000,000 on straight/curved geometry, followed
by properly rotated curved specimens. Bind the previous5,012-byte archive
manifest, preserve failures and launch at most three independent processes.
No automatic retry. A failed smoke stops the larger wave.

This prototype reuses native source operators; it is not an independent
mechanics oracle, packaged controller or nonlinear/material qualification.
If successful, next steps are stronger physical work/material reference checks,
general load/history/state integration and objective connection qualification.
Existing B2/B3/Q4/S3, defaults and historical evidence remain unchanged.
Independent review PENDING; NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
