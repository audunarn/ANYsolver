# Independent F09 decision and certificate review

Reviewer `/root/anyfem_consumer`; read-only, no implementation, jobs or edits.
Parent implemented the test and certificate. This is a bounded Level-A design
review, not F09/G0B scientific acceptance.

The exact-Fraction LDL's `pivot/diagonal < 1e-12` is a provisional operational
guard, not a floating factorization estimate or defensible physical-condition
boundary. Public fixed-wrench agreement strengthens graph evidence but three
discrete rectangles cannot establish a continuous or unit-aware admission range.

Smallest replacement: certify all basic energies of the actual emitted rounded
tangent, and separately its rigid/cross work. Basic-only right-inverse tests
cannot detect spurious stiffness confined to the rigid kernel. Section-input
SPD, local-output representation and assembled sparse solve failure stay separate.

Source `b2_f09_output_certificate_dev.py` is mathematically sound as a bounded
local output guard/design discriminator. Exact symmetric Schur PSD handles a
zero pivot by requiring its remaining column zero. BR=I and BZ=0; K is the
actual symmetric binary64 tangent, interpreted as binary rationals. Both
Loewner bounds at eta=1e-8 cover all six basic energy directions, including
coupled weak directions. Centroid Z scales translations by L and rotations
by one; F=max(section force diagonals, section moment diagonals/L²), M=FL,
E=FL. Rigid wrench row-one norms and rigid/cross absolute entry sums bound
the explicitly declared amplitude cube. Metre/mm controls are consistent.

All seven physical cases pass (strongest rigid wrench 3.0279e-17; cross
7.6782e-17). Injected basic/rigid/cross defects fail; rigid/cross controls evade
the basic-only test. Historical nonphysical shear-soft stress also passes;
this is not assembled graph stability or physical-range admission.

Caveats: A derives from `_basic_action`, so the certificate checks rounding
preservation of the implemented law, not its independent constitutive correctness.
Keep force-method/energy/station oracles. Separate rigid and cross limits are
not one combined <=1e-8 total-energy bound (mixed term factor two), nor an
all-amplitude relative bound near rigid modes. Retain stronger registered local
1e-12 predicates. Before removing the pivot screen, enforce a typed guard on
emitted tangents and retain distinct graph/equilibrium checks.

No correction required to this bounded discriminator. It is suitable for the
next bounded product implementation, but F09 remains open and the pivot guard
remains until that implementation and its impact checks are established.
