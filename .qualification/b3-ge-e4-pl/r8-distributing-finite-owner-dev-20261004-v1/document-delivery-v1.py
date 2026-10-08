"""Update current records; retain the preceding note and historical evidence."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
DOC=REPO/'docs/agent_plans'
GROUP=DOC/'development/r8-distributing-reference-linear-20261004'
ACTIVE=DOC/'B3_GE_E4_PL_ACTIVE_STATE.md'
(GROUP/'active-before-public-finite-owner-20261004.md').open('xb').write(ACTIVE.read_bytes())
installed=json.loads((ROOT/'installed-runtime-v1.json').read_text())
consumer=json.loads((ROOT/'consumer-runtime-v1.json').read_text())
assert installed['exit_code']==consumer['exit_code']==0
SW=installed['wheel_sha256'];FW=consumer['fem_wheel_sha256']
def save(path,text):
    path.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode())
save(ACTIVE,f'''# B3-GE / E4-PL / B2 active state — 4 October 2026

## Current result and next decision

ACTIVE. Complete amended G0–G6/F01–F13/V01–V28/B01–B18 remains binding;
implementation, testing, acceptance and release are separate. The
[goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md)
and [matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) govern.

Delivered: explicit experimental finite distributing record, sparse local saddle
assembly in the existing GE owner, elastic force stepping, cached physical
wrenches, rejection/cancellation and dedicated binary checkpoint/restore.
Flat Cartesian multi-Q4/generalized native B3; retained variables preserved.
Reference-only law/model identities and old checkpoints remain unchanged.
Source191PASS (before final metadata-only descriptor adjustment); final installed
186PASS, consumer43source/43installed and installed public restart example PASS.
Example accepts .25/.5/1, equilibrium8.943e-10, gap1.206e-17,2355byte checkpoint.
Supporting OpenAI review is development input, not different-family acceptance.

Next implementation: one finite ANYfem construction/persistence/solve/recovery/
checkpoint-resume slice, using this explicit new record and existing consumer
services. Preserve historical reference-linear project format; no silent upgrade.
Current ANYfem change only fixes empty-field compatibility and rejects finite
records from unsupported reference/modal import routes; no finite consumer yet.
Do not broaden controllers/materials or add a framework while finishing this exit.

Science question: what independent native mesh-adequacy/model-assumption check
would change the physical torque claim? Existing three-level matched reference
Mx differences4.249→2.233→0.813%, Fy3.472→1.290→0.364%; native final torque movement
1.518%, fixed two-layer solid thickness. Not converged1% acceptance. No automatic
paired refinement; old geometry donor only10x4/20x8/40x16 and80x32solid exceeds
4096element map guard. Do not bypass guards or substitute a line/weld law.

## Ownership, restart and authority

ANYsolver: C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001,
branch codex/stiffened-main-reconcile-20261001. Preceding HEAD9269719e; current
finite owner product/example/tests plus linked docs/evidence are root-owned.
Exact staged candidate bytes will be recorded before scoped local delivery.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
branch codex/experimental-ge-panel-consumer; preceding HEAD6013db0. Three narrow
compatibility source/test changes are root-owned. No unrelated dirty work touched.
All numerical jobs terminal; no worker has Edit authority. Root controls serial
jobs, integration and Git. At most3workers, one implementation exit plus one
scientific question. No push/main merge/publication/contact-worker messages.
Optional local/Mistral unavailable; do not re-probe. Different-family review open.

FormalF03 UNCONSUMED: never execute/copy/substitute
scripts/b3_e4_f03_c1_fy_supported_reference.py, SHA
c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481.
Never inspect/copy/archive us3-modal-canary (credentials); no Get-CimInstance.
100krows/600s/8GiB/8threads/ONE numerical job; tighter guards and G5 budgets stay.
Current numerical checks600s/2GiB, effective pools1/JIT off. No authority renewed.

## Evidence and acceptance boundaries

[Grouped evidence](development/r8-distributing-reference-linear-20261004/results.md)
and raw .qualification/b3-ge-e4-pl/r8-distributing-finite-owner-dev-20261004-v1
bind source191, final installed186, consumer43/43, example, exact actual imports,
commands/resource settings and prior source snapshots. Solver wheel{SW};
ANYfem wheel{FW}. Wheels/sites disposable; hashes and logs retained.
No passed campaign is repeated without changed inputs or an unresolved finding.

Finite law is a reduced area-mean/director/polar pose, not a pointwise welded
surface. Relative Log/rank/director/chart numerical domains are explicit.
Local pad curvature can be quadratic; preflight reports its upper bound, not a
measured G5 result. Initial scope excludes reference-linear solve, chart rebase,
adaptive/displacement/arc, external/staged wrappers, yielding and spectra.
These remain mandatory later obligations, not a permanent scope reduction.

Historical source/artifacts/failures stay intact, including private posev1/v2,
owner-localv1/v2/v3, CalculiX executions and all closed certificate outcomes.
BL5 auxiliary21 cases do not settle actual indefinite physical stability;
inverse/positive-part campaigns CLOSED_UNRESOLVED, inventory13positive/
oneunresolved/sevenunassessed. Pressure amendment DECLINED. No retry by guard,
budget/order/precision/mesh substitution. F5 still lacks verified discontinuous
retained sided forces. Scoped foundation passes are not aggregate G0 acceptance.
Full F04/G0/G2, line envelope, materials/topology/loads/spectra/capacity, complete
GE/B2 scale/platform/consumer/external/different-family/release remain open.
No overall development-speed gain or release readiness is claimed.
''')
plan=DOC/'B3_GE_E4_PL_REVISION_8_PLAN.md'
s=plan.read_text(encoding='utf-8')
old='''  The matched reference check and supporting finite-map review now permit
  experimental owner integration of the private projected-director/thin-polar
  candidate (22 focused source controls plus10 actual-owner saddle/recovery
  controls). This is not physical qualification.
  Reuse the existing owner; prove actual chart/spatial work, sparse curvature,
  reactions and atomic restart before public experimental finite admission.
  Give the candidate an explicit finite law/model/checkpoint identity and
  preserve the current reference-only identity and unused-option contracts.'''
new='''  Experimental projected-director/thin-polar integration is now delivered:
  explicit finite record/law/checkpoint kind, sparse saddle, cached physical
  recovery, force stepping and atomic restart.191 source controls bind the
  pre-metadata-adjustment source;186 final installed controls,43 source/43
  installed consumer compatibility checks and public restart example pass.
  Reference-only identities/checkpoints remain unchanged. No physical or
  aggregate qualification follows. Next finish the distinct finite ANYfem
  construction/persistence/recovery/checkpoint-resume exit in existing services;
  current consumer changes only preserve empty-field compatibility and reject
  unsupported finite import. Keep later material/controller/spectral obligations
  visible and avoid optional feature breadth until that exit works.'''
assert old in s;s=s.replace(old,new)
s=s.replace('Reviewed preceding solver HEAD `adc98d4b`','Reviewed preceding solver HEAD `9269719e`')
s=s.replace('Finite pose, fully converged physical fidelity and full F04 remain open.','Finite pose/owner/restart now have installed experimental evidence; finite consumer, fully converged physical fidelity and full F04 remain open.')
save(plan,s)
goal=DOC/'B3_GE_E4_PL_REVISION_8_GOAL.md'
s=goal.read_text(encoding='utf-8')
needle='The near-term path is now:\n'
assert needle in s
s=s.replace(needle,'''Current implementation exit: the explicit finite distributing owner now has
installed solve/recovery/restart evidence; next finish its distinct ANYfem
consumer/persistence route without changing the old reference format. Physical
torque convergence and aggregate acceptance remain open. See the active note for
exact source/artifact applicability, limitations and preserved authorities.

The near-term path is now:
''')
save(goal,s)
matrix=DOC/'B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
note='''
F04 public finite distributing owner, 4 October — IMPLEMENTED_NOT_QUALIFIED.
Explicit GEFiniteDistributingFootprint record, separate finite law/model/binary
checkpoint kind, existing sparse owner/driver, cached exerted current wrenches,
monotone translation-force stepping and atomic restore/continue are implemented.
Flat elastic Cartesian Q4/generalized native B3 only; disjoint points supported.
191source (before final metadata-only descriptor delta),186final installed,
43source/43installed consumer compatibility and installed restart example PASS.
Consumer preserves empty-field legacy compatibility and rejects finite records
from unsupported routes; finite consumer is the next missing exit. Local pad
curvature upper bound is explicit, not practical-scale acceptance. Reference-only
identities/checkpoints unchanged. Full physical/material/controller/spectral/
topology/scale/platform/consumer/different-family and aggregateF04/G0/G2 remain
OPEN; formalF03 UNCONSUMED. [Exact slice/evidence/limits](development/r8-distributing-reference-linear-20261004/results.md).
'''
save(matrix,matrix.read_text(encoding='utf-8').rstrip()+'\n\n'+note.lstrip())
report=f'''
### Public experimental finite owner — complete installed development slice

Explicit `GEFiniteDistributingFootprint` selects
`GE_FLAT_Q4_DISTRIBUTING_DIRECTOR_PLANAR_POLAR_POSE_V1_CANDIDATE`; old reference
records remain reference-only and cannot be mixed. The compiled reference map
and finite pose are prepared once and reused by the existing GE driver. Actual
spatial rows, shell chart columns and multiplier curvature assemble sparse local
blocks; native retained coordinates remain global. No new state owner/framework.

The reduced mean/director/polar pose is not a pointwise weld. Initial admission:
flat elastic Cartesian Q4, native generalized B3, disjoint points permitted,
monotone nodal translation-force stepping. Reference-linear solve, chart rebase,
adaptive/displacement/arc, staged/external wrappers, yielding and spectra reject
explicitly. These required later combinations are still open, not deleted.

Evaluated current physical nodal actions/resultant wrenches are cached before
atomic publication; no raw Log multiplier is displayed as a physical moment.
Dedicated binary kind `finite_distributing` binds the law/model and rejects old,
wrapper/chart/corrupt/wrong-model payloads. Normal restore does not replay history.
Candidate domain failure discards trials; programming/ownership/memory failures
propagate. Tests exercise cancellation after commit, rejected candidates, disjoint
point/pad rows and both recoveries, stale generations and continuation parity.
Local curvature can grow quadratically with pad support; preflight reports the
sum of [6(N+1)]² upper bounds, not measured memory or G5 qualification.

| Route | Result | Pytest / whole seconds | Sampled process-tree peak bytes |
|---|---|---|---:|
| Source-v2 |191PASS|90.55 /92.5090|204128256|
| Final installed-v1 |186PASS|26.63 /28.5363|206303232|
| Consumer source-v1 |43PASS|4.88 /6.9841|190767104|
| Consumer installed-v1 |43PASS|4.80 /6.9287|189820928|
| Installed public example |PASS|not timed as optimization /4.0292|166809600|

Final source differs from source-v2 only in adapter descriptor admission metadata;
do not attribute source191 to that final adapter hash. Installed186 binds all12
actual final solver imports byte-for-byte; consumer16 imports additionally bind
four amended consumer modules. All completed tests have empty stderr, effective
numerical pools1/JIT disabled,600s/2GiB supervision. Build/install logs are also
retained; build tool subprocess counts are not claimed as numerical qualification.
The source-v1 55PASS and original tested bytes remain preserved. No timing gain
or complete-platform claim follows from these development checks.

Solver wheel `{SW}`; ANYfem wheel `{FW}`. Raw directory
`.qualification/b3-ge-e4-pl/r8-distributing-finite-owner-dev-20261004-v1` holds
commands, runtime/source/test/import identities, exact dependency versions,
resource outcomes, retained source-v1, and supporting review. Installed sites and
wheel files are disposable; hashes/size/build logs retain their identity.

Public example reaches factors .25/.5/1 after a2355byte prefix checkpoint,
equilibrium ratio8.942681437660687e-10 and gap1.2059448850772913e-17; restored
and uninterrupted final displacements agree at its registered test tolerances.
This is experimental lifecycle/equilibrium evidence, not finite physical accuracy.

ANYfem changes are narrowly compatibility/fail-closed: a known empty finite field
is permitted in old reference export; nonempty or malformed fields are rejected
by reference/modal import instead of being silently omitted. The old experimental
project format remains. A finite consumer workflow is not yet implemented.
Supporting OpenAI review found no current slice blocker; different-family
scientific acceptance is still unmet. Full F04/G0/G2 and remaining programme
requirements stay open; formalF03 remains UNCONSUMED. No main merge/publication.

Next: the explicit finite ANYfem construction/persistence/solve/recovery/checkpoint
exit using existing consumer services. Independently retain the physical torque
convergence question; no automatic external/finer-mesh campaign is launched.
'''
save(GROUP/'results.md',(GROUP/'results.md').read_text(encoding='utf-8').rstrip()+'\n\n'+report.lstrip())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
save(fem/'docs/development/r8-ge-finite-distributing-compatibility-20261004.md',f'''# Finite-field compatibility — 4 October 2026

Development status: IMPLEMENTED_NOT_QUALIFIED. No finite consumer workflow added.
The reference export recognizes the new solver field only when defined by the
actual API and exactly empty; modal/reference import rejects malformed/nonempty
finite records instead of losing attachment semantics. Unknown fields remain
fail-closed. Historical experimental Project formats/defaults are unchanged.

43source and43installed checks pass with solverwheel{SW}, consumerwheel{FW}.
Raw evidence and actual16module import hashes are retained in ANYsolver canonical
worktree .qualification/b3-ge-e4-pl/r8-distributing-finite-owner-dev-20261004-v1.
See its grouped report docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md.
Numerical pools1/JIT disabled;600s/2GiB supervised. Supporting Read review closed
both compatibility/silent-discard findings; not scientific/platform acceptance.
Next finite construction/persistence route must select a distinct format/law,
never silently upgrade old reference projects. No publication or main merge.
''')
attrs=REPO/'.gitattributes'
extra='''
# Final tested finite owner and raw development evidence retain exact bytes.
src/anysolver/_stiffened_shell_ge_checkpoint_binary.py -text
tests/test_stiffened_shell_ge_distributing_finite_public.py -text
examples/stiffened_shell_ge_distributing_finite.py -text
docs/agent_plans/development/r8-distributing-reference-linear-20261004/active-before-public-finite-owner-20261004.md -text
.qualification/b3-ge-e4-pl/r8-distributing-finite-owner-dev-20261004-v1/** -text -whitespace
'''
save(attrs,attrs.read_text().rstrip()+'\n'+extra)
attrs=fem/'.gitattributes'
save(attrs,attrs.read_text().rstrip()+'\n\ndocs/development/r8-ge-finite-distributing-compatibility-20261004.md -text\n')
print('Updated active note, plan, goal, matrix, grouped evidence and narrow consumer delivery note; history retained.')
