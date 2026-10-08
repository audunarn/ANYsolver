# Stress-free curved point references — development slice, 2 October 2026

The public facade now constructs a new virgin elastic Q4/native-GE point
definition from typed sparse reference perturbations. It transports physical
offsets once, propagates canonical shared beam poses, preserves section/inertia/
integration/arithmetic contracts, and admits the new geometry through existing
compilation. It takes no accepted state. Loaded source checkpoints are unchanged;
new model identities reject those checkpoints. Full G4C remains open.

Source parent: `958559b7`; exact candidate modules and fixtures are recorded in
the archive's artifact manifest. Local delivery commit is available in Git.
Solver wheel SHA256:
`7cb1eedb95e9c66ec5f44b311c0339c993536139beb64a516831cc96615f7eb2`.
All 413 solver modules matched source, wheel and installed bytes. Unchanged
ANYfem wheel `e1bd72d76d6c13873b47194ecabe0210bef3f2d252abac3644898e9455c9ef94`
and all 98 consumer modules were rechecked against source/installation.

## Verification and delivered workflow

- 17 focused installed checks passed: typed/owned inputs, zero-change identity,
  common motion, local host disagreement, canonical shared nodes, late
  cancellation cleanup, native policy/tolerance preservation, geometry negatives,
  both roof imperfection signs, loaded-state isolation, restore/continuation,
  tilted-facet mechanics and unchanged legacy point-panel control.
- The actual 4x4 E04 roof with +0.1 mm crown amplitude passed standalone/native
  ANYfem save/reopen, finite seed, two arc steps with fresh restore, exact final
  checkpoint and resultants. Initial scaled reference residual is zero. Final
  force is 12.139861 N, crown incremental translation -0.027314964 mm,
  equilibrium 3.13149e-12, compatibility 1.41336e-17.
- The existing CLI with -0.1 mm amplitude passed linear/finite seed, two arc
  steps, restore after the first step, identical per-step/final checkpoints and
  final history/resultants. Final force is 12.172946 N and crown incremental
  translation -0.026957768 mm. These are two small development paths, not
  imperfection sensitivity or converged capacity results.

Supervised full-process costs (one numerical thread, JIT off; observed runtime
settings recorded): installed checks 37.87 s / 195776512 sampled tree bytes;
ANYfem route 17.00 s / 174088192 bytes; CLI 18.66 s / 168054784 bytes. Each stayed
inside 600 s / 1 GiB. No speedup or scale claim follows from these measurements.

## Review and retained failures

Independent OpenAI read review clarified shell-port rotation/rebasing, beam
tangent admission, facet planarity, support relocation and single eccentricity.
Implementation review found malformed-shell admission and model-wide scaling
of host agreement. Both were fixed and tested. Host agreement now scales only
the participating local operands. Final implementation/example review had no
actionable finding. Reviewer ran no numerical checks and did not implement this
slice. This is development review, not cross-family scientific acceptance.

All source attempts v1–v10 are retained. Failures were an incorrect constant
import, a read-only SciPy assertion, two inadmissible distant-geometry test
fixtures, and a test that tried to weaken native reference tolerances. The
corrected assertions retain read-only arrays; the scale regression isolates
unrelated metadata; policy tests use tighter admitted tolerances. No product
guard or scientific tolerance was weakened. Failed runs remain failures.

## Evidence and remaining boundaries

[Summary and exact hashes](summary.json), [raw runs and fixtures](runs-v1.zip).
Archive SHA256:
`c70a4b00a8f44617ace6b6c27b0befd9ab9d0b33b290c949f0e728930b0b9528`.
Execution metadata is whitelisted; full environment mappings are excluded.
Prepared artifacts remain in `%TEMP%/r8-stress-free-reference-installed-v1`.

The shell rotation field transports ports; Q4 reference directors still come
from geometry. Supports move with the new reference fixture. The CLI uses the
declared fixed nominal area/length continuation metric. General warped meshes,
S3/material/line/footprint imperfection operations, spectral mode imperfections,
physical imperfection sensitivity, converged capacity and mandatory external
comparison remain unfinished. Formal F03 remains unconsumed. No aggregate
gate, release, main merge or publication is implied.
