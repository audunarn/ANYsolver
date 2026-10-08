# Curved material point continuation — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** The existing public arc controller now admits the
explicit curved-Q4 material point profile with generalized native B3 yielding
and optional shell J2. No aggregate programme gate or release is accepted.
Source parent: `80c3920c`; final source bytes are bound by the installed artifact
manifest in [raw evidence](raw-evidence-v1.zip).

## Change and decision

The continuation trial already evaluated all domains from one accepted parent.
The blockers were the elastic-only arc identity and BL5-only shell history
replay/publication. A separate `finite_arc_curved_material` binary kind and
`B3_GE_CURVED_MATERIAL_POINT_TANGENT_PLANE_V1_DEV` controller policy now bind the
material route. The existing affine endpoint replay and atomic publisher handle
the optional admitted Q4 material state explicitly, without forging a BL5 flag.
Accepted and predecessor histories are both retained. Old elastic/BL5 identities
and layouts retain their meanings.

The physical chord metric, tangent-plane method, trial budget (maximum twelve
backtracks), cutbacks and physical acceptance checks are unchanged. Required
free equilibrium is `1e-8` and scaled compatibility is `1e-9`; an exhausted budget
still fails. No equations, material integration, defaults or version changed.

## Checks actually executed

Final focused source route: **4 passed**, 67.229 s supervised, sampled process-tree
peak 181,592,064 bytes. The installed campaign passed **21 checks**, with two
fixture errors; after supplying their missing binary seed, **only those two**
legacy checks were repeated and passed. Thus **23 distinct installed solver
checks passed**, including:

- Both-domain yielded loading and unloading, two continued arc increments,
  exact fresh restart and detailed shell/generalized-station recovery.
- Force-control endpoints at the same accepted predecessor and physical load
  increments, with declared development comparison floors (`rtol=1e-7`).
- Valid-digest altered shell/beam predecessors and wrong elastic-policy rejection.
- Cancellation after one accepted prefix and immediately before commit; stale
  publication preserves generation and checkpoint.
- Generalized beam yielding with elastic shells and no artificial shell histories.
- Legacy curved-elastic arc, BL5/J2 arc, displacement endpoint contracts and
  attempt/cancellation bookkeeping.

Installed solver wheel SHA256:
`f69b70e39f7c6416401c3ef0e55ee8102401b4902c41b79d55c95c541797e191`.
All **413** product modules matched source, wheel and installed site byte-for-byte.
First installed execution: 70.522 s / 193,150,976 sampled peak bytes; missing-seed
repair execution: 46.357 s / 178,950,144 bytes. These are verification costs,
not speedup measurements.

Paired installed ANYfem checks: **2 passed**, 20.237 s / 192,217,088 bytes. A
nonrigid virgin material reference survives standalone and native Project
save/reopen, develops shell and beam yielding, continues through the existing
public operation, then reproduces its continued history, every checkpoint,
shell states and generalized station records after fresh restoration. Strict
consumer input negatives remain covered. All **98** consumer modules match the
unchanged wheel/site/source. Consumer wheel SHA256:
`6435122e6aded71bcaa3b16a535c23efc15889367f85aa4810c77256d07e2b10`.
Solver and consumer imports were inspected; effective numerical thread pools
and Numba were one thread, JIT disabled. Every child remained within its
600 s / 1 GiB development ceiling.

## Failures preserved and review scope

Source v1 used eight backtracks for a seed whose existing fixture specifies
twelve; three seeds failed before arc execution. A guard-message assertion also
failed. Source v2 reached material arc acceptance but an old restore guard had
not been removed. Source v3 passed all three continuation tests and failed one
message assertion; final v4 corrected the assertion and added consequences checks.
The first installed solver run omitted a 15,067-byte legacy binary fixture; the
first consumer run omitted an imported fixture module. These are retained as
failed executions, not mechanics failures. No passed numerical campaign was
repeated to repair the missing fixtures.

Integration-owner review traced kind/layout binding, fixed-predecessor replay,
scratch isolation, atomic commit, public admission and old-route compatibility.
This is development review plus native/same-code oracles, not independent
cross-family scientific acceptance. Optional reviewers remain unavailable.

The example material laws are development fixtures. This slice does not prove a
material roof limit point or descending branch, external agreement, mesh/unit
invariance, line/footprint coupling, physical fibres, curved S3, active-plastic
spectra or displacement control. In particular, the existing compiled retained
variable normalization was preserved rather than silently changing older curved
force checkpoints; physical force/moment scaling needs its own consequential
assessment before a general continuation claim. Independent mechanics, resource
scale, platform and full programme obligations remain open. No publication,
main merge, formal F03 execution or new external campaign occurred.

## Evidence

[Summary and execution identities](summary-v1.json),
[physical route outputs](physical-outputs-v1.json), and
[raw runners, artifacts, manifests, checks and failures](raw-evidence-v1.zip).
Raw archive SHA256:
`aac91e78c78d4bfced44a05b8504d3047d947b3b83a09e1d49248f8d294d0ab9`.
Execution records use an explicit safe metadata whitelist; inherited environment
maps and the protected contaminated historical archive were not copied.
