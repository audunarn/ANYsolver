# Supporting Read scrutiny — capped-cylinder beam ends

Reviewer `/root/beam_surface_contract` inspected the dirty reconciled solver
candidate without edits, tests or nested delegation. Same model family;
supporting scrutiny, not independent engineering acceptance.

The review confirmed endpoint potential/residual/Hessian signs, exact
directional-derivative interval enclosure, open-or-fixed-ownership affine
subdivision, actual B3 end derivatives, all-material-node incidence and
endpoint/topology restart binding.

Concrete counterexample: at rho=R,z=h+d,0<d<r an owned atomic endpoint has inward
radial energy Hessian zero and outward k_end*(d-r)/d. At z=h,rho=R+d the analogous
axial limits differ. The submitted kernel accepted these physical feature seams
with one branch Hessian. The lead added exact/represented seam rejection and
independently derived one-sided checks for both transitions. Endpoint preflight
now runs before distributed integration; otherwise these fixtures reached its
existing finite budget. Both final seam checks pass; failures remain retained.

The lead separately diagnosed a swept preflight infinity sentinel leaking into
restart diagnostics. Only unevaluated zero-iteration contact preflight rejection
records a null residual and explicit not-evaluated reason. The open-restart tool
case and ordinary failed/accepted checkpoint checks pass installed. Computed
nonfinite results are not normalized into success.

The model remains additive line plus endpoint-point work, not a continuous
hemispherical surface integral. Active ownership changes reject; open changes
need a whole-path certificate. General mixed-panel integration, spatial and
enforcement refinement, engineering admission and full D3 remain open.
