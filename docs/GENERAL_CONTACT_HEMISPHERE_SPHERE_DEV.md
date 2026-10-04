# Actual hemisphere support against a fixed sphere — development

`CLASSICAL_B2_B3_HEMISPHERE_SUPPORT_SPHERE_STATIC_DEV_V1` is implemented and
installed-tested. Independent engineering acceptance, application admission and
release remain open.

Run `examples/general_contact_hemisphere_sphere.py`. Use explicit
`beam_end_cap_work="hemisphere_support_dev"`, declared round radius/hemisphere
caps, separate line (N/m²) and endpoint (N/m) stiffnesses, integration controls and
gap tolerance below both radii. One explicit scalar-elastic concentric classical
B2/B3 selection contacts one fixed sphere through ordinary nonlinear static
force/displacement controls. Actual curved B3 fields and midnode endpoint-tangent
work are retained. Genuine ends come from all material-node incidence.

For q=c−O and actual outward unit tangent d, set a=q·d. The closest hemisphere
point belongs to the cap sphere when a≤0, giving g=|q|−R−Ro. For a>0 it belongs
to the physical cap rim, giving g=√(a²+(|q−a d|−R)²)−Ro. Both branches use the
same point spring ½ k_endpoint min(g,0)² and meet C1. The sphere Hessian is selected
at the seam; one-sided checks verify the other limit. A parallel nonunique rim is
strictly open in the admitted exterior domain; its zero penalty work is explicit.

Existing Jet2 differentiates every B2/B3 translation and obstacle centre. Sparse
beam blocks retain complete cap couples; fixed-sphere force and moment follow
that same work. Exact binary-input branch/activation decisions and conjugate gap
formulas retain signs near activation. The distributed radial line law and its
adaptive integration remain unchanged. Complete radius envelopes and exact curve
regularity certify affine static paths. This profile resolves the configured
spatial gap accuracy before subtracting the temporal speed bound. Bounds use the
exact sum of literal radii, preserving Fraction input in the bound owner; this
changes enclosure arithmetic only. Legacy float-radius/ownership behavior stays.

## Checks actually run

Fresh private wheel: **49 passed in 31.888 s**, **362,438,656 B** peak process-tree
memory, JIT off and effective pools/Numba one thread. 216 loaded modules and all
506 package files match candidate bytes. Independent hemisphere-angle minimization,
all-node/centre virtual work and 10⁻⁵ Hessian checks, both B2/B3 ends and branches,
rigid covariance, physical contact points/wrenches, one-sided seam and exact
activation signs pass. Actual active seam crossing passes the complete path bound;
the legacy owned-point route still rejects it. Hidden through-crossing rejects.

Independent guided bar response error **1.110×10⁻¹⁵** meets its 10⁻⁶ development
target; minimum gap −1.900×10⁻⁶ m meets the explicit 10⁻⁵ m budget. Force and
displacement, completed JSON restart, incompatible identity, actual exception and
cancellation replay, material-junction ownership, runnable B3 example and explicit
missing-cap/spring, moving-tool and aggregate-sphere rejection pass. Legacy sphere/
cylinder loading, separation/open restart and multiple fixed-plane support plus
lazy no-contact checks pass.

[Evidence](d1_review_support/contact_hemisphere_sphere_20261004/summary.json)
retains seven measured runs/66 raw records. Review found a reversed Jet2 seed
argument order before numerical runs, admission/composition risks and an exact
radius dependency; each was corrected. Source01/02 conservative seam rejections,
a radius-check fixture error and the verified source06 Fraction-cast failure are
retained. The first pre-radius-fix wheel is retained privately and was not installed.
Supporting same-family source review is not engineering acceptance.

Remaining: correct mixed/multiple sphere composition, prescribed motion, cylinder/
beam-pair/finite-face cap transitions, material-surface friction/spin, native work,
transients, mesh/enforcement qualification and full C0–C9 completion. No performance
savings, publication, default change or release claim is made.
