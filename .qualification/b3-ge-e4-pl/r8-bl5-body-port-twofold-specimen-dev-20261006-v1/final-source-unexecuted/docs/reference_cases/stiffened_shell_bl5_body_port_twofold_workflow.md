# Saved-density two-part body-work development workflow

This separate candidate uses the original saved density, unchanged shell clamps,
full mixed beam operator and six physical rigid modes. It imports the immutable
historical native wheel, not the current package. Both coordinate parts survive
original-equation residuals, work, support/common-origin wrenches and point/P0
traces. The original physical equilibrium gate excludes gauge forces; joint KKT
closure cannot replace it. A failed shell stops before any beam RHS.

Material superposition is restricted to the actual virgin strictly ELASTIC
quadratic section law. Independent responses at pHi and pLo share the same virgin
origin and retain all returned gradient halves. Reference-linear stationarity
uses JqHi+JqLo. Stored energy is EHi+ELo+pHi dot gradPsi(pLo), including both
returned gradient halves. Zero reference energy/gradient/potential, unchanged
histories, zero dissipation and individual/combined elastic guards are mandatory.
Combined exact fibre stress must lie strictly inside its virgin yield boundary;
YIELD_BOUNDARY/HARDENING_KNOT are refused. No plastic superposition is admitted.

One conditional development job may evaluate the unchanged shell RHS with three
corrections and, only after all shell gates pass, the unchanged beam RHS. All
failed calculated outputs remain. Passing only establishes effective body work
at this saved density; common-action subset and broken-cell trace limitations
remain. It establishes no coupled native accuracy, refinement, qualification or
physical connection acceptance. Numerical execution is pending source review.

## Executed development outcome: admission failure, body gates unassessed

The five consumer checks passed in0.32s under the exact historical installed
operator/CI graph. Unchanged saved-density preparation and full native loads
matched the original V2 preflight exactly. The attempted shell caller then failed
at the core's fixed-index type admission: owner supports are numpy.int64 while
the candidate requires Python int. This occurred before factorization or any
linear solve. No shell response, beam RHS, material recovery or compliance result
was calculated. The runner's BODY_RHS_STARTED status means invocation intent;
the saved traceback establishes actual admission-only failure.

A bounded caller repair converts each unchanged support index to Python int and
extends the mocked complete-caller regression. The repaired source passed syntax
checks only and has not been numerically executed. Automatic approval review
rejected a combined repair/second-launch command under the no-rerun restriction;
no second job ran. Execution requires a separate explicit decision. The original
failed evidence and executed source are preserved. This is partial implementation,
not a successful body-work discriminator or scientific acceptance.
