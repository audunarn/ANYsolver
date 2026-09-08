# Saved-factor paired-mode experiment

Base61afe74a037675a70241465d52e6aeaaf1f81054, tree
70c49595e8219ce0b3ef2427a6e14e1f3cfe8304. Three added research-only paths:
this plan, paired-mode experiment helper, test. No production source changes.

Use only the two hash-bound pre-validation captures from18845e1, never rerun
the mechanical specimens. Freeze before execution. Keep all12 roots unchanged.
Apply ordered two-pass modified Gram-Schmidt in the unchanged kinetic metric,
then expand the complete coordinate map into high and low binary64 arrays.
The low array is the rounded exact-dyadic residual of expansion, not added
stiffness, inertia or an empirically selected coefficient.

Reassemble complete original signed energy and physical kinetic Gram from the
exact sum of both halves, rounded once only at the comparison matrix. Require
both original checks at1e-11. Save rounded-only counter-comparisons rather than
silently claiming that high alone passes. Save results before assertions;
preserve every failure. No normalization substitutes for work validation.

Separate inventories: one exact low-part unit test, then two saved-factor
experiments. One worker, one numerical thread,24GiB,600second child,
120second CPU-inactivity watchdog,1800second whole-wave bound. Fresh external
output, exclusive creation, clean source guards, no automatic retry. No
full-spectrum, mechanics or qualification cycles in this experiment.

A pass demonstrates only that the saved numerical representation can satisfy
these checks; it does not qualify the kernel or supply missing full-action,
state, covariance, continuum, restart or package tests. Any implementation
successor must retain original checks, explicitly own/hash both vector halves,
and never hand a high-only diagnostic to a caller as a validated mode.
No goal narrowing. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
