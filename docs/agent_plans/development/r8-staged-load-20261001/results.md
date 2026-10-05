# Staged translation dead loads — experimental integration,1 October2026

Decision: provide genuinely independent force directions through the existing
finite point-owner solve and atomic accepted-state boundary. No element equation,
default, physical tolerance, package version or previous checkpoint identity is
changed. This does not repair historical F06 failures or consume formal F03.

Implemented: immutable model-bound absolute endpoints; continuous piecewise-affine
forces; strictly increasing programme positions with every crossed integer knot;
compile-once endpoint vectors; explicit accepted progress/current force; fixed and
existing adaptive stepping; postcommit detached observation; atomic checkpoint and
chart rebase. A separate programme envelope and augmented inner model identity
bind future stages and forbid admission of a stripped checkpoint as legacy.
Restore validates privately before publishing the one global accepted state.

Source base02ea75f5d16c889c32c94d80078897c0c527f918; exact candidate source/fixture
hashes are in `r8-staged-load-installed-v1/source-manifest.json` and `identity.json`.
The archived `anysolver-0.4.7-py3-none-any.whl` SHA256 is
`0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c`.
Its388 Python modules match source, wheel and installed site byte-for-byte.
211 canonical imports are in that installed site. Python3.14.2/NumPy2.4.6/
SciPy1.17.1/numba0.65.1 dependencies and actual locations are recorded.
One effective BLAS/Numba thread and disabled JIT were verified in the child.

Installed affected checks: **119passed**, no failure/error/skip:56 descriptor/
compiler,8 staged owner,16 observer,23 finite/material,13 increment controller,
3 S3 binary. Checks cover force/progress ownership, future-stage identity,
strict target admission, fixed/adaptive continuation, knot/interior restart,
cancelled/failed initial publication, typed callback errors, changed/tampered/
stripped checkpoints, actual chart reset and continuation. Execution261.07pytest
seconds/265.4123431process seconds; sampled process-tree peak234618880bytes.
The serial600second/8GiB ceiling was not reached. No speedup is claimed.

Separate unchanged legacy control: the prior wheel
`243b2d8a2f1b03a6f08c49624f449e6e282749203b77b37b4be7817cd8758317`
and candidate give identical checkpoint bytes and seven physical array fields.
Raw checkpoints/NPZ/imports/commands are in `r8-staged-load-legacy-parity-v1/`.
Execution5.7146994seconds/186986496bytes; this is compatibility evidence, not a
performance comparison. Full campaign logs, runners, fixtures, manifests and
JUnit inventory are retained unchanged.

Independent complete source/evidence review found no consequential defect:
`r8-staged-load-complete-review.md`, SHA256
`86c79162aae6b522c5243a172a46a38a4b8d08423a4fb00126ca078c5acddbde`.
The independently proposed seam and root-integration-only review are retained too.
Review scope explicitly distinguishes material-aware machinery from the small
elastic staged fixture actually exercised. Earlier failed evidence is unchanged.

Limits: translation dead forces on admitted GE point owners only; no staged
moments, follower/line/footprint programmes or consumer programme persistence.
Zero endpoint representation does not imply finite completion after unloading:
the unchanged zero-load equilibrium check remains strict. No F06 coverage,
staged-yield history, broad G4A or aggregate programme acceptance is established.
Next use the new capability for a prospectively fixed independent-direction
Q4/S3 loaded transport path, preserving0.05rad/1e-5commutator coverage floors.
