# F06 v3: loaded equivalent chart descriptions on Q4 and S3

21 September 2026. **Four/four bounded Q4/S3 straight/curved cases
passed; F06/G0B remain open.** Frozen source/contract commit
`b2fd0af93963a31395b125a865dd30f6bb28cdee`.
Exclusive raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f06-loaded-rebase-v3/`.
SHA-256: `manifest.json`
`05179ac208989066e6fadac3c851893fe6290080a844215c42a3d93f3de36fa1`,
`results.jsonl`
`c696f86068c53cd5edec90c73c6a06227f210f314be56193dd7de0ae6f740c39`.
The one-time runner exited zero with four complete records. The manifest
pins the exact source commit, tracked file hashes and imported source
package; the tracked worktree was clean before execution.

Every case used an actually accepted two-increment coupled state. Shell
rotation norms were about `.0008414` Q4 and `.0025949` S3-V2D;
joint multiplier norms were about `.0005`. Shell conjugate displacement
work was `2.238e-7` Q4 and `7.164e-7` S3 in the fixture's units;
native beam residual norms were about `.000548`. Each case reported
nonzero shell spatial force/tangent, and its original accepted
descriptor and checkpoint stayed byte-identical. Reconstructing the
same poses with nodal shell increments set to zero and physical
rotations moved into chart anchors gave identical point gaps, joint
spatial wrenches/Jacobians, and fixed-support reactions at the recorded
precision. The largest reported normalized discrepancy among all
registered numerical parity metrics was `3.70e-17` (Q4 shell spatial
tangent); the loaded free residual norms remained below `1.52e-13`.

V2's Q4 failure was retained separately. V3 distinguished candidate
path equality from material-state magnitude. Both qualified Q4 cases
had 48 numeric virgin elastic-state values with norm `0`, as expected
from the elastic shortcut, despite nonzero loaded shell force/tangent
and work. Both S3 cases had 227 numeric values with norm about `4.905`
and directly matched nonzero layer strain and stress. No material
history was changed or invented to make the charts agree.

These aggregate norms are **same-unit numerical representation parity**
checks, not dimensionless physical force/moment accuracy. The experiment
does not issue a rebased state, transport a loaded beam/shell history
through a new accepted owner, restore a checkpoint in the new chart,
or exercise large noncommuting rotations. The bounded historical owner
still stores total additive shell rotations. F06 requires an owned
atomic chart-rebase design, physical force/moment/energy and attachment
checks across multiple accepted steps, rejects and restart, and
independent mechanics acceptance. F03 also remains unresolved and
continues to bar G1.

Independent post-run read-only audit matched all eight tracked file
hashes to frozen HEAD, both raw artifact hashes, four ordered pass
records and every registered metric. It independently confirmed the
topology-specific material-state policies, unchanged checkpoints, and
the limited chart-description interpretation. The two S3 checkpoint
hashes also match their preserved v2 records exactly.
