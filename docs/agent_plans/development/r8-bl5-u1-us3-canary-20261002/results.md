# Executed U1/US3 reference-route feasibility — 2 October 2026

One small all-user CalculiX 2.23 model executed successfully. This resolves the
preprocessing/output uncertainty for an algebraic director-shell/beam route;
it does not qualify a BL5 connection, multiplier policy or physical torque model.

## Model and observation

One US3 triangle spans `(0,0,0)`, `(1,0,0)`, `(0,.2,0)`, thickness `.035 m`;
two U1 beams span x=0–1 at z=.0675 m. E=210 GPa, nu=.3; the declared generalized
beam section retains A=.01, equal I=8.333333e-6, kappa=.8 and U1's polar J=2I.
This is not a resolved square or an outer-surface-matched annular section.

The shell nodes at x=0 are clamped. Beam root DOFs1–5 are fixed; yaw stays free.
Five exact affine equations integrate explicitly declared nodal P1 traces:
beam weights `(.25,.5,.25)`, shell-edge weights `(.5,.5)`, lower beam arm−.05 m
and upper shell arm+.0175 m. Three translation and two director channels are
constrained; no normal-spin row or node merge is added. This port differs from
U1's consistent interior interpolation and native B3 retained half-cell traces.

The exact supported pivot determinant is−1/128. Linearized common rigid fields
annihilate the rows; detached beam-root rigid yaw produces mean lateral gap .5α.
Those algebraic identities do not establish the complete structural kernel or
interface stability.

Under tip Mx=1 Nm:

- One static increment completed, exit0, `Job finished`, empty stderr and no
  warnings/errors/fatals.
- Six displacement/rotation components are printed for all six physical nodes.
- The solver reports **14 solved equations**, consistent with 36 coordinates,
  17 supports and five MPCs. Larger printed node/MPC counts are allocation bounds.
- Tip rotation and applied work are **2.315852e-7 rad/J**.
- Beam yaw is nonzero and constant **−6.987515e-9 rad**, with corresponding
  beam y-translations; no hidden sixth root support is indicated.
- All five gaps fall inside their printed-value rounding intervals. Maximum
  gap/floor ratio≈.495; this is not a pass against programme gap tolerances.
- All reported numerical CPU counts, including Spooles, are **1**.

The process finished in .0472 seconds. The 20 ms sampling loop did not obtain
meaningful memory/thread samples; historical recorded zeros mean **unobserved**,
not a measured peak. The requested supervisor bounds were 180 seconds and 1 GiB.
No memory-qualified or timing-improvement claim follows.

## Source, review and limitations

Pinned executable SHA:
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
The archived [2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), pp130–135, documents
U1 and six-DOF US3. Archived 2.23 `usersections.f` and `e_c3d_us3.f` establish
the required `*USER SECTION,...,CONSTANTS=1` thickness property. Ordinary
`*SHELL SECTION` alone is insufficient for this US3 kernel. No prior U1/CPS
failure or formal F03 authority was replayed.

Independent Read reviewer `/root/e02_rigid_tip_runner` checked the equations,
deck, exact supports, source and actual outputs. No blocker remains for this
narrow feasibility claim. It identified the original missing warning guard;
actual saved logs contain no warning. The delivered script rejects warnings and
uses nullable resource observations. Pure replay of the saved deck/log/parser
checks passes; no numerical rerun occurred. An initial replay comparison confused
integer dictionary keys with JSON string keys; the normalization repair is
recorded separately and changes no numerical data.

Executed runner SHA:
`2a042d126651631bf01e836cd3e6ac3a5a3dc1ac11d7d532b47ee0ce67190233`.
Delivered runner SHA:
`a3f20ab32dd6a1cf798dc2b403425c4a32abd33b7942694692e47fc8e97c0342`.
The exact executed runner is retained; delivered changes are warning/resource
reporting guards, with identical generated deck and parser results on saved data.

Raw deck, all solver outputs, original runner, execution/input/result records,
review replay and source hashes: [archive](raw-v1.zip), [inventory](raw-v1.json).
Execution root: `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-u1-us3-canary-v1`.

**Resulting action:** this route is available for a declared beam/director-shell
engineering reference. Next establish compatible section/attachment idealization,
common virtual work and usable physical output before any accuracy comparison.
Do not infer root-wrench balance from RF, native half-cell equivalence, U1 interior
trace equivalence or multiplier selection. Existing F5/solid/E02 evidence retains
its original scope; F03/G0B/M2 and complete external obligations remain open.
