# Finite Q4 skin/work and actual-path development workflow

## Delivered scope

The explicit `corotational_nodal_director_dev` profile runs original Q4/Q4 monolithic contact through twelve registered common Y rotations (5 degrees each), then force-driven press, strict opening and recontact at 60 degrees. The fixture retains free two-body bending, isotropic elastic Qualified Q4 material, original bilinear surfaces, fine shared nodal Q1 pressure and a 0.2 um initial physical clearance. This is bounded development evidence, not engineering acceptance or release.

Only planar-reference Qualified Q4 models whose every assembled element participates are admitted. Total theta <=1.2 rad, owner-local phi <=0.1 rad and local translation/minimum reference edge <=0.01 are checked before structural trials and at accepted/restart poses. Rotations are either all three free or all three fixed/prescribed per node. The constraint transformation permits zero-offset independent unit selectors only. Finite rotations for S3, warped references, mixed models, general MPCs, partial rotational constraints, nonlinear materials, transient, arc and implicit ordinary-force selection remain outside this profile.

## Geometry and work contract

Physical nodal skins are `x_i=X_i+u_i+h_i*Exp(theta_i)*dref_i`, interpolated by original Q1 faces. Pure numerical drill is right multiplication about the reference director. Additive chart theta_z is not generally pure drill.

Let `Wspin=[I,-h[d]x]`, `V=dx/dq=Wspin*diag(I,J_l)` and `fgeom` be the existing geometric work force. The contact residual uses physical spatial couples: `Rspin=Wspin.T*fgeom`. Its q Jacobian is `Wspin.T*Hx*V` plus the derivative of `h*d cross fgeom`. The force/pressure crossblock uses the spin gap gradient, while complementarity differentiates the additive-coordinate gap. This follows the structural owner's spatial moments and is generally nonsymmetric. It is not the Hessian of an additive-theta potential.

The director uses a bounded Taylor evaluation with first/second variations and an explicit evaluation-error enclosure. Along actual affine q segments, the analytic director curvature remainder is bounded by `abs(h)*||dref||*||delta_theta||^2/8`, plus endpoint/interior arithmetic enclosures. Directed Q4 cubic bounds and all-corner chart guards cover these envelopes; adaptive subdivision acts on the original q path. Every actual shortened candidate is certified before its material trial. A single unsafe 60-degree chord is refused; registered 5-degree segments pass. No sampled-pose/chord-only certificate is claimed.

The common-frame seed transports each free nodal frame by `Qdelta*Qi` and each free midsurface rigidly before projecting prescribed controls. It preserves free deformation, and its complete committed-to-seed path is certified. It adds no physical ties. Translation-only frame changes retain free theta exactly.

## Constitutive records and restart

The outer checkpoint retains global additive q and model/program/settings identities. Qualified Q4 records are sealed and validated at actual corotational owner-local `u_d`, using the exact production reference cache. The interpretation `qualified_q4_corotational_reference_deformational_u_d_v1` is bound and reported. Exact finite-profile preparation validates these records, deep-copies them and strips their seals before trials. Legacy global-u state contracts remain unchanged. No deletion, plastic-origin migration or generic corotational checkpoint bypass is admitted.

## Public use

Use the new example with its explicit path and matching `kinematics='corotational', corotational_tangent='consistent'` options. The installed verification used fresh processes/checkpoints at steps 1,4,8,12,13,14,15; their new snapshot inventories concatenate to 1..15. The final CLI consumed the real terminal checkpoint with `--through-step 15 --restart <checkpoint-15.json>` and produced zero new increments. It proves parser/validation/reporting of terminal restart; it is not a fresh full CLI run.

See OUTCOME.md and IMPACT.md. Exact commands, immutable wheels, per-attempt sources, full stdout/stderr/JUnit/runtime and SHA bindings are under `C:/ANYworkspaceWork/contact_finite_rotation_shell_work_20261008`; CLOSURE.json is the compact index.
