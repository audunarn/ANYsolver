# Supporting capped-cylinder source scrutiny

Read-only worker `beam_surface_contract`, 3 October 2026. Same model family;
no independent engineering acceptance. The worker inspected equations/source,
without executing tests or changing files. The integrating lead checked the
findings against source and retained the corrective tests and failed inputs.

The exterior side/cap/rim gradients and Hessians follow closest-point distance.
The reviewer identified a real interior moving-seam tangent defect in the initial
unrestricted candidate: for axial direction x, R=.01, h=.1, beam radius=.01,
segment x=.092–.098 at radial distance .005 crosses the medial seam at x=.095.
Integrating branch Hessians gives radial stiffness .003*k instead of -.012*k;
the missing term comes from motion of the seam.

The revised profile rejects gap tolerance at/above the tube radius and requires
a conservative whole-centreline exterior proof before any work mapping. The
counterexample is now an explicit rejection test. Exterior cap/rim and side/rim
gradients are continuous, so the identified interface term does not apply there.
This is a genuine bounded profile restriction, not a repaired interior model.

Exact branch-checked Bernstein inactivity and activation-root endpoint signs
retain radial/axial correlation. The reviewer found no false certificate in the
examined changes. However floating partition candidates plus adaptive Gauss
agreement do not prove a general mixed-panel integration-error bound or the
absence of every small second pocket. The source comment and guide explicitly
retain this limitation. The integrating lead added separate quadratic pockets,
rim/grazing and moving-tool checks; their passes do not resolve arbitrary-curve
integration acceptance. Broader refinement and independent assessment remain.
