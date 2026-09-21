# F09 physical B2 local operator: preparatory implementation

21 September 2026. Private source commit `a8b5bb4` introduced
`B2_PHYSICAL_FLEXIBILITY_LINEAR_V1` as a straight-reference local
force-flexibility operator. It evaluates scalar isotropic and symmetric
positive-definite generalized 6x6 section stiffness, exact polynomial
flexibility, local force/tangent/energy and station resultants/strains.
Rational intermediate arithmetic avoids erasing the very weak shear
mode through subtraction of rounded entries. It has no public selector,
global graph assembly, mass or geometric stiffness.

Thirteen focused private-module tests passed in 0.50 s in the local
Python 3.13 environment, checking independent weak-shear energy,
both bending planes, basic/rigid modes, generalized section coupling,
station work, representability errors and owned-definition mutation.
The test import explicitly bypassed the broad `anysolver` package root;
this is not an installed-package or registered F09 result.

Independent read-only code/mechanics review found the local scalar and
generalized equations sound within this preparatory scope. Its initial
P1 stale-cache ownership finding was closed by sealing reassignment and
deletion of the operator definition and storing the internal matrices
as immutable tuples; the focused tests then passed 13/13. The reviewer
left three P2 matters open: the provisional normalized `1e-12` SPD
pivot cutoff is not a registered physical/conditioning admission;
the rounded dense tangent has not proved retention of extreme weak
shear modes in a graph solve; and the scalar/generalized descriptor
does not yet carry the complete physical section provenance, mass or
geometric-stiffness metadata.

**Status: implemented local preparatory oracle, not F09 qualified.**
Before any profile dispatch, define and freeze the physical descriptor
and numerical range; exercise an assembled factor/action path for weak
modes, independent physical/unit/station/directional oracles and the
full registered F09 matrix. Legacy public B2 behavior is unchanged.
