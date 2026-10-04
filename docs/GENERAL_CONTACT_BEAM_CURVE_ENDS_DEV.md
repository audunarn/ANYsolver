# Classical quadratic-beam physical ends — 4 October 2026

**Implemented and installed-tested development. Not independently accepted,
released, or admitted for ordinary application analysis.** Source is bound by
the local checkpoint commit and the [evidence](d1_review_support/contact_curve_endcaps_20261004/summary.json).

## Model and use

`CLASSICAL_B2_B3_ROUND_TUBE_QUADRATIC_PHYSICAL_ENDS_STATIC_DEV_V1` uses one classical
B2/B3 cell per body, including B3–B3 and mixed B2–B3. Reference B3 cells remain
straight under the existing scalar isotropic-elastic von Karman contract. Their
current Q2 curve, actual endpoint tangent and all nodal position maps are retained;
no chord replacement, artificial mid-node cap or section-deformation claim.

Use the public definitions/ordinary static route in
[example](../examples/general_contact_beam_curve_ends.py). Both surfaces declare
`beam_end_caps='hemisphere'`, explicit radii, line stiffness in N/m², endpoint
stiffness in N/m and dimensional gap tolerance. The existing explicit line
integration and full-curve gap accuracy/cell/depth settings remain required.
Unresolved initial penetration, unsupported geometry and exhausted budgets reject.
The example's relatively loose gap budget is for code verification, not the
programme's engineering penetration criterion or an application recommendation.

## Discrete work and geometry

The existing symmetric half-weighted two-direction line potential is reused.
Each owned end/interior contact adds `E=.5*ke*g²`; a reciprocal genuine cap/cap pair
adds one spring. True ends use all classical material-node incidence, including
unselected junctions and middle-node attachments. Nonphysical selected cuts reject.
Outward ownership uses the actual Q2 endpoint tangent, rather than its chord.
This is a declared point end law, not continuous hemisphere surface integration.

The existing `b3_distance_jet` differentiates the unique closest station on the
actual target curve. Its reduced distance Hessian is
`Hqq-Hqt*Hqt.T/Htt`; `Htt` includes target curvature. Point residual and tangent are
`ke*g*grad(g)` and `ke*(grad(g)*grad(g).T+g*H(g))`. Both-body and mixed B2 embedding
blocks are assembled. Reference line measure is unchanged. Point and line storage
and physical body wrenches about the global origin are reported separately.

Endpoint interval admission uses exact rational Q2 Bernstein controls. For
`F(t)=(r(t)-p).r_t(t)`, globally positive `F_t` and strict endpoint signs prove a
unique fixed closest branch. Exact sign brackets enclose interior roots and actual
endpoint ownership. Common temporal intervals bind all caps and reciprocal partners.
Nonconvex projection profiles, active branch/ownership ties and unresolved closed
switches reject; samples never establish path admission. Closed feature transitions
and broader multiple-minimum handling remain required programme work.

Full pair separation uses exact relative degree-(2,2) tensor controls, squared
degree-(4,4) controls and existing tensor arithmetic/subdivision. Coordinate boxes
and squared Bernstein minima supply lower bounds; real corners/centre supply upper
bounds. Best-first refinement/pruning preserves the complete represented domain.
Bounds round outwards and must meet the explicit dimensional enclosure accuracy.
Exact Bezier relative-velocity bounds and endpoint-gap Lipschitz intervals enclose
the actual affine static trial path. Curve regularity is checked separately.
Cell/depth/report-precision exhaustion is explicit non-success.

Literal clamp activation uses exact squared gap and cancellation-resistant scalar
conversion: a rounded `norm-R==0` cannot delete its finite active tangent. Conversion
underflow rejects. Interior activation within unresolved floating roundoff rejects.
Restart binds these geometry identities, true ends, laws and numerical controls.
No physical increment is committed by candidate evaluation.

## Executed evidence and remaining scope

Installed **21 checks pass in 27.588 s**, peak process-tree **335622144 B**,
JIT disabled and effective numerical pools at one thread. **220 loaded modules and
500 package files** byte-match source. Solver wheel SHA256
`83524d9c9d10ace7c0be09cbd49da51f034d7ae1d9d5e9f1249d0712acfb5876`.

Checks include independent scalar curved point energy, B3–B3/mixed both-body
directional tangents (`1e-5`), full work/wrench balance, rigid transformation and
connectivity/body exchange, actual middle-node and through-crossing paths,
independent P2-bar response (**8.409e-16 relative**, target `1e-6`), force/displacement
controls, active/open JSON split restart, changed-law/settings/topology rejection,
actual exception/cancellation rollback, public example, capability rejection and
inherited B2/B3/no-contact routes. Full gap is separately checked at `1e-5` and
`1e-7 m` under the same 10000-cell/depth25 limits.

Nine measured runs/59 raw records preserve exploratory and actual AABB-depth
failures, the unsuccessful separating-support experiment and a confounded
through-crossing fixture. The legacy uncapped curve kernel is unchanged. Review's
rounded activation defect and subsequent underflow concern were corrected;
same-family source scrutiny is supporting evidence, not independent engineering
acceptance. [Raw evidence and review](d1_review_support/contact_curve_endcaps_20261004).

Multi-cell quadratic beams, generalized closed transitions, mesh/enforcement and
engineering acceptance, finite rotations/materials, beam–shell boundary work,
native/friction/dynamics, application admission and the full C0–C9 programme remain
incomplete. No complete-route speedup or programme completion forecast is claimed.
