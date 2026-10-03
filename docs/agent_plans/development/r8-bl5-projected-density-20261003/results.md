# Complete projected-density patch screen — 3 October 2026

**Retain as a distinct diagnostic candidate; not a selected production space.**
Fixed reference half-cell averages of the complete five-channel affine density
remove the demonstrated torsion covariance while retaining native physical
half-cell poses. No product basis, continuous gap law, beam equation, loaded
solve, reference model or formal F03 assessment was changed or executed.

Candidate identity: `BL5_REFERENCE_HALFCELL_AVERAGED_AFFINE_DENSITY_DEV_V1`.
For each material half-cell, replace `a+b*xi(s)` by `a+b*mean_cell(xi)` in
the same gap potential. All five channels use the same rule and original
support boundaries. This is an exact new discrete multiplier density, not
pointwise enforcement or an unexplained correction to recovered forces.

The source reconstructs original C exactly from the captured local jets,
then changes only its fixed reference density basis. Existing saved K and
reference fixtures are reused; no owner or global tangent reassembly occurs.

| Bounded control | m8 | m4 |
|---|---:|---:|
| Original C reconstruction discrepancy | 0 | 0 |
| Projected prescribed-torsion energy / continuum | 1.0 | 1.0 |
| Finite common rigid-motion gap/work maximum | 2.12e-16 | 2.12e-16 |
| Five-channel physical domain-wrench discrepancy | 1.08e-19 | 1.73e-18 |
| Actual-update local dual-work derivative error | 3.93e-12 | 4.70e-12 |

Three constant translations and all-channel common rigid variations pass.
Physical wrench controls include pure affine densities plus nonzero
constant-plus-affine densities on an off-root support. Force, director torque
axes/signs, arm leverage and moment about the common beam-root origin are
checked against independently integrated projected densities. This does not
replace finite loaded physical transfer or stability assessment.
The tested `C_projected.T*lambda` is the resisting/work-conjugate constraint
wrench. The connection wrench exerted on a domain is its negative; future
loaded-action recovery must preserve that distinction.

## Counterexamples and limits retained

Projection preserves resultant force but changes the spatial first moment of
an affine density by `-b*H^2/(6*m^2)`. Its physical affine L2 Gram entry becomes
`H*(1-1/m^2)/3`; neither original recovery/reference actions nor original Gram
may be reused silently. An explicit common action map is required for future
engineering comparisons.

Compatible quadratic continuum bending sampled on shell spacing2h and beam
spacingh still has normal mean gap `+kappa*h^2/4` in this native sign convention.
Both cases report6.103515625e-9 (h fixed); integrated weak moments are separately
labelled. Projection does not cure this existing interpolation mismatch.
Its order follows the independent interpolation calculation, not a measured
refinement sequence or a bound on coupled response/locking.

A beam-nodal-rotation vector is invisible to both old and projected interface
rules. A bounded alternating example carries110.2769J after eliminating only
torsional moments. Cell rotations are prescribed, and the first cell retains a
rotation residual: this is a positive-energy interface-kernel-vector witness,
not a fully stationary mode, uniform stability result or proof excluding all
mechanisms. One half-cell per support would annihilate the projected affine
basis altogether; it is not admitted by this m4/m8 screen.

## Executions and review

Initial screen completed4.785s; adding pure-affine physical wrench checks
completed4.744s. Independent review found that their zero resultant did not
exercise arm leverage or director torque signs. Nonzero off-root controls then
failed at1.859s; an unchanged diagnostic with detailed controls failed1.929s.
The expected wrench incorrectly used global origin rather than the saved
beam-root origin `(0,0,0.0675)`. The exact offset lever-arm difference explained
the failure. Correcting that test origin, not C or local work, completed4.660s,
exit0, sampled peak163164160bytes, effective native pools one. Failures preserved.

Independent OpenAI review also corrected mean/integral labels and the
interpretation of the kernel-vector energy. Different-family scientific
acceptance remains open. No tolerance was relaxed.

[Initial14-file manifest](raw-manifest.json), SHA256
`fcc2e2cc477360c6daf08e983bd9db0a0300f1be4ab32d428a9063a8660f6c18`,
and [corrective19-file manifest](raw-manifest-v5.json), SHA256
`e4d906fc70e28e3e411a99b69c12d3c5f83568b9534e494b641844fa3da1dfde`,
preserve exact source versions, failed/completed commands, diagnostics and
input/operator hashes. The imported local mechanics come from the previously
byte-verified installed gravity wheel; this is not a final isolated graph.

Next usable action: assess whether this complete reference-density candidate
can support the required common work/recovery and constrained mixed-system
checks, before a matched loaded comparison. Growing spaces, seven ratios,
three-level convergence, torque/shear/drilling, physical references and independent
acceptance remain mandatory. Small gaps, a repaired patch or one Gram value do
not select the formulation. Formal F03 remains unconsumed; M2/G0 and full release
remain open. No channel tuning or automatic refinement campaign follows.
