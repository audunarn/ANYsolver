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
# Beam-trace discrimination, 2 October continuation

The saved canary remains a nodal-P1 feasibility model. Its beam-side port is
**not equivalent** to the interior U1 interpolation, even on the supported
coordinate space. This finding does not attribute the native transfer discrepancy.

Executed bounded command (no CalculiX solve):
`C:/Python/Python314/python.exe scripts/check_u1_canary_trace_work.py`, with
OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1. Exit0, about0.5s including Python startup.
The script verifies the pinned archive hash, integrates the corrected derivative
polynomials in `resultsmech_u1.f:443-468` from the left endpoint and checks endpoint
values and rigid translation/rotation fields. Integrating bending and shear energy
reproduces `e_c3d_u1.f:479-529` to relative1.4948928420860556e-16 for the actual
half-metre, isotropic canary section. This is a local source-backed derivation;
the routines themselves evaluate the derivative polynomials at endpoints.

For one bending plane, a=12EI/(kGA L^2), b=1/(1-a). The derived element means are
`mean(v)=(v1+v2)/2+L*(theta1-theta2)/12` and
`mean(theta)=b*(v2-v1)/L-a*b*(theta1+theta2)/2`.
They differ from the nodal-P1 means. Opposite-sign transverse rotation in the
second plane follows the source's `w'+psi` shear convention. Torsion/axial traces
remain linear. The script assembles all18 beam-coordinate columns across the two
elements, including the -.05m beam-surface arm. Maximum absolute coefficient
changes by port row (ux,uy,uz,rx,ry) are
`[.05747126436781609,.020833333333333343,.020833333333333343,0,1.1494252873563218]`.
Removing the actual root DOFs1–5 leaves nonzero changes of the same magnitudes
(roundoff aside). These are dimensioned matrix entries, not normalized accuracy
or stability measures. Independent OpenAI Read review found a stronger witness:
with shell coordinates and beam rotations zero, beam Z translations `(0,-epsilon/2,
epsilon)` satisfy every old nodal-P1 row and the root supports. The reconstructed
mean Y rotation is `-1.149425287356322*epsilon`. Hence this is a different supported
constraint space, not just a row rescaling. The executable now checks this witness
and binds the canary deck hash. The strengthened check passes; raw scalar output
is `beam-trace-work-v1.json`. Review found no blocking algebra error. This is not
different-family qualification. No exposed interior-output API or uniqueness of
all possible reconstructions is established by the polynomial extension.

Decision: retain all old execution evidence under its original nodal-P1 meaning.
Do not score a native interior-trace law against it as an equivalent connection.
Next complete the US3 shell-side trace/work contract, then prepare a separately
identified consistent-interpolation reference if it discriminates the physical
question. No external rerun, native-law revision, multiplier selection or formal
F03 authority was consumed. Energy identity does not establish physical adequacy
of this U1 formulation, and no native B3 half-cell equivalence is claimed.

## Full trace contract and physical-reference disposition

Continuation after0888da71: the pinned US3 source uses P1 translation and two
physical director rotations in us3_sub.f:1396–1423, and their P1 bending gradients
at739–777. This supports a **declared** reference-linear physical trace; CS-DSG
shear and ANDES membrane remain separate assumed-strain maps. It does not establish
one unique displacement reconstruction whose gradients reproduce every strain.
Normal-spin attachment columns are zero, but indirect ANDES/drilling influence
on coupled response remains possible. Five integrated rows are not pointwise ties.

The extended algebraic script checks all six common rigid motions and all five
unit multiplier resultant wrenches with actual shell+.0175m/beam-.05m arms.
Maximum errors are5.551115123125783e-17. A transverse slope with zero director
rotation retains zero director channels, so this map does not set the director
equal to the geometric normal. These are local implementation checks, not
stability, physical torque accuracy or finite-motion acceptance. Transpose balance
is dual to rigid-motion invariance, not a separate physical accuracy reference.
Raw record: full-trace-work-v2.json. Independent OpenAI Read review found no
source-level objection to preparing this explicitly identified operator.

**A subsequent physical discriminator stops that preparation.** For the actual
half-metre U1 element, EI=1.75e6Nm² and kGA=646153846.1538463N, clamping the root
and inverting the source tip2x2 block gives transverse-force compliance
2.18441845764855e-8m/N, versus the independent force-method expression
L³/(3EI)+L/(kGA)=2.4583333333333335e-8m/N: **11.1423% lower**. Cross compliance
and pure-end-moment compliance agree to roundoff. The source-energy identity
therefore verifies the transcription, not physical shear accuracy.

Command: C:/Python/Python314/python.exe scripts/check_u1_canary_trace_work.py
with OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1; exit0, subsecond algebraic execution.
The strengthened script retains this counterexample and both matrices in
physical-trace-discriminator-v3.json. Review independently checked the parameters,
coordinate pairing and force-method interpretation; no mismatch identified.

Decision: **do not build or execute a corrected U1/US3 coupled deck as a matched
shear reference at this discretization.** Preserve the original canary, the
source-consistent trace construction, and isolated constant-curvature result at
their stated scope. A nominal coupled pure-moment load can induce attachment
shears and is not exempt. This does not reject all U1 meshes or change any
criterion. No parameter fitting or refinement campaign follows this finding.

Return to the existing external beam-only physically matched evidence and common
work maps when selecting the next native transfer discriminator. Distinguish
continuum idealization, discrete trace and enforcement errors explicitly; a
nodal-P1 attachment is a valid declared discrete model, but is not an exact oracle
for a different interior trace. Mandatory full external comparisons remain open.
No external solver was launched; formal F03 remains unconsumed.
