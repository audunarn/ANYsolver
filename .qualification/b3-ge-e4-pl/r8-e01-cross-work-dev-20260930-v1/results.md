# E01 reciprocal work decision — saved fields, no new solve

Question: plate/director transfer or indirect membrane/drilling feedback under
the unchanged six-row point bond? Independent review recommended one saved-field
discriminator after checking geometry, supports, offsets and beam-port parity.
No refinement, matrix replacement or drilling tuning.

For saved shell actions aN,aE and coupled fields sN,sE, common linear beam
compliance and the rigid bond map imply
`aN^T sE - aE^T sN = f^T(qE - qN)`.
Subtract the two beam reciprocal-work equations: shell and beam bond actions
are opposite. Pair all45 shell nodes in their global work-conjugate coordinates;
root fields vanish. Under common +100Nm tip torque, right side is100 times the
tip-roll difference. Existing48 beam-port columns agree5.603e-14.

Total5.022586926971475e-4J; tip-work5.022586926973562e-4J;
relative closure4.15541e-13. Partition:

- membrane/drill(ux,uy,rz):5.135551007697543e-4J,102.2491% signed;
- plate(uz,rx,ry):-1.1296408072606766e-5J,-2.2491% signed.

These are signed cross-work terms, not positive energies, sensitivity derivatives,
F03 norms or allocation to one defective element. Mz-to-isolated-shell-roll=0
does not exclude this indirect coupled feedback. Complete coordinate contributions
and exact runner/input hashes are in `cross-work.json`; runner `cross-work.py`.
Original saved inputs remain immutable in the historical v4 evidence directory.

**Decision:** retain six-row points and thresholds. Saved map/action reciprocity
is consistent. The next engineering comparison must match material-spin/membrane
connection interpretation; do not infer that native shells are wrong or start a
fourth refinement. Different shell drilling models tied to beam yaw can change
coupled torque response. Official [ASDShellQ4 documentation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/ASDShellQ4.html)
describes its membrane-coupled drilling stabilization; this does not qualify
either beam–shell idealization.

BL5 remains a separate director bond with normal spin released, never a silent
point-row deletion. E01/M1/M2/F03 stay open. No new solve, product equation,
criterion, consumed authority or foreign file change. Independent review and
next reference action are recorded in `review.md`. This is a grouped development
decision, not a new helper-level qualification gate.
