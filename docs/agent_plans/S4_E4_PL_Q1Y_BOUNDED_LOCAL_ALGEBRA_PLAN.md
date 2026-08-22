# E4-PL-Q1Y: Bounded Local-Algebra Closure

Q1Y is a research-only successor to Q1X.  It evaluates the actual 35+3
stationary system for the seven registered base geometries, then extends each
base result to all eight D4 numberings through exact internal-operator
congruence.  It does not rerun Q1V, solve supported KKT systems, authorize Q1B,
or modify production code.

One standard-library exact producer per geometry emits inverse, Schur, rigid,
quotient, and LDL witnesses.  A separate SymPy checker reconstructs the source
operators without importing producer mechanics and verifies the witnesses by
exact algebraic-field multiplication.  The checker never recomputes symbolic
matrix inverses or factorizations.  Equality is domain-element equality;
ordered signs alone use independent 256/512/1024-bit outward dyadic bounds.

Seven producers run in batches of three.  Each proof is checked twice in fresh
processes, with at most four checker processes.  Every child is limited to 600
seconds, 24 GiB, and one numerical-library thread.  No retry is automatic and
no canonical aggregate is created until every child has terminated.

Exact local-algebra contradictions are NO-GO, exact operator-covariance
contradictions are a separate NO-GO, unresolved ordered signs are
UNCLASSIFIED, and process or review failures are BLOCKED.  Passing all bounded
requirements closes local algebra only and remains UNCLASSIFIED pending a
separate support/KKT successor.
