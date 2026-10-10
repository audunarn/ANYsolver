# General contact seed gap — Mistral work note 2026-10-10

Scope `D1_SEED_GAP_DISCRIMINATOR_DEV420_V1`, direct chat coordination, no worker.
This is the only Mistral-owned repository note; guard/ledger/evidence and
reviewer/lead documents are untouched.

## Input binding

- Literal record: `C:/ANYworkspaceWork/contact_mistral_seed_gap_delivery_20261010/LITERAL_PATH_ZERO_INPUT.json`
  (sha256 `f8e7dee46a3135c621492364f5f727d0eb34d57873afeb7146606c4bda31a114`),
  first `path_witnesses[0]` capture only: Q4 source start/end corners, S3 target
  start/end corners, four per-component endpoint error boxes, gap tolerance
  5e-05 m, production diagnostics `found=false, samples_checked=27`.
- Interpretation: literal first recorded path only. No full-solve acceptance
  and no inferred relationship to later bisection records or the other
  captured poses.

## Independent reference equation (derived from the literal Q4/S3 geometry)

Path parameter `t in [0,1]`, source skin parameters `(u,v) in [0,1]^2`,
affine physical-skin interpolation of nodal positions along the path:

- `A_k(t) = (1-t) a0[k] + t a1[k]` (Q4 corners), `c_j(t) = (1-t) b0[j] + t b1[j]` (S3 corners)
- `s(t,u,v) = sum_k w_k(u,v) A_k(t)` (bilinear Q4 skin)
- `T = (c1-c0) x (c2-c0)` (target normal), `P = (A1-A0) x (A3-A0)` (parent corner-0 source normal)
- `N = (s-c0) . T` (target-plane height), `r = N/(P.T)` (foot radius along P)
- `y = s - r P` (projected foot, lies on the target plane)
- `Ns = dX/du x dX/dv` with `dX/du = (1-v)(A1-A0) + v(A2-A3)`,
  `dX/dv = (1-u)(A3-A0) + u(A2-A1)` (actual parametric Q4 normal)
- physical source-normal gap `g = r (P.Ns)/|Ns| = (s-y).Ns/|Ns|`
- projected-overlap constraint: foot barycentrics
  `lambda1 = ((y-c0) x e2).T/|T|^2 >= 0`, `lambda2 = (e1 x (y-c0)).T/|T|^2 >= 0`,
  `lambda1+lambda2 <= 1`.

Endpoint error boxes: every saved corner is enclosed by
`[saved - error, saved + error]`, blended affinely along the path; all
arithmetic propagates the enclosures. Decision semantics: a violating point
requires `g < -gap_tolerance` with the foot inside the S3 triangle; a safety
certificate requires `min g >= -gap_tolerance` over the whole path domain
(the foot-inside subset is covered by the whole-domain certificate).

Method: exact rational interval arithmetic (`fractions.Fraction`; binary64
inputs are exact dyadic rationals, subdivision at dyadic points, exact
integer sqrt enclosures) in a branch-and-bound over `[0,1]^3`, plus an
independently written directed-floating-point interval arithmetic
(`math.nextafter`) cross-check, plus exact rational point witnesses.
No production gap/witness kernel is called for any oracle value.

## Preliminary analysis (to be certified by the guarded run)

- At the path end the source corner A2 dips about 15.7 um below the target
  plane: height `(s-c0).T/|T|` at `(t,u,v)=(1,1,1)` is approximately
  `-1.567e-05 m`; the gap `g` differs from the plane height only by the
  cos-factor `cos(P,Ns)/cos(P,T)` of order `1e-8` relative.
- A2's projected foot lies about `2.8e-6` (lambda-sum) beyond the target
  hypotenuse `x+y=1.2` at every `t`, so the represented overlap excludes a
  thin sliver at A2 and the feasible minimum sits on the sliver boundary,
  within about `5e-10 m` of the unconstrained value.
- Expected certified outcome: whole-domain exact enclosure of `g` has a lower
  bound around `-3.9e-05 m` (root-box natural extension), i.e. the true
  minimum gap of this pair path is certified `>= -5e-05` tolerance: the path
  is safe within tolerance and any production refusal on this pair is
  conservative certificate uncertainty, not physical penetration.

## Concrete edit (in progress)

- `scripts/general_contact_seed_gap_reference.py` (new): self-contained
  stdlib-only independent reference (exact rational + directed-float
  enclosures, locator, machine-readable result).
- `tests/test_general_contact_seed_gap_reference.py` (new): independent
  checks — artifact binding, exact-vs-float containment properties,
  two-formula consistency (gap vs plane height vs local-normal gap),
  literal-path certificate, synthetic violation detection, synthetic
  separation certification.
- After the discriminator works: `tests/test_general_contact_seed_gap_stage_diagnosis.py`
  (production chain stage diagnosis on the literal arrays, 60 s guard), then
  only an evidenced compatible repair in
  `src/anysolver/general_contact/q4_overlap_local_bound.py` /
  `s3_patch_static.py`, checked through
  `tests/test_general_contact_seed_gap_coupled_prefix.py` (180 s allowance
  only after the repair changes the blocker).

## Remaining uncertainty

- Which production stage (whole-pair swept bound, matching-projection
  degree7/node1024, overlap-local fallback, or the endpoint chain) refuses
  this pair path, and whether other captured pairs drive the 0.25 admissible
  fraction — deliberately not chased per instruction.
- Exact certified bounds pending the guarded run; the note will be updated
  with the machine-readable result.

## Artifact-based integrating-lead handoff — supersedes preliminary prose

Authors V2/V3/V4 reached their turn limits without completing this note; useful
code and checks were inspected rather than discarded or re-run for accounting.
V1 was intentionally interrupted after27 inspections and no code/checkpoint.
No GPT-Astra agent was involved. Mistral authored the connected reference,
interval correlation repair and floating-point interval-type repair. This chat
ran attempt07 and inspected the final Mistral attempt08 receipts.

Actual final attempt08 `mistral-reference-v8`:6/6 PASS,0failed/errors/skips,
7.0370637s process-wall,180.348MiB peak, unchanged bound helper inputs. Earlier
seven NONPASS runs remain retained. Total guarded scope65.3267043s; maximum8
attempts consumed and scope CLOSED;354.6732957s unused CLOSED, never pooled.
No production contact/caller source changed; no physical solve/build/install.

Exact rational certificate for literal path_witnesses[0] alone:1visited box,
gap lower−3.907253498997946e−5m; no unresolved/remaining boxes. Directed float
mirror lower−3.90725349900181e−5m. The reference reports minimum interval
[−3.907253498997946e−5,−1.5667589596364828e−5]m. The current proof uses
multilinear vertex enclosures, not the earlier inconclusive natural extension.
This supports within50um for that one literal pair under the documented affine
skin/error-box contract. It neither locates the overall controlling face nor
certifies all captured paths/full seed. Production still refusesfraction0.25.
Separate Mistral Read source assessment is active, session46027; not engineering
acceptance. Candidate hashes and exact result/receipt paths:
../contact_mistral_seed_gap_delivery_20261010/REFERENCE_CANDIDATE_BINDING_V4.json.

Provenance clarification: original capture SHA f8e7dee46a3135c621492364f5f727d0eb34d57873afeb7146606c4bda31a114;
derived LITERAL_PATH_ZERO_INPUT.json SHA238a19cc6ac72445d97de8a44e3f44b75eb606bb42fb548ba18bfe7866952ec7.
The preliminary note conflated them; the verified loader distinguishes them.
Changes: scripts/general_contact_seed_gap_reference.py,
tests/test_general_contact_seed_gap_reference.py, this note. A disposable raw
scratchpad was also generated outside the repository; protected evidence was not
overwritten. Preserve it as an ownership exception, not source or accepted data.

Next: assess the independent reviewer findings, then apply the same independent
reference to the remaining exact captured paths and identify the actual refusing
production stage. Deliver the compatible certificate/globalization repair only
from the demonstrated result. All physical inputs, gaps, degree7/node1024 limits,
full300 fixture, D1 breadth and C0–C9 remain unchanged and required. No whole-route
speed improvement or engineering acceptance/release is claimed.

### Separate source assessment completed

Mistral Read46027 returned a final report, source hashes unchanged. It supports
the single-path enclosure and found no defect in core interval/vertex mathematics.
This chat checked its consequential model questions against production: gap
formula and inclusive-foot constraints agree; reference_linear maps are affine,
and endpoint errors include fixed-map reconstruction arithmetic. No new physical
choice was adopted. Nearest-rounded serialized values and missing wider refusal
coverage remain limitations to address in the next connected runner/caller slice.
All owned handles terminal; no execution balance active. Review and disposition:
../contact_mistral_seed_gap_delivery_20261010/REFERENCE_REVIEW_DISPOSITION_V1.md.

## Prospective connected production delivery

Previous goal turn progressed: new independent reference,6/6 measured source
checks, separate Mistral assessment and local checkpoints df5a6c98/198f8286.
Current question remains the controlling overall seed refusal, not the now-proven
first face. Mistral Edit21450 owns the remaining literal-record/stage discriminator
through compatible actual-caller repair and checks; no GPT-Astra agent.
Fresh D1_SEED_PATH_ADMISSION_DELIVERY_DEV600_V1:600s/90reserve/max12 attempts/
953MiB/serial,focused60s,named changed2x2 prefix180s; old balances CLOSED.
Brief: ../contact_mistral_seed_path_delivery_20261010/IMPLEMENTATION_BRIEF_V1.md.
Next current worker note: GENERAL_CONTACT_SEED_PATH_MISTRAL_WORK_20261010.md.
The prior exact reference is preserved in reference-v4-frozen-source externally
before extension; no frozen run replay. This chat prospectively adopts an equivalent
outward vertex-interval sufficient proof behind existing default-False overlap-dual
development flag, if supported by the independent discriminator. Any integrated
proof binds opt-in revision constant_nonnegative_joint_bernstein_plus_vertex_interval_v3;
defaults/identities/physics/gap/degree7/node1024 unchanged. A true violation selects
compatible feasibility handling, not unsafe certificate admission. Wider export
and refusal coverage belong in this connected slice, not a helper-only branch.
