# P5 continuum history and cyclic discrepancy — 2026-09-06

Author research successor to `7d3e92f4b576ecd0c81a78b70709893ec95d0473`,
tree `cf4ff701c79a41a825996e6fab33529f01f5b98d`.
The preceding turn established a controlled virgin-increment comparison.
This turn extends the separate continuum reference through fixed prior
histories and uses identical full load schedules across discretizations.
The full cyclic 2% engineering comparison is **not closed at eight elements**.

## Constitutive reconstruction and fixed origins

The new reference imports only NumPy, dataclasses and the earlier standalone
continuum reference. It imports no discrete element, geometry implementation,
section implementation, AD kernel, recovery or production state machinery.
It remains same-author research, not independent authorship or review.
The public source/version and preserved PDF authority remain those recorded
in `GE_BEAM3_CURVED_P5_NONLINEAR_CONTINUUM_DEVELOPMENT.md`.

For a supplied material origin (z0,p0), the stress-controlled inverse is:

- d = a.s, threshold = y+H p0;
- delta-p = max(0,(abs(d)-threshold)/H);
- z = z0+sign(d) delta-p, p = p0+delta-p;
- strain = C^-1 s + z a;
- inverse derivative = C^-1, plus aa^T/H on the active branch;
- incremental density = 0.5 s.C^-1.s + 0.5 H(p^2-p0^2) + y delta-p.

The supplied history grid contains every RK4 endpoint and midpoint. With N
dyadic-grid integration steps, this gives 2N+1 distinct material origins.
Every shooting candidate and sensitivity evaluation reads these same fixed
origins. No interpolation or material-history advancement occurs inside a
candidate integration. The grid cannot be changed mid-increment, and passing
a history field from a different grid fails rather than silently resampling.

After convergence, a reserved integration exactly reproduces the accepted
endpoint fields and potential. Midpoint positions/frames are reconstructed
by cubic Hermite dense output from the accepted endpoint states and their
actual ODE derivatives. Those fields determine the next increment's midpoint
histories. This is an approximation requiring refinement checks; it is not an
exact continuous-domain history field. No frame projection is applied.

Origin arrays are copied. New histories, strains, resultants, dissipation and
dense fields are returned as explicit result data; there is no hidden live
commit or global history store. The exact binary64 applied force is included
in each result. The caller must explicitly supply the accepted history field
to the next problem. This reference is not a production transaction or
restart API.

## Minimal shared-reference change and bounds

The existing virgin reference gained a material-coordinate inverse hook.
Its default behavior delegates to its unchanged virgin law. The RHS and
endpoint recovery now call this hook, allowing the history successor to
supply fixed material origins. No strain definition, equilibrium equation,
RK4 coefficient, shooting derivative or convergence tolerance was changed.
The previous reference version and its hashes remain preserved in commit
`7d3e92f`; its prior development record is not rewritten.

Per increment: at most 12 shooting updates, eight line-search candidates and
32 integrations **including** the reserved accepted-field reconstruction.
The fixed grid is one of 32/64/128/256/512 steps. Dense reconstruction adds
N+1 explicitly bounded RHS evaluations. Frame drift and determinant checks
apply to dense fields as well as integration endpoints. Budget exhaustion,
inconsistent replay, invalid histories or unresolved frame drift fail closed.
There is no automatic retry, load cutback or grid refinement.

## Identical cyclic experiment

Reference geometry, complete coupled elasticity, direction, yield and hardening
are unchanged from the preceding comparison. The schedule is
`[0.1,0.2,0.1,0,-0.2,0]` times tip-force pattern `[0.1,-0.3,0.2]`.
Unlike the earlier -0.1 reverse segment, -0.2 activates a partial reverse-yield
region in the continuum reference. Every mesh starts from virgin history and
uses the same six load increments. This is an explicit new development case,
not a reclassification or rerun of formal evidence.

At 256 reference steps, 513 material history points are retained:

| Amplitude | Continuum tip displacement (approximate) | Points with positive yield dissipation |
|---:|---|---:|
| 0.1 | [0.03598138,-0.06390458,0.06154385] | 513 |
| 0.2 | [0.16782580,-0.19064851,0.20525831] | 513 |
| 0.1 | [0.17559681,-0.14324221,0.16453174] | 0 |
| 0 | [0.18268684,-0.09419107,0.12233050] | 0 |
| -0.2 | [0.19362783,0.00920234,0.03303234] | 79 |
| 0 | [0.18213052,-0.09399308,0.12183186] | 0 |

Accumulated history never decreases. Reverse-active points decrease z while
increasing p. The last unloading segment retains the prior histories exactly.
There are no negative dissipation increments. These are sampled counts, not
physical-domain measures; reference grid and element quadrature distributions
differ and their raw active fractions must not be equated.

Tip-displacement differences between independently started 128- and 256-step
history cycles are below 3.5e-10 for the first four steps and approximately
1.06e-7 and 1.05e-7 for reverse loading and final unloading. The nonsmooth
yield-front steps do not exhibit the same high-order accuracy as the smooth
virgin case. A separate 512-step diagnostic produced final tip displacement
approximately [0.18213053,-0.09399308,0.12183186], with dense-frame error below
7.3e-12 throughout the cycle. No multiprecision or interval error bound is
claimed. These reference uncertainties are much smaller than the observed
discrete cyclic discrepancy.

Relative Euclidean tip-displacement errors against the 256-step reference:

| Amplitude | 1 element | 2 elements | 4 elements | 8 elements |
|---:|---:|---:|---:|---:|
| 0.1 | 34.02% | 16.71% | 5.53% | 1.51% |
| 0.2 | 47.94% | 23.44% | 7.77% | 2.12% |
| 0.1 | 56.19% | 27.38% | 9.06% | 2.47% |
| 0 | 66.08% | 32.08% | 10.61% | 2.89% |
| -0.2 | 120.35% | 70.96% | 22.27% | 4.15% |
| 0 | 99.11% | 58.76% | 18.42% | 3.42% |

The one-element row is preserved from the exploratory diagnostic. The test
suite repeats the two-, four- and eight-element cycles. Their errors decrease
at every step as the mesh is refined, but eight elements exceed 2% at every
step after the first. Assertions explicitly preserve that unresolved gate.
The existing eight-element maximum was not raised, and no material/mechanical
coefficient, tolerance or scientific criterion was tuned to this experiment.

The last eight-element permanent displacement is approximately
[0.17621422,-0.09069155,0.11727815]. Convergence supports a discretization
explanation for this controlled cycle; it is not a proof over other loads,
material laws, slendernesses or histories. The earlier virgin-only under-2%
result remains valid only for its narrower first-increment case.

## Verification, failures and provenance

- New history-reference suite: **14 passed in 45.26 seconds**.
- Existing nineteen P5 suites: **330 passed in 60.83 seconds**.
- Checks cover separate imports, history stress inversion and directional
  work/derivatives, first-increment agreement, all-origin chaining, unloading
  and partial reverse plasticity, refinement, sampled dissipation, unchanged
  inputs, grid mismatch, bounds, late replay failure, exact-force repeat and
  controlled cyclic discrete convergence with the unresolved error retained.
- The first run had two test-expectation failures. Zeroing midpoint plastic
  coordinates created an unresolved oscillatory field and correctly triggered
  the existing frame-drift guard; the test now requires that fail-closed result.
  The other test reconstructed a force with literal decimals rather than the
  original multiplication, producing an ULP-level input difference. Results
  now bind the exact force, and the repeat uses those original bytes. No
  numerical tolerance or computation was altered to force equality.
- Updated virgin-reference SHA-256:
  `C00C70A2F2B4081AD9CA48CF8F0464701C85DE39D85BBB9FDCE15467F705F3BD`.
- New history-reference SHA-256:
  `3825435E449C00E4CE39AC2A3E46FA8DC886899E502B604972D271195644C9BA`.
- New test SHA-256:
  `1CB56BB75EFC69C9EC3EA3C7D5C3A11FBB728D0B424C38581ABE93AD3A365B26`.

This turn changes exactly the reference hook and adds the history reference,
test and this record. No production source, B2/B3/Q4/S3 mechanics, defaults,
recovery/state law, dependency, package metadata, workflow or historical
qualification evidence changed. No formal request, candidate freeze,
independent review, push, merge, release or activation occurred.

## Next step and full-goal boundary

Prepare an explicitly bounded refinement extension beyond the current eight
elements, with resource authorization if the resulting work is resource-heavy.
Do not silently exceed the registered research driver bounds or relax 2%.
Use the same load schedule and continuum origins/reference controls, and
separately inspect history-dependent quadrature and reverse-yield localization.
Assembled restart/continuation also remains open.

General material adapters, arc length, postbuckling, prestressed modal and
buckling, dynamic integration, the extreme coupled local failure, wider
curved/slender coverage, independent review and installed-wheel production
integration remain required. Objective eccentric/curved beam-shell connection
qualification is still absent. The full objective is incomplete and active.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
