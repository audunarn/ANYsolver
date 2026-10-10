# Supporting control-predictor source review

8 October 2026. Read-only OpenAI reviewer `/root/swept_certificate_review`,
reconciled by the lead. Cached Mistral unavailability remains in force.
This is supporting same-family source review, not independent engineering
acceptance. The reviewer inspected tests but ran no numerical checks.

## Reviewed source identities

| Source | SHA256 |
|---|---|
| `static_path.py` | `b243fd5e283c5849d110cb15b523633b39842d2c9826e28b0dfed8d490d2de7c` |
| `core.py` | `d88816cc276bb17844c0b235860b286631b47a7a5828331894b39b1d812e1648` |
| `automatic_domain.py` | `16a4fba2c1c0adbe76ccbed2eb5874e2467477d3ca393463d28f9d6ca96bfc0f` |
| `nonlinear_static.py` | `540e16b11df201cbd920fb57e1d4de593a5b957f4ce0bbed539e5d86285c1a8d` |

The row-normalised projection gives the minimum Euclidean reduced-coordinate
correction into the prescribed affine control set, retaining its nullspace
components. It does not generally preserve every individual physical free
coordinate; the target displacement in this fixture lies in that nullspace.
The helper checks finite data, control count, rank/conditioning and the resulting
control residual. It predicts a pose, not equilibrium or physical force.

The driver certifies the complete committed-to-seed path and requires an
admissible fraction of one before assigning the seed or evaluating a structural,
material or contact candidate there. Invalid seeds return explicit non-success.
Subsequent failed increments restore the prior coordinates and multipliers;
physical commit remains behind the existing complete acceptance checks.

The new selector is appended to the dataclass, preserving earlier positional
arguments. Default `none` is omitted from automatic compiler and path restart
identities. Opt-in selection is bound explicitly and checkpoint validation
precedes boundary-condition mutation. Unused force/displacement/arc/transient
selection is refused. Initial admission is limited to the frictionless refined
Q4/S3 projected-penalty fixed-map contact-path development profile; rigid tools,
native, friction and other pairings are not implicitly enabled.

The reviewer and lead found no remaining concrete defect in the connected
predictor, admission, compatibility and transaction changes. Actual installed
controls, lifecycle, reaction/work, restart and refusal results belong to the
separate outcome record. No runtime improvement or engineering acceptance is
inferred from this source review.

## V2 compatibility follow-through

Read-only supporting review inspected the shared settings serializer, automatic
compiler wrapper, actual multiple-beam cap/transient and rigid-mesh restart
contracts, public request routing and the focused compatibility fixture. No
concrete serialization or routing defect was found. The default predictor is
omitted only from the affected historical restart/automatic settings schemas.
Opt-in request identification requires an actual contact-path program; unused
dead-load selection remains refused.

Request identity still serializes the selector and binds the current package
source. Pre-selector request canonical bytes are **not** claimed preserved.
The reviewer ran no checks; installed evidence is recorded in the outcome.
