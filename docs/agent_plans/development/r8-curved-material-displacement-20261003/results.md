# Curved material displacement control — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** The existing public displacement controller now
admits explicit curved-Q4/full-pose-point models with generalized native B3
plasticity and optional shell J2. No aggregate programme gate closes.
Source parent: `a8a75970`; the final product bytes and installed test fixtures
are bound by the artifact manifest in the fresh raw archive.

## Delivered behavior

An accepted force-controlled seed can continue to absolute translation targets
through the existing `solve(..., displacement_control=DisplacementControl(...))`
operation. Fixed and adaptive stepping retain fixed accepted beam/shell
predecessors, detailed material recovery, atomic cancellation, chart rebasing
and exact checkpoint continuation. A fixed displacement endpoint can seed the
existing arc controller; returning an arc history to displacement remains
rejected. The applied load is the seed load plus the solved amplitude times the
declared load direction; amplitude is not a force-control load factor.

The new `finite_displacement_curved_material` mechanical kind and
`B3_GE_CURVED_MATERIAL_POINT_DISPLACEMENT_V1_DEV` policy distinguish the route
from legacy BL5. Separate chart/event identities and model binding preserve
compatibility. Elastic shells omit J2 history arrays symmetrically throughout
encoding, decoding, mechanical replay and recovery. The shared envelope and
legacy BL5 policies/full array order remain unchanged. No equations, material
laws, convergence tolerances, default settings, trial budgets or version changed.

## Checks actually executed

- Source v1: six passed, one adaptive restart failure. The outer adaptive decoder
  still admitted only BL5. Its explicit-profile guard was repaired; only the
  failed case was repeated, passing in 19.710 s supervised. Both executions remain
  retained; the passed source campaign was not repeated.
- Fresh legacy oracle: the preceding installed wheel generated a valid yielded
  BL5 displacement endpoint in 27.124 s / 165,593,088 sampled process-tree bytes.
- New installed solver: **25 passed**, 320.017 s / 199,774,208 sampled bytes.
  Coverage includes signed yielded loading/unloading, matched force endpoints,
  exact material/reaction/history restart, corrupted predecessor rejection,
  foreign-profile rejection, stale publication, cancellation before publication,
  optional elastic-shell adaptive restart, chart/event policies, displacement-to-
  arc transition and affected legacy displacement/arc contracts.
- Legacy compatibility: new-wheel recomputation produces the old-wheel checkpoint
  **byte-for-byte**. Restoration and a further displacement increment reproduce
  exact histories, material records, reactions and checkpoint bytes.
- Paired installed ANYfem: **two passed**, 35.150 s / 187,179,008 sampled bytes.
  Strict standalone/native Project save/reopen with native retained scaling,
  force seed, displacement, separate state restoration and continued displacement
  match exactly for both elastic-shell and shell-J2 configurations. ANYfem product
  code is unchanged.

All **413 solver and 98 consumer modules** match source, wheel and installed site.
Imports came from the declared sites. Effective BLAS and Numba numerical pools
were one thread, JIT disabled; all serial jobs stayed within 600 s / 1 GiB.
These are verification costs, not optimization measurements.

Solver wheel SHA256:
`c5f28ee7190e3185f0faa57ece88958f1b7918e48a5cb0e4b7c66cd56529f097`.
Consumer wheel SHA256:
`937eb59f99fc72463af3daad8c7363755fb957648f81d7647591305af61d3374`.
Old solver oracle wheel:
`780e77539f6c511026ff626485af7d583cc5562f7f4c7452e0fbc45222489e34`.

## Review and limits

An independent OpenAI source reviewer, not the implementer, found no confirmed
correctness defect in identity/layout binding, fixed-predecessor replay,
cancellation/atomic publication or adaptive restore isolation. Four requested
regression consequences were added and passed in the installed suite. The
integration owner inspected the final diff, executions and artifact correspondence.
This is development review, not cross-family scientific acceptance; previously
unavailable optional reviewers were not probed again.

The bounded force/displacement comparison uses development `rtol=1e-7` with
quantity-specific absolute floors recorded in the test. It is not a relaxed
programme criterion or independent mechanics reference. Accepted equilibrium
`1e-8` and scaled constraint `1e-9` remain mandatory. The fixtures use declared
development material laws. Curved S3, physical fibres, line/footprint attachment
qualification, broader loads/topology, units/mesh envelope, scale, external and
platform acceptance remain open. No F03, external execution, main merge, push
or publication occurred.

## Evidence

[Execution summary](summary-v1.json) and
[fresh runners, test fixtures, imports, manifests, legacy oracle, source failure,
repair and review](raw-evidence-v1.zip).
Raw archive SHA256:
`766e3afea05ef0a1d69c4c858db4acc50fbe2e33902ff4327bb2c7df8314868d`.
Execution metadata uses an explicit whitelist. No inherited environment map or
protected historical archive was read or copied.
