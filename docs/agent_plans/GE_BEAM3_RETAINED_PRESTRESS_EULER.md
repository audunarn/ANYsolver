# Actual retained nodal preload and Euler refinement gate

Base `6f693654e54cc02533f7cf8c25f6510a6d98d43c`. Research helper/tests only;
all element, load, state, section, spectrum arithmetic and public/default
implementations remain unchanged. Preserve all old evidence and failed candidates.

Use the existing straight clamped-free length-2 generalized modal fixture,
EA=1000, uncoupled section, weaker EI=1 and existing physical section inertia.
Refine through 1,2,4,8 macrocells. Euler reference remains pi^2/16. Each sampled
compression is applied as a physical tip nodal dead force through the retained
Newton programme with targets (0.5,1.0), from stress-free genesis. No analytical
state seeding or manufactured accepted state. Verify resulting signed F/EA
translations and actual reaction at 1e-11; preserve the complete checkpoint.

For this particular uncoupled straight family, prove exact structural-zero
separation of axial, torsion and the two spatial bending families in the ORIGINAL
factor chain. Boolean nonzero support of left/right material factors must show
no output row shared across families; kinetic rows and signed geometric entries
must likewise separate. Reject even 1e-200 cross-family support. Never expand a
rounded stiffness to establish this proof or drop merely small entries.
Extract original subarrays by removing only proven zero coordinates/factor rows;
retain the existing exact-dyadic paired solver and its 1e-11 action/Ritz checks.
This optimization is not admitted for general coupled/curved models.

Check the partition against a complete paired solve locally and at the four
initial N1 preload values. Solve and require positive axial/torsional minima
once per mesh, and verify their complete extracted arrays stay exactly equal
at every preload. Both bending families are solved at every point; neither
spatial instability is discarded. The minimum bending root determines the sign.

Keep the prior 22-point search: tension at -0.5 Euler, zero, compression at
0.5 Euler, upper bound 2 Euler, then exactly 18 bisections of the signed spectrum.
Require tension > unloaded > compressed > 0, negative upper root, final opposite
sign bracket narrower than 1e-5 Euler, and finest N8 critical-load error below 2%.
The complete audit checks decreasing critical-load error with refinement.
Current squared frequency is not itself a buckling load factor.

Smoke the six partition checks before N1. Stop expansion on failure. Run N2
before N4/N8. Each mesh invocation must fit 600 seconds; do not add retries or
relax a gate if a resource or scientific failure occurs. Two fresh-directory
cycles of the passing complete mesh inventory must be byte-identical.
All children: one numerical-library thread, 24 GiB Windows Job process tree,
600-second wall limit and 120-second CPU-inactivity watchdog. At most three
workers and 1800 seconds per wave. Preserve checkpoint/progress/failure logs;
no canonical partial aggregate. Runtime remains a diagnostic, not a speed claim.

This adds actual programme-path evidence to the existing reference problem,
not full spatial postbuckling/curved engineering qualification. Broader material/
fibre and solver parity, practical scale, independent review, full environment,
installed public opt-in integration and objective shell connections remain open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
