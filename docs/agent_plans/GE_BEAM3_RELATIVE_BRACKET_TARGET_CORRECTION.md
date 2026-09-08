# Target-aware relative-bracket correction

Base97abdbd78085e8a84ff31c7d42916efea58d46b3, tree
7dc8babb5cdf511e7eef390cbfff895ede4c17bd. Preserve its complete68-file
archive and failed local signed-wide test; no historical rerun/reclassification.
This five-path successor changes only _native_relative_factor_chain_modes.py,
this plan, and adds the initial status/archive records (four paths total).
The existing failing test is retained unchanged as the regression witness.

The signed-wide diagonal specimen has roots(-2,3,1e24), search bounds
(-10,2e24). While seeking the first root, the midpoint lands on the third.
Resolved inertia counts around that midpoint locate the target entirely to
its left, but the draft algorithm incorrectly raised. If counts a,b surround
the probe and target ordinal i<a, retain the left interval; if i>=b, retain
the right interval. If a<=i<b, close the target bracket. Reject a>b. This
uses monotone inertia of the already validated positive-mass pencil and
adds no root, shift, mass, coefficient, tolerance or iteration-budget changes.

Initial separate results: collection27; adapter-local24 tests,23 passed/one
failed; dense-local17 passed; prestress-local3 passed. Dense/prestress science
is byte-identical to its hash-bound accepted development baseline. No slender
specimen or repetition was launched after the failed smoke inventory.
All process trees are empty; initial status remains blocked.

Retain every case, error criterion and resource bound from
GE_BEAM3_GENERALIZED_FACTOR_MODAL.md. First run the single signed-wide witness
as successor smoke, then the complete24-test adapter local and separate17/3
inherited inventories. Only after all pass, run the three rho rehearsals,
then two fresh-directory repeats and continuum regression if all remain clean.
Single-witness output must match that test within subsequent complete runs.
No automatic retry. One numerical thread,24GiB,600seconds per child;
three workers maximum,120second CPU inactivity,1800second wave limit.
No production qualification or independent review is claimed.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED; full goal active and incomplete.
