# Independent mechanics review of G0 footprint candidates

Reviewed source: ANYsolver integration commit
`5e1cad638daf672e051be79a64a668d2408a6ca6`.
Reviewer: independent agent, not an implementer. Review received during G0;
no source edits or evidence relabeling by the reviewer. **No G0 acceptance.**

1. **P1 — Pose objectivity proof bypasses its fit.** The common-motion branch
   in `scripts/probe_b3_ge_e4_pl_g0_pose_footprint.py` sets `fit=W@fit`
   rather than refitting transformed shell nodes. It assumes the equivariance
   being tested. Refit in both an independent oracle and the jet path; check
   nonzero-multiplier wrench balance and transport.
2. **P1 — Rigid support rank is incomplete.**
   `scripts/probe_b3_ge_e4_pl_g0_rigid_footprint.py` checks projected rotation
   columns, not the full translation/rotation Jacobian. An offset collinear
   support can make the rotation block rank three while a rotation about the
   line remains invisible after compensating translation. Check full six
   columns, nullspace and conditioning for offset-collinear, coincident and
   curved supports.
3. **P2 — Local work/tangent evidence is narrow.** One reference normal-axis
   moment and one directional Hessian at one deformed state do not verify all
   spatial-wrench chart corrections or assembled multiplier blocks.
4. **P2 — Shell evidence is narrow.** Flat identity-frame, four-corner
   fixtures and in-plane physical stiffness do not establish transverse-shear
   preservation or absence of thickness locking. Curved/pre-rotated
   stress-free references, full director-coupled response, thinning, three
   refinements, Q4/S3 mixtures and support overlap remain required.

The original diagnostic logs and hashes remain unchanged. Corrected probes
are new versioned runs; the reviewer did not approve the candidates or G0B.

The same independent reviewer inspected the versioned v2 scripts and logs.
Both P1 proof defects are corrected **for their bounded fixtures**: the pose
test refits actual transformed positions through the jet and independent
SciPy routes and checks spatial wrench transport; the rank test uses the
complete six-column Jacobian and exposes offset-collinear rank five despite
rotation-block rank three. The reviewer matched the recorded log hashes to
the registration. Remaining limits include one chart/multiplier state, no
coupled director/line evidence, and only one checked null vector in the
coincident rank-three case (the three tiny singular values are reported).
The JSON summaries do not by themselves carry invocation/environment/exit
metadata. Neither P2 finding nor F04/G0 acceptance is closed by this review.
