# D1 fixed-structure pressure-only enrichment — development result

The independent reviewer proposed one bounded discriminator on the same 32×8
scalar structural mesh, near-rim geometry and saved FV256×320 reference as the
previous 16×8 versus 32×8 pressure comparison. The question was whether either
x or y pressure-only refinement changes common 8×9 physical bin forces and
the rim force by at most 0.2%, a prospective development sensitivity share of
the retained 2% spatial-response allowance. This is not a new acceptance gate.

The parameterized [probe](../../scripts/general_contact_d1_fixed_structure_pressure_probe.py)
used the original 32×8 pressure space, 64×8 pressure in x, and 32×16 pressure
in y with an explicit knot at the physical y=0.9 support rim. It retained the
same exact cross-mass integration, scalar stiffness, loads, support, bins and
KKT checks. The unchanged 32×8 reference reproduces the prior 0.4811% FV bin
L2 error and has 96 active pressure modes. The [bounded result](d1_pressure_enrichment_e_a8ade309_20260928.json)
ran under the [180-second, 1-GB cap](d1_pressure_enrichment_resource_e_a8ade309_20260928.json).

Neither enriched scalar pressure solve settled within the independent oracle's
500 projected active-set iterations. The y-enriched space has one pressure
mode with exactly zero physical support beyond the rim; the probe now removes
only exactly unsupported modes before solving, preserving every positive
support. Both enrichments still fail to settle. The initial x failure and the
y unsupported-mode failure are retained in the [x failure](d1_pressure_enrichment_b_a8ade309_20260928.txt)
and [y failure](d1_pressure_enrichment_d_a8ade309_20260928.txt) logs.

**Decision:** This run does not measure the proposed enrichment sensitivity or
establish pressure-space instability. The scalar oracle is inadequate for
these richer spaces as presently solved. Do not infer a D1 mechanics failure or
increase the iteration budget automatically. A subsequent pressure-resolution
claim needs a robust, independently checked complementarity solve or a
different admissible fixed-structure pressure discriminator, with work-rank and
KKT certificates. The production fine Q1 basis is unchanged.
