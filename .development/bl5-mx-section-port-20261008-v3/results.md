# Mx beam-only section-port contrast — development result

The saved C3D20 body and 10 N m torque were held fixed. A six-mode area-L2
section projection was integrated on each end face; its rigid-motion identity
error was `8.9e-16`. The saved end-traction vector equals its work-conjugate
section-dual load to `6.8e-16` relative L2 difference. Thus end-load
distribution is not the Mx discrepancy on this specimen.

| Root restraint | Resolved applied work | Native/resolved work ratio |
|---|---:|---:|
| All root-face nodes fixed | `0.001449918650 J` | `1.13594` |
| Six area-L2 section poses fixed; warping free | `0.001474597704 J` | `1.11692` |

The root change increases resolved compliance by `1.70%`, leaving a substantial
body discrepancy. The native `0.001647014034 J` beam-only work agrees to
floating-point precision with the prismatic Saint-Venant prediction
`M²L/(GJ)` for the declared `0.04 × 0.06 m` rectangle. The port-root C3D20
model is `10.47%` stiffer than that prediction. This is one coarse 3D mesh;
it does not prove why its result is stiff or establish a converged continuum
reference. The next discriminating check is systematic C3D20 torsion refinement
under the *same* section-port root and dual torque. Convergence toward the
Saint-Venant response would classify the old resolved beam body as a coarse
reference; failure to converge would direct inspection of the port, body and
constitutive idealization. Neither outcome alone qualifies BL5 or F03.

[Raw result](contrast.json) and [bounded receipt](receipt.json) retain exact
source/saved-input hashes and observed CPU0, one numerical thread, JIT disabled,
164.8 MB sampled peak process-tree RSS, and 7.21 s cumulative process time of
the 120 s allowance. V1 and V2 attempts remain preserved. No CalculiX or
coupled equilibrium solve ran.
