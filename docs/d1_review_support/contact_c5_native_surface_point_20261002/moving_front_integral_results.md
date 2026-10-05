# Moving-front integration connection — non-success

Explicit integrate_open_event_friction_fronts helper reuses existing adaptive Gauss4/8,
full point history and residual/tangent/work packing. Requires all captured endpoints
strictly open and explicit event-sequence profile. Whole-angle stationary branch cover
precedes per-angle endpoint/stationary cuts; axial uncertainty strips are represented,
not omitted. Per-angle enclosure calls consume the existing shared support budget.
No analysis-owner/restart admission or historical-path change.

First connected tilted-source pulse-appearance case FAILS: point event isolation reaches
temporal resolution inside the stationary-front uncertainty strip.0.56s test call,
pytest6.67s. Do not treat as pass or increase caps. Raw failure/runtime retained.

Next derive uniform conservative work enclosure for the whole uncertainty strip. This
is numerical integration error, not removal of a physical contact. Strictly open endpoint
force/tangent are zero; dissipation/release/cumulative work must have explicit certified
bounds within unchanged integration budget or evaluation remains non-success. One-stationary
branch and fixed-sign B bound penetration near its extremal H; discrete Coulomb work must
account for all retained history windows. Independent mathematical scrutiny requested.
Candidate formulas and essential assumptions are in reviewer task context; final derivation
must be saved beside source before production use. Closed-ending/multiple-stationary cases
remain outside this first connected work slice, not outside programme requirements.

Review derivation: uniform density bounds times FULL reference strip measure can bound
integration error for released-entry/fixed-partner discrete replay. Require contact-producing
global H extremum, full time/angle coverage, fixed-sign B and strictly open endpoints.
Penetration covers every strip coordinate/front enclosure plus arithmetic error.
Slip path variation must include ||r_dot||+||F_dot|| ||r||, where F is FULL target frame
and r includes normal separation. With C=mu*P and n substeps,
D<=C*(total_slip_variation+2*n*C/kt); release<=C^2/(2kt) per certified window.
Cumulative work sums ALL preceding segments/incoming cumulative value; last-segment
D/release are separate. Add bounds to global absolute work-error totals. Never call
strip never-contacted or use integral bounds as recovered point histories. This reviews
a possible discrete error enclosure, not continuum accuracy or numerical acceptance.
