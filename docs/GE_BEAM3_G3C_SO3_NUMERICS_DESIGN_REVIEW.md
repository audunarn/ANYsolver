# Independent isolated SO(3) kernel design review

Subject `e7136a913f294c1990c89d4a53b7ef0c67e3268c`, tree
`cdc8215d94bdbce1fae601af9168356f3fbf48bd`. Reviewer
`/root/g3b_independent_review` accepts implementation and bounded testing of
this isolated, unrouted kernel only. The two-file design extent and six frozen
source bindings were checked independently; checkout is clean and diff-check
passes. No kernel implementation or graph mechanics was executed.

The degree-16 Exp series and degree-40 Log series, with differentiated Horner
evaluation, preserve the mathematical functions while avoiding the demonstrated
small-argument derivative cancellation. The half-angle Exp expression is
algebraically correct. The closed Log formulas are safe from the near-one
catastrophic cancellation on the newly selected complementary interval; for
negative cosine their terms have matching signs. The strict lower chart guard
is unchanged. Slight trace roundoff above one is handled by analytic
continuation rather than clipping a differentiated coordinate.

The a-priori tail estimates are valid: at delta=0.5, the exact first omitted
Log second-derivative term is about 1.861e-22, and a decreasing-ratio geometric
majorant is about 2.513e-22, below the conservative stated 3e-21. The first
omitted sinc second-derivative term at x=1 is about 2.633e-38, below 1e-35.
The 1e-13 rounding discussion is a conservative engineering estimate, not a
correct-rounding theorem; the independent full-interval executable accuracy
gate remains mandatory and may still reject an implementation.

The new evaluator may reuse unchanged Jet arithmetic but must not call old
coefficient/rotation entrypoints or redirect any existing caller. This avoids
silently changing the 23-importer shared dependency graph. Static isolation,
bound hashes, no existing-file delta and independent review must establish that
boundary before the private kernel can pass.

## Independent oracle supplied

`g3c_decimal_so3_oracle.py` in reviewer scratch independently implements Decimal
coefficients, scalar chain rules, matrix Exp/Log, value/gradient/Hessian. It
imports no NumPy or anysolver code. Scalar references use factorial/recurrence
series over the complete selected Exp range and admitted Log range, with
adaptive geometric derivative-tail bounds, not candidate piecewise formulas.
The requested Exp range through (2pi)^2 is covered by its explicit x<=40 bound.
The Log series has a hard 16384-term ceiling and fails rather than returning an
unconverged reference. The elementary oracle self-test passed in about half a
second, including full-Jet Log(Exp(v)) identities and 90/110-digit rounded
reference agreement near the relative chart limit. No mechanics runs occurred.

The oracle self-tests initially exposed two scratch-only harness issues, both
corrected before delivery: exact Decimal equality was too strict for two
equivalent rounded recurrence expressions at zero, and an 8192-term ceiling
was insufficient for the requested 110-digit near-limit convergence criterion.
The corrected test uses a 1e-98 Decimal zero-limit check and bounded 16384-term
ceiling. These are reference-development fixes, not changes to candidate
thresholds or mechanics. All expected binary64 comparisons remain 1e-11.

For full-Jet testing use non-axis-aligned directions and both sides of every
old/new branch. Log(Exp(v))=v applies only within the admitted principal chart;
common 1.4pi tests must compare Exp to its oracle (or the correctly wrapped
principal Log), never assert equality to an unwrapped 1.4pi vector.

## Remaining gates

Freeze concrete separate static/scalar/full-Jet node inventories and the exact
independent oracle bytes before execution. Author suite must pass before the
independent bounded rerun. Only a successful kernel result permits preparation
of a separately reviewed private dependency graph; existing failed directional
evidence, source contracts, conventional Q4 recovery and B2 clamp recovery
remain unchanged and open. No graph, public, restart, release or default
integration authority is granted by this design review.
