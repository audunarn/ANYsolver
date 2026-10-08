# F03 exact saved-pose representation diagnostic

22 September 2026. This bounded diagnostic follows the independently
reviewed Section A of `B3_GE_E4_PL_G0_F03_PRIMAL_NEXT_DIAGNOSTIC_DRAFT.md`.
It identifies numerical representation errors in three existing classical
Ritz states. It does not solve a new physical problem or accept a reference.
G0B remains open and G1 remains barred.

## Inputs and frozen question

Use exactly the n12, n16 and n24 states from the consumed
`.qualification/b3-ge-e4-pl/f03-primal-ritz-v1` execution at source
`e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5`. Preserve its original
FAILED_EVIDENCE decision. Bind all original artifacts and mathematical
sources using the completed parent inventory. Also bind the complete
`.qualification/b3-ge-e4-pl/f03-primal-saved-audit-v1` inventory, source
`c8b2f78d3ace4e23ed8f636fd6b474ef250ccda6`, registration
`62dd4f7bdb2001471603c7b45fc2a3adc709a9bf06ab49e075def1407cc5389a`,
and adjudication
`27ffa25aa390f8d83a579430015d49eb86fb9df6ada654d492aec5a20e478935`.
That audit's integrity passed while n16/n24 failed the unchanged numerical
screen. Bind its independent postreview
`a9b61c230d417d5c1004725cc87ba1bab59882de88c52dcdee0a966cdd62dec8`
and32-file completed inventory
`5073230a813bf9acef534d756ac05fb7deb29d1f7cf7caae507db94afc99014d`.

Read the bounded original archives without changing their arrays. Retain
their complete schema, byte hashes and case identities. This diagnostic
uses saved q, pose coefficients and station matrices. No equilibrium,
stiffness assembly, material evaluation, load assembly, projection-node
reconstruction, fresh reaction recovery or Green-norm recomputation is
permitted. Source-bound construction/solve guards remain active.

The question is how much of the saved pose-derivative discrepancy comes
from floating polynomial evaluation, coefficient reconstruction and the
direct station action. Spatial approximation and physical reference
convergence are separate questions, outside this execution.

## Exact independent construction

Use Python Fraction arithmetic for the separable rectangular moments,
Legendre recurrence, translation of p_i(s+xi), contraction with q and
power-to-Legendre conversion in x_beam=2s-1. Do not call the original
pose/basis/quadrature implementation to build the oracle. Lift the saved
binary64 coefficients of q exactly, preserving component/i/j ordering.

Use only the represented-constant geometry stream: binary64 d_x=0.2,
d_y=0.23, a=0.05 and the original rounded
J=0.2**2+0.23**2+2*0.05**2/3, each lifted exactly to a rational. Preserve
J_geom=E[xi^2+eta^2] and gamma=J_geom/J. Do not replace J with an exact
geometry recomputation or impose gamma=1. No nominal-decimal stream is
included in this registration.

Store the exact coefficients both in tau=s-1/2 powers and in Legendre
polynomials of 2s-1. Independently evaluate both representations and their
first two derivatives at the nine rational stations s=k/8. They must
agree exactly. No higher Ritz degree, changed q or projected replacement
of a saved coefficient is permitted.

## Discrepancy and endpoint identities

Preserve p_F,k and d_F,k from the original NumPy differentiation/evaluation
and station-matrix action, using their original arithmetic order. Let p_S
be the exact polynomial of the saved coefficient bits and p_O the exact
oracle polynomial. With brackets denoting exact binary64 lifting, store
all three signed terms and require exact rational closure:

    [p_F,k]-[d_F,k]
      = ([p_F,k]-p_S^(k))
        + (p_S^(k)-p_O^(k))
        + (p_O^(k)-[d_F,k]).

Retain the rounded floating subtraction and its arithmetic remainder
separately. Reproduce the original physical/angular scaling and the
per-derivative-order global normalization from `verify_saved`; angular
scaling uses the existing characteristic length exactly once. Replay only
the derivative-binding submetric. Retain and label the original full
saved-action maximum separately from the immutable saved audit; do not
call full `verify_saved`, projection or Green-norm routines. Preserve its
1e-11 limit and failed status. Exact-arithmetic results must not replace
either the original full metric or its floating derivative submetric.

For every channel and both endpoints, retain the exact signed Legendre
coefficient-error sum and its absolute triangle bound for derivatives one
and two. The second-derivative weights at s=1 are
(j-1)*j*(j+1)*(j+2)/2; at s=0 include (-1)^j. The first-derivative
weights at s=1 are j*(j+1); at s=0 include (-1)^(j+1).
Require exact agreement with the independently differentiated coefficient
polynomial and a valid triangle bound. These identities apply only to
the coefficient term, not the floating evaluation term.

Report raw, signed contributions, bounds and comparisons on the original
normalization. Do not label a small signed contribution an error bound
when cancellation is possible. Agreement with the independent integral
is diagnostic information; it cannot retrospectively pass an old case.

## Execution and evidence

After synthetic arithmetic tests, independent code/mechanics review and
a clean source freeze, register and execute once:

    python scripts/b3_e4_f03_primal_exact_pose.py --run-all --root .qualification/b3-ge-e4-pl/f03-primal-exact-pose-v1

Use the existing supervisor with three serial children, five environment
thread caps equal to the string "1", integer-one threadpool observations,
300s and 1GiB sampled child RSS per
case, and a1200s launch cutoff. Do not run competing scientific jobs or
retry a consumed child. Preserve exclusive markers, identity events,
raw stdout/stderr, receipts and all partial or failed outputs.

The new registration binds this protocol, the mechanics draft, runner,
exact module, unchanged mathematical/input readers, dependencies, runtime,
thread/resource settings and both complete parent inventories. Exact
rational values use pairs of numerator/denominator strings, at most4096
decimal digits per integer, at most2048 rational pairs and at most16MiB
per case JSON; the contained exact-pose record additionally has an8MiB
cap. Validate size before reading/parsing and digit lengths
before integer conversion. Numerators permit one leading minus only;
reject plus signs, leading zeros and negative zero. Denominators are
strictly positive with no leading zeros. Require reduced fractions and
encode zero only as ["0","1"]. The runner freezes exact keys and case
dimensions before registration; these ceilings do not permit extra data.
Display rounding must not affect adjudication. Validate complete output
keys, dimensions, finite displays and exact rational identities against
the saved inputs. The original archives remain the physical-state source.

Terminal precedence is FAILED_EVIDENCE, FAILED_EXECUTION,
FAILED_DIAGNOSTIC_IDENTITY, then PASSED_REPRESENTATION_DIAGNOSTIC.
All three receipts are required for final adjudication. A passing
representation diagnostic means that its independent construction and
attribution identities are verified, not that the original numerical or
physical reference has passed. Retain both parent decisions, unresolved
physical settling, and zero new equilibrium/assembly counts in outputs.

Require independent saved-only postreview and an immutable completed
inventory. Any next spatial residual calculation or revised approximation
requires its own reviewed contract. This diagnostic authorizes no new
physical solve, relaxed threshold, FE-as-reference comparison, native
integration, production-space selection or G0B closure.
