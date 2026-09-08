# Native uniformly loaded arch development

Base c34baeea2ab155b071abe90c2963a31856763f7d. No mechanics changes.

The crown point-load benchmark cannot currently run through the new native arc
programme without a new nodal-force adapter. Use an explicitly different
uniform spatial dead load per reference arclength, already supported natively.
Do not relabel old crown-load results or claim equal branches.

The continuum background is Bali et al., DOI 10.1002/nme.6994, equations 6--11
and 15--17, https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/ . The following
specialization is same-author work, not independent review. No ANYsolver
mechanics is imported by the continuum implementation.

For y0=.1(1-X^2), X in [-1,0], define F(X) as signed reference arclength from
the crown. With uniform downward density q, balance gives nx=constant and
ny=q F(X); F'=J0. Crown symmetry imposes x=0 and theta=0, not a concentrated
crown force. The left end is clamped. Prescribe crown drop, solving the four
position/rotation/moment ODEs and two parameters nx,q. Use EA=1000, GA=400,
planar EI=.01, normalized uniformly by EA before collocation. This is an
elastic continuum family, not a plastic beam certificate.

Differentiate this BVP analytically to obtain dq/d(drop). Check off-grid ODE
and sensitivity residuals, clamped/symmetry boundaries, positive stretch, and
dU/d(drop)=-2q integral(delta y ds0). BVP7/BVP9 keep 1e-7/1e-9, 1025/4097
node limits, 2000 callbacks and 60 seconds per solve including sensitivity.
Compare density and slope within 1e-5 normalized between profiles; this is
reference resolution, not the separate 2% engineering qualification gate.
Fixed drops are .01,.025,.04,.055,.08,.1. Do not choose reference constants
or tolerances based on native errors. No generic simplify or mechanics import.

First verify reference derivatives by complex step, stress-free geometry,
force balance and two-profile resolution. Preserve its complete diagnostic
records. Then prepare a native two-macro smoke fixture with identical parabola,
section and full clamped end nodes; all interior spatial DOFs remain free.
Choose explicit arc scales/steps from the resolved reference, not by tuning
mechanical coefficients. Check full native state replay and compare at actual
accepted crown drop. A coarse result or lost convergence is diagnostic, not
qualification. Do not expand an expensive wave before this probe completes.

Each child: one numerical thread, 24 GiB Windows Job process tree, 600-second
wall, 120-second CPU-inactivity cutoff; at most three children and 1800 seconds
per wave. No automatic retry. Preserve any failure and all historical evidence.
Full spatial stability, actual native limit-point crossing, practical-scale
convergence, mass/spectra, review, public integration and joints remain open.

## Resolved-reference-guided smoke, before native observation

Nine reference tests passed in 3.614 supervisor seconds. Two-profile maximum
normalized density/slope difference is 1.5134542613592927e-7. At drop .01 the
resolved density is .054249981808877475 and slope -.3283567737190095; all six
registered drops have negative slope. Inspect a distinct early sequence
0,.001,.002,.004,.006,.008,.01 to bracket the turn from the stress-free state.
This is new reference sampling, not replacement of the completed inventory.

Freeze the native two-macro smoke at four arc steps (.2,.2,.2,.2), length scale
.1 and parameter scale .1. The unloaded predictor therefore has a density
increment no greater than .02; the four steps are only a smoke, with no claim
that the coarse native turn will be reached. Use order 4, the reference EA/GA/
planar EI and explicit remaining torsion .008 and other bending .01. Both end
nodes are fully clamped; every interior spatial DOF is free. Use the unchanged
generalized law with yield 1e6 and hardening 1, then require every accepted
history to remain elastic. Compare actual accepted crown drops with BVP9 and
report relative errors without a coarse-mesh pass threshold. Full native
checkpoint decoding is required. Preserve any failure rather than retrying.

## Smoke and diagnostic incidents

The native smoke failed at step four with line-search exhaustion after three
accepted steps. It is not retried. Its complete accepted checkpoint is 298555
bytes, SHA-256 A73AF73CC0433E72850A5B8BD2B17624AEF8AAEAB09C247C8FC5D42B2E0740C0.
Replay and compare this preserved prefix without advancing the native path.

The first prefix-reader invocation failed before mechanics because the CLI
resolved the installed ANYsolver rather than the private source checkout.
Preserve that invocation and its script. Correct only CLI source-path setup
after input-hash verification, and verify the imported package path explicitly.
Run a new corrected read-only diagnostic; this is not a repeat of the failed
native smoke or a change to beam mechanics, reference equations or tolerances.
