# Integrated objective-map candidate: independent source review

2026-10-18. Read-only review of the integrated mechanics and solver callers.
No imports, numerical execution, pytest, product/test writes or workers.
Mistral remains implementation owner. Parent-reported seven mean-focused passes,
two plastic-half passes and the240s coupling timeout are context only; this
review did not execute them or verify their input receipts against these hashes.
There is no full -.20 completion claim.

## Reviewed identity

SHA256 values captured at inspection; repeated product/test hash reads were
unchanged during this pass. Later guard/two-master edits require a delta recheck.

|File|SHA256|
|---|---|
|src/anysolver/corotational.py|1114E97329D80F545B79B52F35739CA6176BB0BCA0926AC12AA4A61368F8E253|
|src/anysolver/nonlinear_static.py|D9968DBCD7CB2812AA684EDC0D730E957823150AFB6AF94CB8E18BA5330710C8|
|src/anysolver/nonlinear_performance.py|D22FD0F3C29E2E25AC22F306F2F70ACB64A30D0ADB856B30667B6BACD1F7624A|
|src/anysolver/elements.py|B3AC0D22E053AA670277C173AA3417F576D161AD132F1CA44C0ADDAA3BE28A08|
|src/anysolver/mesh_gen.py|2D023D1758A4785A3F812A051BD74B942432919F9273AD8C966B7A3D3A2A0485|
|tests/test_nonlinear_beam_shell_coupling.py|ACD63DFF89934D01E0DD7DF66A89FF01468E94D14C5699D0725CC3BCAF27CB66|
|tests/test_nonlinear_beam_shell_slice3.py|AEBF3DC7EF2AC544BEA44F639B7192B87E62A60214FB849AE09492423F78D1CE|
|tests/test_nonlinear_beam_shell_slice3_continuation.py|E34189454108DF374A16FE9D76D2FE872704E02B25D22E3AF2C9575ABAB24302|

## Result

The integrated forward map, its individual-master Jacobian, force adjoint,
complete frozen-imbalance geometric Hessian, inverse and reaction transfer are
algebraically connected correctly on an admitted smooth mean branch. The main
force/DC/restart/postcheck paths actually call those updated methods. No new
core force/tangent sign or material-commit defect was found in this pass.

Acceptance is still blocked by the already identified mean-domain/chart guards
and continuation-test defects listed below. Passing representative objectivity
tests does not close the unsupported-branch cases. Convergence and numerical
derivative accuracy remain measured obligations.

## Integrated mechanics checked

### Forward/inverse and admission

corotational.py:1438–1484 computes the correction from master rotations before
applying any slave changes:

    dtheta = theta_m-theta_lin
    du = (R_m-I-skew(theta_m))*r + cross(dtheta,r)
       = (R_m-I)*r-skew(theta_lin)*r.

Adding this to the old linear embedding gives the intended physical slave
translation sum(w*u_master)+(R_m-I)*r and orientation theta_m. Both orientation
and offset therefore use the same mean. The inverse subtracts both corrections
from supplied slave coordinates instead of overwriting them; incompatible slave
perturbations remain observable by the linear constraint residual after inverse
mapping. Input arrays are copied.

The updated guard at1691–1741 rejects downstream consumers of every rotating
slave translation and every multi-master nonlinear slave rotation. It preserves
direct one-master rotational descendants and upstream shell row ties. Because
corrections are evaluated from uncorrected master values, this refusal is
necessary to justify the claimed order independence. The compiler independently
refuses support/MPC duplicate dependent definitions before map construction;
skipping supports in this guard remains appropriate. Signed weights are refused
only on the new active multi-master route; e=0 descriptors remain inactive.

### Jacobian and force reduction

At1486–1532, M=sum(G_i*P_i) uses each master's linear reduced projection P_i.
The slave translation correction is A*M+skew(r)*P_lin; slave rotation correction
is M-P_lin. These are derivatives of the actual corrections above, including the
nonlinear slave orientation.

At1534–1552 the force shortcut adds to master rotational covectors

    G_i.T*(A.T*f_b+m_b) + w_i*(skew(r).T*f_b-m_b).

The old T.T projection still contributes its weighted linear slave lever and
rotation terms; the second term cancels those old contributions. The remaining
master covector is G_i.T*(A.T*f_b+m_b), exactly the new Jacobian adjoint.
This check includes nonzero slave moments, not only forces.

### Complete geometric contribution

At1554–1621 the frozen-imbalance derivative differentiates all per-master
covectors G_i.T*(A.T*f_b+m_b) with respect to every master's three rotations.
It therefore contains both mean second derivatives and the slave-orientation
second derivative contracted with m_b. The omitted linear correction is constant
in those rotations and has zero Hessian. Projection by P_i.T and P_j and final
symmetrization match the intended scalar second variation.

This is a finite-difference Hessian of an implicitly iterated mean, so its
numerical quality depends on a smooth branch, mean solve accuracy and step
selection. Symmetry of the final array alone is not evidence of a correct
derivative. The current representative FD tests are appropriate, including
nonzero slave rotation covectors, but do not certify unsupported charts or
performance on larger meshes. The240s timeout is not a derivative-pass claim.

### Spatial wrench transfer

At1641–1679 the complete slave imbalance is transferred as w_i*f_b and
G_i.T*(m_b+A.T*f_b), then the slave force/rotation entries are zeroed. For a
rigid-spin-equivariant smooth mean this satisfies the differential spin identity
and preserves the physical deformed-arm spatial wrench. The previous
common-covector transfer is gone. Current mean-focused tests check both finite
map covariance and physical wrench transfer using distinct rotations; their
fixture has disjoint master groups, so its per-entry transferred-wrench sums
are meaningful. This review does not claim the mean is equivariant outside the
supported branch/admission domain.

## Caller integration and material lifecycle checked

- Descriptor construction now stores individual master theta projections.
  No other source/test instantiation bypassing the builder was found.
- DC full_u, initial admission, lambda predictor, Newton, residual line search,
  commit, reaction recovery, final state and snapshots use physical mapped
  coordinates. The augmented matrix declares GENERAL. Both performance-wrapper
  original-solver branches forward rotating_mpc_map and the lambda-recovery flag.
- Force full_displacement maps its affine path. Internal/external reduced forces
  use the new adjoint, follower tangents use J.T*K_ext*J, and the geometric term
  receives full F_int-F_ext. Existing line-search promotion calls use the mapped
  candidate and the updated reductions.
- Auto selects work_conjugate even with follower pressure when a rotating map
  exists; incompatible explicit legacy force laws are refused. The internal
  objective constituent B.T pullback is therefore retained.
- Ordinary supplied initial displacement is inverse-mapped before reduced
  coordinate recovery; fixed-affine force restart retains exact reconstruction
  checking. Preload states are inverse-mapped before projection. DC/force final
  postchecks apply the new inverse before checking the existing affine equations.
- The fully constrained fresh path now maps u0, while already mapped checkpoint/
  force-restart states are not mapped twice. The earlier R3 zero-vector regression
  is corrected statically. Corotational initial fields remain explicitly refused;
  the withdrawn R2 is not reinstated.
- Mean evaluation and corrections use copied arrays and no material history.
  Constitutive trials still receive the actual physical state. Ordinary initial
  inputs are detached; persistent trials are replaced/discarded by existing
  transaction helpers. Residual-only line-search and lambda-recovery evaluations
  are not committed; accepted states/snapshots remain generated after convergence.
  Reaction diagnostics discard their active trial. No material law/tolerance
  change is introduced by the map algebra.
- A prior finite state lying on the old arithmetic-mean manifold can be
  incompatible with the new map. It must be refused accurately rather than
  silently projected or stripped of history bindings. Serialized Q4 checkpoint
  support remains a separately observed pre-existing limitation, not closed here.

## Open findings on this exact version

### I1 — P1: mean domain/absolute-chart findings remain uncorrected

_so3_weighted_mean at1195–1305 still uses the arithmetic-vector initialization,
relative |psi_i|<pi and a determinant threshold. It still returns identical raw
vectors before absolute-chart validation. The concrete ambiguous-mean and
identical->perturbed chart-jump counterexamples in supervisor_globalization_review
M1/M2 therefore remain applicable. Its docstring claims ambiguous/chart-crossing
cases are refused, which these guards do not establish. A unique local convex
domain, consistent absolute chart and objective seed/branch policy are required
before the broad contract is accepted. The near-unit partition shortcut
derivative inconsistency also remains unresolved in this version.

If the owner replaces the two-master iteration with an exact geodesic formula,
recheck the returned G_i, the same local domain/chart conditions, direct and
coincident limits, and the connected finite-difference Hessian. An exact
two-master formula alone does not close ambiguity at antipodal relative rotations.

### I2 — P1/P2: continuation acceptance oracles remain open

On the recorded continuation-test hash:

- Lines502–507 still call inverse/forward ambient round trip a manifold check.
  Use actual inverse-mapped constraint residual/physical map relations.
- Line678 still asks resumed snapshots for -.10, which is the supplied initial
  state rather than a newly accepted resumed increment. The half-prefix already
  checks that split; the resumed loop should use its tail milestones only.
- Lines488–489 still capture shallow/view copies for reconstruction immutability.
  Freeze independent displacement/material copies and check the supplied
  reconstruction copy too.
- The full-state comparator still recurses into nested sequences through a
  mapping-only helper, and compares origin/cache metadata as if it were physical
  material history. Select the required physical fields/schema and compare all
  GP/fiber entries at existing strict tolerances.
- The stopped-resume test still passes caller inputs inline and observes only
  probe/counts, leaving material-parent preservation/last accepted state unchecked.
  Cancellation still observes events rather than complete accepted snapshot
  contents retained across later rejected trials.

Per-snapshot physical wrench assertions have now been restored for BOTH routes,
which is appropriate after the objective map. Every-snapshot achieved-lambda
residual checks are present, but the above oracle defects prevent treating the
expanded test file as complete acceptance evidence yet.

### I3 — P3: class docstring mixes the correction and physical embedding

The class equation near1420 states physical u_b=sum(w*u_s)+(R_m-I)r minus
theta_lin cross r. That subtraction belongs to the correction added to the old
linear slave value, not the final physical embedding. The implementation above
is correct; relabel that equation as a correction or remove the extra term from
the physical relation to avoid misleading future test/reference authors.

## Handoff/limits

Core integrated algebra is suitable for continued owner verification after the
open guards/oracles are repaired. This review supplies no numerical acceptance,
no renewed execution allowance and no qualification/release claim. Preserve all
failed evidence and existing tolerances. Source changes after the recorded hash
require impact-based delta review; do not rerun already valid checks merely to
replace their author or erase a failure.
