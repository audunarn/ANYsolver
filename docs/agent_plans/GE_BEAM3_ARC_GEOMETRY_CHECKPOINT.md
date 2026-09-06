# GE-B3 native arc geometry checkpoint

Private development successor of `06d7e869e60d1884a330c6778dde89b2c8673cc0`.
The new `_ge_beam3_arc_geometry` module implements the objective frame-chord
hyperplane value and first derivative in the native spatial Exp increment chart.
It does not implement an arc solver, accepted-state transaction, adaptive
cutback, public route or qualification. Existing source/mechanics/defaults and
all earlier qualification and incident records remain unchanged.

## Equation and native-coordinate derivative

The preserved research hyperplane uses the rotation contribution
`0.5 <Q-Q0, hat(w) Q0>_F`, where `Q = Exp(hat(v)) Q0`. Orthogonality of `Q0`
reduces this exactly to `w dot (sinc(|v|) v)`. Thus no rounded dense-frame
subtraction is needed, and the origin frame cancels analytically. The native
increment-coordinate row is
`sinc(t) w + ((t cos(t)-sin(t))/t^3) (w dot v) v`.

This row differs from both the raw spatial derivative and the derivative of an
accumulated rotation-vector dot product. The latter is not the finite-rotation
frame-chord constraint. Small-angle series with explicit omitted-term bounds
avoid cancellation; they do not change a mechanical coefficient or tolerance.
The native `0.9*pi` increment guard remains. Arbitrary common rigid rotations
rotate `v` and `w` together and preserve the scalar constraint.

The full hyperplane adds weighted translation increments and the load-parameter
increment. Translation and rotation metric triplets are isotropic so a common
rigid-frame change cannot silently alter a diagonal metric. Fixed coordinates
have zero increments/directions; their isotropic weights may remain positive.
Anisotropic diagonal metrics, negative weights, nonfinite data, an all-zero
predictor, implicit scalar types and unsupported increments fail closed.

Callers must supply actual native step increments. This helper never reconstructs
small translations from rounded world positions or treats accumulated rotation
coordinates as authoritative physical frames. The future solver must still bind
these increments to the live native trial and accepted origin.

## Verification

Initial geometry tests: 25 passed in 1.41 seconds. Expanded regression:
**43 passed in 1.68 seconds**, comprising 28 geometry checks and three preserved
five-check static evidence inventories. Geometry checks independently reconstruct
the frame Frobenius expression, differentiate Exp using Jets, verify the spatial
to native-chart pullback, compare directional finite differences, and exercise
proper rigid-frame covariance and zero/fixed blocks. A `2^-54` rotation retains
its nonzero chord where subtraction of rounded dense frames loses information.

The preserved research hyperplane and native chart source identities are bound
in the canonical development record alongside the new module/test hashes. These
are independent formula constructions, not an independent human/agent review.
That review remains pending. No formal request, archived scientific cycle,
installed wheel, new full-beam mechanics run or engineering qualification was
performed for this geometry-only checkpoint.

## Next integration

Wire this verified row into the native bordered predictor/corrector with the
actual load-parameter derivative, shared rotational state, accepted-origin
histories, staged global capsules, orientation/metric restart binding and
bounded cancellation. Test small elastic/plastic and arch paths before adding
bounded adaptive cutback. The full standalone straight/curved beam and objective
beam-shell connection goal remains active; this helper does not complete it.
