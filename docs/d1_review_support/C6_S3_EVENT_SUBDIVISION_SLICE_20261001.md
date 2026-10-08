# Guided S3 event subdivision — prospective development discriminator

Question: can the affine S3 owner integrate at activation/release instead of
merely reporting a root on a step that spans the event? Preserve the existing
physical mass, penalty force, Newmark endpoint equation and material transaction.
This is development, not general collision or C6 engineering acceptance.

Use the existing candidate lifted path to identify its first pressure-support
transition and the right branch at the start. For active mask A,

    KA = K + B_A.T W_A B_A,
    bA = f_offset + B_A.T W_A gref_A,
    [M/(beta h²)+KA] qA(h)
        = f(t+h)-bA+M[q0/(beta h²)+v0/(beta h)+(1/(2beta)-1)a0].

M remains singular on algebraic coordinates; positive definite algebraic work
and positive physical mass make this branch endpoint solve well posed. It is
the same Newmark endpoint family as the actual driver on a valid branch, not
an extrapolation of the preceding coupled candidate. Loads are constant or
affine within a history interval, whose knots already subdivide steps.

Independent review found that broad sign brackets can select a later duration
root even if that endpoint's reconstructed path is valid. Revised candidate:
condense only the mass-null algebraic work and diagonalize the physical generalized
elastic problem (at most three physical coordinates in this profile). Each mode
has denominator1+beta*h²*omega²; its numerator is cubic for affine loads. Multiply
positive denominators to form each supported-gap numerator polynomial. Retain
every coefficient and use bounded Bernstein sign-variation subdivision to isolate
roots; unresolved multiple roots fail explicitly. Refine the first sign-departure
root in an isolated bracket using the actual branch endpoint equation.
No negative stiffness is clipped; indefinite/pole-bearing families fail explicitly.
Physical mass and positive algebraic work alone are not sufficient for this step.
The Schur PSD roundoff preflight uses uncondensed subtraction/mass scales; every
computed eigenvalue is retained. For grid-boundary roundoff, require actual family
signs on both sides within the explicit time budget and endpoint gap budget.
Affine load extension is used only for that numerical bracket, with no beyond-end
state/work commit or claim about the physical load beyond a history knot.

Validate starting signs at a strictly positive minimum duration. Reevaluate the
actual coupled candidate at the proposed earliest isolated duration from the
same committed origin; independently check endpoint event gaps
and the complete lifted interval. Earlier represented transitions or unresolved
brackets trigger ordinary bounded cutback/failure. Endpoint brackets alone are
not a general first-event/search certificate; no sampling guarantee is asserted.
Initial touch is handled by the right branch and finite minimum duration, not
repeated zero-length commits. No contacts or positive supports are dropped.

New explicit development opt-in requires the algebraic-path/rate options;
separately dimensioned time and gap budgets, finite root/localization caps and
algorithm identity enter restart. Event-localized physical steps commit only
after existing equilibrium, endpoint/path gap, cancellation and state gates.
Default profiles remain unchanged. A localized boundary is a legitimate checkpoint
boundary; arbitrary end-truncated restart rules remain unchanged.

Discriminator: independent scalar free-flight/linear spring, activation with
constant acceleration and unloading/release. Compare q, physical v/a and endpoint
forces against independent scalar Newmark equations at the localized duration.
Then public guided S3 activation, active/open continuation and split restart,
failure/cancellation cleanup and history-knot interaction. First source checks,
then one isolated installed artifact. Routine180s/953MiB/thread1, no consumed
authority renewed. A failed localization gets one discriminating correction;
no automatic iteration/resource budget increase or temporal sweep.

## Prospective resolved-boundary continuation correction

The current source-v11 trace identifies repeated localization at an already
resolved event. Retain the support indices proven to lie within the localized
time/gap budgets as algorithmic boundary state. Only the immediately following
increment may coalesce its contiguous start transitions when every changed
support belongs to that boundary, elapsed duration is within the explicit time
budget and starting gap is within the explicit gap budget. Other supports and
later transitions remain unresolved events. Full penalty residuals, all supports,
path integration and independent interval minima remain unchanged.

At the localized endpoint recover the right algebraic rate trace using those
verified supports as numerical touch locations, bounded by the event gap budget.
This adds no force smoothing or rotational inertia; old rate/path profiles keep
their arithmetic-only touch rule. Physical mass projections remain invariant.
Store boundary supports only after complete physical acceptance; clear them after
the next accepted increment unless that increment ends at another localized event.
Rejected trials keep the committed boundary state. Bind this state into a strict
event-specific version4 restart schema; retain versions1–3 for old profiles and
reject the earlier event prototype's incompatible checkpoints.

Verify the coalescing predicate independently, including nonmember supports and
one-budget-only failures. Rerun the coherent formerly failing module, then split
restart at activation, release and tilted simultaneous supports, malformed boundary
state rejection, failure/cancellation and historical profile compatibility. One
installed artifact follows source/early review. Scientific tolerances, minimum_dt,
resource limits and full programme scope are unchanged.

The first boundary-state correction clears uniform/history/tilted repeat-event
failures, but split restart exposes a4.9e-10rad/s² algebraic acceleration mismatch
at release. A force-based acceleration trial worsened it to6.2e-10 and was removed.
Source-v5 observes existing evaluations only: structural directional curvature is
exactly zero, ruling out that hypothesis. The localized-pose seed and the ordinary
checkpoint predictor follow different arithmetic paths; position subtraction also
amplifies roundoff by1/h². The event profile now initializes both at the same
predictor and accumulates acceleration corrections alongside position corrections.
The residual remains M*a+F; each correction obeys dq=beta*h²*da. The event root
still fixes duration, all complete-path and force/work checks remain, and historical
profiles keep their arithmetic. Source-v6 passes all16 existing event checks at
unchanged tolerances. Extra boundary-state/continuation checks and review follow.
