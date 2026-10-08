# Named cylinder-static benchmark candidate — 4 October 2026

**Reviewed base:** 34cac87a; manifest binds the execution candidate. **State:** specification for prospective assessment,
not an accepted profile. Production baselineadbdfa3d; wheelSHA256
f6a1b3dc3318d4e8ec5faea8c4b26c933a61970c0e2cbe422440b19df185dfab.
The goal authorizes a bounded claim-bearing run; no earlier consumed authority is
used. The immutable manifest binds this specification, fixture/reference/test and
installed package bytes, exact selections and environment before formal execution.

## Claim and exclusions

Assess the **named** elastic small-motion B2/B3 cylinder-static benchmarks below:
axial force/displacement control; distributed axial mesh/enforcement response;
free plane-limit bending and scalar line-density resolution; fixed-body committed
press/open/recontact and open-state restart; guided curved B3 interior and active
hemisphere-rim work; guided prescribed-cylinder translation and explicit seed.
The scope is the literal fixtures and controls, not arbitrary models or a continuous
parameter range. Positive disposition closes these benchmark evidence rows. It
does not independently admit the general development API, other shapes/materials,
non-round envelopes, finite rotations, friction, native beams or dynamics.

No new public capability/default/restart identity, normal application admission,
release, publication or fullD3/C0–C9 completion follows. A PASS cannot erase prior
failures. Development results are exploratory inputs to this candidate, not its
formal outputs. Prescribed translation plus staged loads remains excluded.

## Frozen inputs and scientific checks

All literal inputs live in the manifest-bound parameterized fixtures, including
loads, supports, section properties, structural routes, radii, cap/line laws,
integration/iteration/path controls and independent equations. No tuning follows
the formal output. The fixture's fixed scales apply to every comparison.
For eachB2/B3, the literal axial continuum(cells,linek) selections are
(1,1e9),(2,1e9),(4,1e9),(4,4e9),(4,16e9). Bending32/64cells use baseline
linek1e4/capke10; only64cells additionally use strongerlinek1e5/capke100.
The64baseline repetition in the line-field test is deliberate: it produces the
field comparison and within-run enforcement contrast, not a new mesh selection.

| Row | Inputs / independent reference | Gates |
|---|---|---|
| Axial continuum | L=.2m, EA=1N, P=.02N, Rcombined=.11m, actual left cap ke=1N/m; B2/B3 cells1/2/4, linek1e9/4e9/16e9N/m². Independently derived hyperbolic unilateral continuum, direct polynomial work/gap quadrature | displacement/root/contact reaction0.1%; relative equilibrium1e-6; gap10um; positive line contribution; decreasing penetration under stronger line enforcement |
| Free bending | L=1m, r=.01m, E=1e7Pa, nu=.3, q=.001N/m, clearance.001m; fixed cylinderR=1e7m; clamped root, freeUX/UZ/RY. B2/B3 cells32/64; linek1e4/1e5N/m² and capke10/100N/m | tip/total reaction0.1%; force scaleqL, moment scaleqL², separate wrench residual1e-6;10um gap; active tip sphere/true-end ownership |
| Line field | same bending64cells, reference measure. Independent polynomial activation roots and quadrature of signed physical line density; continuum's actual tip spring retained | normalizedL1/L2<=2%; independent minimum gap10um and width agreement1e-6; integration-error estimate<=.002 of normalized line response (one tenth of2% budget); stronger enforcement reduces penetration |
| Reference arithmetic | single active interval Timoshenko ODE Q=S(w'-theta),M=Dtheta',M'=-Q,Q'=k(w-c)+-q; tipM=0,Q+ke(w-c)=0; separate80-digit Taylor transfer | front residual1e-10; tip boundary residual1e-60 in independent arithmetic; reference reaction agreement1e-9, tip1e-10; open-branch extrema/positive active-branch velocity controls |
| Axial code/control | existing exact axial matrices, independent line/cap energy, literal force/displacement controls | signed displacement1e-6relative; inherited reaction/cap-energy2e-6, line-energy2e-5; whole normalizedforce/moment1e-6; inherited gap/action-reaction checks; actual endpoint/interior forces |
| Cycle/restart | one immutable unit-factor programme with tip increments-.02,+.04,-.04N; fixedR=.1m/r=.01m cylinder, initialgap2mm; prefixglobal2, freshJSONresume3 | every committed actual displacement/contact force/root reaction1e-6relative or1e-10absolute; actualforce balance1e-10N;10um gap; real open line/cap state; resumed terminal states/forces agree; excluded moving-load-program rejects |
| Curved work | manifest-bound guided B3 interior/fixed-moving and moving active-rim fixtures; separate shear/axial work, planar cap potential and line polynomial quadrature | inherited1e-6 response/wrench and10um independentgap; active widths1e-6; rim smooth tangent1e-5 over three perturbations; reference explicitly rejects outside its planar domain |
| Installed handoff | unchanged public examples, capability/development rejection and actual module/source bytes | expected development identities, no unsupported normal application admission, installed-source parity and effectiveJIToff/Numba+pools1 |

The1e7m-radius bending benchmark is a **plane-limit discriminator**, not an exact
arbitrary-cylinder continuum solution. Nominal cylinder height mismatch<=12.5nm
is separately reported; displaced stations, exact-radius addition and literal
clearance roundoff are recorded. Structural mesh/curve/load approximation and
von Karman versus linear-reference differences are included in the response error,
not attributed to a single convergence order. The reference admits one active
interval only. SciPy/quad error estimates are not outward certificates; independent
transfer and root/branch controls bound the specific numerical adequacy claim.

## Evidence reuse and execution

The existing source/installed geometry-work, stationary-root, virtual-work,
both-body mapping, tangent, full/backtracked swept path, rejection/cancellation/
exception, incompatible checkpoint and no-contact evidence are unchanged by this
test/reference-only integration. Bind their existing summary/inputs by hash and
use source impact, not an irrelevant repeat. No requirement is waived.

Fresh formal groups are separate bounded calls to the existing run.py supervisor:
mesh/reference, line-field/cycle, axial continuum, and curved/control/handoff.
Each has180s/953MiB process-tree limits, own exclusive raw directory, explicit
installed2 import root, no automatic retry. Manifest freezes full commands.
Do not change the supervisor to conceal failures or change gates afterward.
Any timeout, failure, missing output, import/environment mismatch or scientific
predicate failure is NONPASS for its row; unaffected rows remain separately
identifiable. A corrected candidate needs a new identity and prospective scope,
not overwritten evidence or implicit authority renewal.

Review this specification before formal runs and assess the package afterward.
Independent analytical/continuum/transfer methods provide claim-matched scientific
comparisons; same-family source scrutiny alone does not establish independence.
Keep implemented, tested, independently assessed benchmarks, admitted capabilities
and released status distinct. A benchmark PASS leaves general D3 admission open.

## Supporting specification review

Read-only reviewercurved_initial_review found and closed mismatches in explicit
axial equilibrium, inherited force/energy tolerances, literal mesh/regularization
selections and actual versus reference applied load. Current specification is
reviewable subject to complete manifest verification. No formal outcomes were
observed during this review. It supplies supporting scrutiny, not a sole scientific
independence or engineering-profile admission claim. Independent mathematical and
numerical references remain required by the rows above.

The unchanged supervisor's raw input metadata says code development/no acceptance.
This new prospective specification/manifest identifies the **fresh named benchmark
assessment** selections; the final assessment records their disposition. That does
not relabel old runs or promote any general development profile. The manifest
adds transitive fixture/reference identities absent from the legacy raw header.
