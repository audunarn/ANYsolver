# Native generalized global force/restart development

Base: 6cab6d24cdd22a028c628e951447b0229daef3dc.
Add a private typed force programme, complete-chain restart and accepted
generalized-resultant recovery. Make only exact-type gated hooks in the shared
nonlinear solver. All existing B2/B3/Q4/S3 and physical-fibre mechanics, routes,
defaults and historical qualification evidence remain unchanged.

The programme binds model, sections, loads, supports and initial chain. It uses
actual nonlinear_static Newton, line search, reactions and accepted snapshots.
Require GENERAL factorization for the distributed spatial-couple Schur tangent.
Keep homogeneous selection supports and existing bounded private model limits
until broader solver/path qualification; these are not the final production
scope. Unsupported direct entry fails before stiffness evaluation. Generic
restart/initial fields/imperfection and unauthenticated raw initial states
cannot bypass the programme.

Generalized restart uses its own schema and externally supplied SHA-256.
Validate exact canonical JSON, keys, finite nonboolean arrays, six normalized
paired plastic coordinates plus paired accumulated evolution per station,
section/cell identities, complete genesis/history, loads, epochs/predecessors,
internal seeds, multiplicative rotations and equilibrated shared DOF states.
Deep capture is allowed only within the authenticated active programme.
Preserve exact supported displacement extraction; do not reconstruct via LSQR.
Limits: 2 MiB, 65 complete snapshots, 60-second validation; no pickle/inference.

Recovery uses accepted internal rotations/resultants and exact accepted origin.
It exposes local/global generalized resultants, strains, positions, frames and
history without advancing state. It must explicitly state that no fibre stresses
are supplied. It does not add numerical or external load resultants to material
recovery. It confers no modal/buckling, dynamic or production authority.

Cases: straight elastic, curved coupled plastic, and connected curved coupled
plastic. Use frozen fixture C/M, Y=1e6 elastic or .025 plastic, H=.6, reference
line (.09,-.03,.02), distributed couple (.07,-.04,.05) per element. Two accepted
load increments, prefix restart to the identical final state, unloading,
failed-step preservation, reference/current recovery work and mutations.
No coefficient, tolerance, state law or geometry tuning.

Run each geometry in its own bounded child. Each suite emits separate inventory;
at most three children, one numerical thread, 24 GiB, 600-second child wall,
120-second CPU-inactivity and 1,800-second wave limit. Smoke before complete
rehearsal; clean freeze before two fresh deterministic cycles. No automatic
retry. Preserve any failed data/source before correction. Historical regression
lanes remain separate. Require byte-identical canonical scientific files.
Independent review PENDING; overall goal, public integration and production
qualification remain incomplete.
