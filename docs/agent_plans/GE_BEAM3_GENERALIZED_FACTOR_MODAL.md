# Current generalized factor-preserving modal successor

Base bbad553365fb6d10267ea8ed9862ca6aeed94a20, tree
ded772df0968ee1ec16fe19fd338ad379a2bdfac. Five paths: this plan;
src/anysolver/_ge_beam3_native_generalized_modal.py (shared validation refactor);
new _ge_beam3_native_generalized_factor_modal.py,
_native_relative_factor_chain_modes.py; test_ge_beam3_generalized_factor_modal.py.
No beam potential, section/state law, recovery, load, mass definition,
quadrature, existing B2/B3/Q4/S3, public routing or defaults change.

Retain actual current elastic-interior history and conservative load guards.
Refactor the existing replay and model capture so the original dense route
has identical arithmetic/output. The successor captures actual Hqq=G and
Hpq=J plus S=-Hpp. Require exact kinematic transpose pairing. Form the
energy-symmetric compliance by exact pair averaging rounded once, preserving
equal entries including signed zeros. With L=chol(Ssym)^(-1), validate
L S L.T against I at1e-11 using exact supplied-binary64 congruence rounded
once; this checks the original compliance, including skew, in energy units.
No explicit ill-conditioned full inverse is constructed. This replaces a
different failed inverse-based algorithm, not its historical classification.

Use the exact same signed geometric Hessian, not a reference replacement.
Retain the accepted nodal spatial-Jacobian consistency check. Factor the
actual lifted physical inertia at its frozen24-point stations; compare its
Gram matrix with current-rest mass at1e-11. Material/kinematic factors remain
separate through complete dynamic-map reduction. Rounded dense stiffness
is only a preconditioner/diagnostic, never final spectral authority.

The preserved factor-chain kernel remains unchanged. A separately named
successor keeps exact dyadic congruence and all original-chain Ritz, action,
mass and backward checks at1e-11. For broad signed frequency scales use
bracket width1e-10+1e-12*abs(midpoint), at most192 inertia evaluations per
root. Relative width must be explicit finite positive <=1e-10; no automatic
bound expansion. Numerical brackets are not certified intervals. Cluster
completion uses their own widths; no truncated cluster is accepted. This
changes root-search discretization, not physical error acceptance criteria.

Freeze full12-mode one-macro clamped comparisons, not only weak modes, for
all12 previous straight/curved/rotation specimens at rho100/10000/1e6.
Bounds(-100,1e28), compare all12 squared frequencies with hash-bound saved
100-digit supplied-factor roots at1e-11 normalized by max(1,abs(root)).
That reference is same-author and does not qualify continuum slenderness.
Historical diagnostic failed byte criterion remains failed; no old record
is rewritten. New signed-zero/input ownership checks precede mechanics.

Separate inventories: new local24 tests/24 records (kernel3, invalid4,
compliance3, input8, material2, live1, reference2, signed prestress1);
inherited dense modal-local17 tests/17 records; inherited prestress-local3
tests/3 records; each rho one test/five records on complete success.
Check collection counts before execution. Local smoke precedes the three
rho rehearsals. Only if all pass, two fresh-directory repeats, with identical
science separately by inventory, and existing continuum group regression.
Failure preserves partial outputs and blocks this successor; no retry.

All children one numerical thread,24GiB,600seconds,120second CPU inactivity;
at most three concurrent,1800seconds per wave. Signed eigensolver600seconds
cooperative limit remains. Independent review PENDING, production false.
Broader static conditioning, materials, curved/loaded dynamics, engineering
continuum/slenderness qualification, installed integration and objective
beam-shell connection remain required. Full goal active and incomplete.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
