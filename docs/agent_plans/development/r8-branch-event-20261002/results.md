# Private branch-event trial — 2 October 2026

Decision: native generalized-cell branch-event estimates can guide this previously
failed displacement correction without changing constitutive equations, tolerances,
Newton/backtrack limits, the full displacement predictor or accepted state.
Public policy/checkpoint binding is NOT implemented; this is a private prototype.

The cell optionally returns directional indicators from its existing implicit
station-force sensitivity, native moment interpolation and fixed accepted radius
Y+H*p0. Margin uses q-radius in the same Decimal evaluation order as _dual.
Default response output remains unchanged. A finite positive crossing estimate
proposes min(1,1.01*t_event), followed by actual assembly and strict merit decrease.
Exact yield-boundary cases fail explicitly in this prototype. These are estimates,
not exact event roots or guaranteed crossings. Extra cell work is counted.

## Evidence

Source checks: first2pass/1failure was an overly specific NaN-message assertion;
existing finite-input rejection was correct. Corrected7checks pass28.62s. Subsequent
exact-boundary guard and work-accounting checks are covered by installed tests.
Independent design/code review corrected subtraction order, explicit boundary
handling and separate cell-work counts. No remaining blocking finding recorded.

One private -68um trial from the unchanged accepted -66um checkpoint succeeds:
load-487.09113664022675N, amplitude0.173832744974511, equilibrium1.5128430104253568e-11,
gap8.563536514300473e-18.11iterations,13global evaluations,12linear solves,0rejections,
22additional event-cell responses. Eight event-limited corrections then three full
corrections. Source run6.22s, peak165302272bytes. No accepted publication occurred;
checkpoint remained byte-identical. It does not complete -500N or later targets,
restart continuity, stability or capacity qualification. No speedup claim.

Installed wheelaf4e498c3d0bb1309dc2a736044713c8c722d189dac0f4ac13da30f099f57191:
405source/wheel/site modules match. Initial collection failed because a copied
reference fixture was missing; no numerical tests ran. Fixture repair retained the
same wheel.9checks then passed31.80s, supervised33.72s, peak177664000bytes, including
candidate reproduction, loaded/virgin implicit sensitivities, default response
parity, exact boundary rejection/work counts and default corrector regressions.
Runtime asserts onsite imports, numerical pools1thread and JIT disabled.
Independent result review confirms only the narrow private endpoint success.

Archive private-candidate-installed-v1.zip SHA256 73c5758f9270e81c57a0ee60601086d00f2d11b3188dcb0920a8ca62d5b2ffca.
Contains failed runs, source/fixtures, seed, raw candidate, installed identities,
runner and safe metadata; no inherited environment maps.

Next: explicit public trial-policy identity bound from the start of the displacement
path and preserved/rejected appropriately on fixed/adaptive restart, including
counted event work and no changes to defaults. Verify integrated behavior before
extending the physical path. Original failures/F03 authority and all full-programme
acceptance requirements remain unchanged.
