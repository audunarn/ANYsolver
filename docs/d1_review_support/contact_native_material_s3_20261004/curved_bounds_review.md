# Supporting curved material search-bound scrutiny — 4 October

Read reviewer /root/curved_initial_review, same model family; no edits or numerical
runs. Supporting scrutiny, not independent engineering acceptance.

Reviewer checked Q2 Bernstein controls, restricted affine swept chords, whole
rotated lift/radial circumsphere, current rotation/ref identity/coordinate guards.
The author replaced the initial nominal-rotation gain before closure: the revised
gain includes admitted nodal Gram error amplified through the shortest-transport
denominator and finite arithmetic. Reviewer found no remaining material enclosure
counterexample after that correction.

Two details required closure: update the obsolete nominal-proper-rotation comment;
preserve xi+1 as an exact rational shift. Both are corrected. Parameter restriction
now uses a quadratic blossom on exact rational endpoints; floating station
evaluation still has explicit roundoff padding. Added sub-ULP shift control.

Reviewer requested near0.9*pi turn/nonorthogonal-node input. Initial +/-2e-12
distortions failed original native-reference admission before bounds. Preserve raw
failure; no tolerance change. The admissible +/-1e-13 fixture checks interpolated
frame norms at2001stations, and explicit controls require the original larger
distortion rejection. This sampling checks the analytical norm envelope; sampling
is not itself the bound proof.

Whole current/swept boxes are search enclosures. They certify neither surface
orientation, physical gap, collision time nor coupled mechanics. Curved force
integration and owner admission remain open. See curved_bounds_summary.json.
