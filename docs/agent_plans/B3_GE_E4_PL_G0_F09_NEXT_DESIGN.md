# F09 next design: physical descriptor and assembled weak-mode proof

21 September 2026. **Design for review, not an execution registration or
F09 acceptance.** The private local operator computes straight-reference
force-flexibility response and passes focused unit oracles, but the
independent review found unqualified section provenance, conditioning
admission and weak-mode graph transfer. These are the next prerequisite
decisions before public B2 profile dispatch.

## Definition boundary

Use one new versioned operator/profile identity and an owned, immutable
model definition with explicit node/source IDs, reference positions,
local physical axis, section origin, unit convention and section identity.
The scalar stiffness variant owns `E, nu, A, Iy, Iz, J, ky, kz` and derives
its six sectional moduli without a shear-denominator floor. The
generalized variant owns the full symmetric positive-definite 6x6
stiffness and its section axes; it cannot invent the scalar inputs.
Caller mutation and serialization/reopen must preserve the exact
mechanical meaning. Hashes are compilation provenance, not a substitute
for typed admission or physical consistency.

Mass information is a distinct optional record: density and actual
sectional translational/rotary/centroid inertia, or a validated
six-channel mass-per-length matrix in the declared frame. Geometric
prestress metadata is another distinct optional record: physical
centroid, section/shear-center axes, and the geometric polar/Wagner
quantities needed by the admitted buckling law. Static stiffness does
not infer either record. Modes and buckling fail in preflight with
specific absent/incompatible-data errors. Historical public B2
defaults, equations, selectors and checkpoints remain unchanged.

The B2 line attachment needs an independently derived physical
translation/rotation trace and virtual-work derivative through the
actual local kinematics. Station resultants `H(x)q` and strains
`S^-1 H(x)q` alone are not that displacement trace. Freeze orientation,
axis reversal, offsets and unit transformations before F10 and F11.

## Decisive numerical evidence

Register a physical range and exact/high-precision reference for a
constrained one- and two-member graph before any F09 qualification
execution. Compare the local force, energy, tangent, station work,
assembled displacement, reactions and scaled residual against an
independently calculated physical-flexibility oracle. Use a
production-like sparse route and measure the actual factorization.
Include both a moderate well-conditioned case and the extreme
`A=2^-80, EI=1` shear-soft case: the weak/strong modal ratio is about
`1e-25`, so correct exact local energy does not demonstrate that a
rounded binary64 global tangent retains the weak mode. Preserve
stable factors/actions through assembly or explicitly reject the
unrepresentable solve with diagnostics; never floor shear or infer a
global rank pass from the six local modal values.

The current exact LDL normalized-pivot `1e-12` limit is provisional.
Before admission, compare SPD data on both sides of it to a high-
precision reference and distinguish invalid input, poor physical
conditioning, output conversion and global solve failure. Freeze
physical scales, nonzero denominators, unit transforms and numerical
tolerances in a single-use registration. No failure may be relabelled
as an ordinary converged response.

An unregistered one/two-member root-clamped tip-shear exploration
subsequently matched its analytic cantilever formula even at
`A=2^-80`; see `B3_GE_E4_PL_G0_F09_GRAPH_EXPLORATION.md`. The formal
graph gate must test harder mixed/rotated/attached responses and a
high-precision oracle rather than presuming all binary64 sparse
factorizations fail at that ratio.

The private owned member/metadata definition is now recorded in
`B3_GE_E4_PL_G0_F09_DEFINITION_PREP_V1.md`. This closes only preparatory
identity, frame, input-ownership and algebraic PSD questions. It does not
settle whether an arbitrary 6×6 PSD matrix is physically realizable as a
rigid-section mass, or how optional mass and geometric records transform
under reversed connectivity. Those semantics must be frozen before modes,
buckling or advertised physical B2 profile admission.

Minimum matrix: well-conditioned scalar S0, old-floor-active and
old-threshold S1, extreme S2, unequal bending/shear axes, scalar
axis reversal and rotation; coupled generalized SPD, near-bound SPD
and indefinite rejection; rigid/free-free and supported patches,
physical station work and at least three trace stations; one/two
member graph, unit changes, supported/absent mass and geometric
preflight. Bind exact source/dependency identities, runner, resource
limits, raw output and independent review. F09 local and graph
feasibility does not itself qualify F12 buckling, B14 spectra or G1.
