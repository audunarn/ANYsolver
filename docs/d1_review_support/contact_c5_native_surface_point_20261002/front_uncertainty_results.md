# Stationary-front uncertainty — source development

All enclosure evaluations now consume the finite shared local call budget. Endpoint N
signs must be strict after rounding padding; ambiguous endpoints fail explicitly. With a
strict N' enclosure, the mean-value theorem encloses root time by padded N(root)/min|N'|.
A quotient enclosure at the root plus |H'|=|N|/B^2 times time uncertainty bounds the axial
coordinate. Caller may require an explicit maximum_axial_uncertainty (dimensionless xi).

Initial independent A/B-in-time bound failed prospective1e-7 width:3.40e-5. Kept failure.
Correlated bound passes at3.28052e-10 width, using5slab evaluations. Saved stationary
front remains xi=.7244843413242318,t~.5.1changed integrated geometry check passes;
independent polynomial controls3pass: two stationary roots, uncertain endpoint rejection,
singular axial direction resource failure. No sampled production extrema, cap increase
or tolerance relaxation. Raw logs/resources/runtime/selection records retained.

This is fixed-angle development. Binary64 error padding needs extreme-scale independent
checks before promotion; source review of new uncertainty handling requested. Angular
coverage and moving integration cuts remain next. Endpoint roots currently reject rather
than silently claiming completeness. No saved aggregate or coupled rerun.

Final source review found non-nesting denominator enclosures: intersect point/bracket/parent
B ranges before quotient, verify nonempty and one sign. Fixed. Endpoint fronts now also
carry axial uncertainty and obey supplied budget.4affected checks pass, plus1adversarial
wide-point-denominator regression. Return now (fronts, count, stationary_records, endpoint_records).
These changes remain developmental and require extreme-scale geometry controls.
