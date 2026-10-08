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
