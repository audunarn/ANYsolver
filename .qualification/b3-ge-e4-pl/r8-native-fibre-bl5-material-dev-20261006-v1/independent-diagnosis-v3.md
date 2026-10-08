# Independent Read review of saved rejected-trial reconstruction

Disposition: the reported axial differences are evidence consistent with finite-difference roundoff amplification, not a noise certificate or tangent pass. One concrete term-role labeling error requires correction. Neither the ULP comparison nor the reconstructed norms establishes the cause of the failed .3125 continuation.

Scope: non-author OpenAI fallback Read review, 2026-10-06. No solver, numerical-package import, numerical evaluation, arithmetic campaign, product edit, Git operation, sibling inspection or protected-campaign traversal. Only this new note is written. This is not different-family acceptance or a qualification decision.

## Inspected identities

- `owner-diagnosis-v3.py`: `a38ce8dcebaac0ef27b62134e94030cf34e5b384ac9179a7b239d583fee735f3`.
- `owner-diagnosis-v3.json`: `bb1d153dd951da1e97fcc7dcf75e8ec05c23912191bf99f26a2ae2b42bb84c0f`.
- Current GE owner: `bc5aee151565ba1e37c52302109e627352d20712bee2bbd9569dccb94d122eda`.
- Finite driver: `2c15cde96cee7facf5b0bd88f33504804a298b6b22bd615dfb983862352332a1` (also the saved rejected-trial binding).
- Retained generalized operator: `39121d4d76a5524579c2ea506c9bdf968a3d254cb7e6740de6173eb5aa7e6787`.
- Retained fibre operator: `f2eb4949bdd870df90343393c2898c7e887a0ac14b41398aa4ade92c7ff7d269`.
- Compensated strain: `0d66c81dd3820a2cc034f0383901805c87cb251d7cf31326ebee32a5d90ff0f0`.
- Compensated coordinates: `b374360f2d1dbe85018cb1b801d1c54321bdadf4a6bff467678838ab4e662d0e`.

The JSON enumerates the exact saved-array input hashes. This review inspects the reconstruction and its published fields; it does not independently recompute those arrays. Corrected owner output was not available when this note was written. Conclusions bind the hashes above.

## Source and dimensional consistency

The fixture source has eight Q4 shell nodes, five merged beam nodes, two 24-coordinate retained blocks and twenty P0 BL5 rows: q126/KKT146, twelve fixed shell coordinates and free134 are source-consistent. The hardcoded reference geometry, section stiffness and six-force/twelve-moment scaling reproduce this fixture's declared arrangement. They are not a generic decoder for other families, line spaces, meshes or policies. The reference length uses stdlib reductions instead of the compiler's NumPy reductions, so byte identity of reconstructed weights is not established merely by matching formulas.

Packed roles are shell0:48, beam nodal48:78, beam1 cell rotations78:84, beam1 resultants84:102, beam2 cell rotations102:108, beam2 resultants108:126, multipliers126:146. Rows84/87 and108/111 are the two members' axial half-cell compatibility equations. The retained operators form these as kinematic measures minus the conjugate constitutive gradient, retaining its high/low components. Their elastic reference force scale is 2.1e9, so small raw compatibility differences can dominate the diagnostic weighted norm.

Concrete error: `kinematic_terms` classifies every column below108 as kinematic. Beam1 force/moment columns84:102 are consequently mislabeled; columns126:146 would likewise not be force/moment roles merely because they exceed108. In the inspected JSON, row84/column84 is a compliance term with coefficient -1.1904761904761905e-10 and stored product3.040880418263973e-9; row87/column87 has stored product4.318053624281526e-9. These are not chord kinematics. The total Kd and norm calculations do not depend on this label, but the decomposition cannot support a causal claim until corrected.

## What the ULP evidence supports

The published four-row numerator discrepancies are of order1e-18 to4e-17, at most about0.69 ulp of the representative .25m half-cell chord. Their heavily scaled FD errors dominate the combined diagnostic, while errors grow at smaller h. This pattern is consistent with binary64 value perturbations being divided by2h.

It is not a whole-chain rounding bound. `_advance` rounds displacement additions, resultant additions and finite rotation products; `_assemble` then forms compensated reference-plus-displacement pairs. `compensated_strain` carries two-part chords through rotation and only later collapses scalar values. Therefore ulp(.25) is a characteristic geometric scale, not the actual translation-update quantum or a proof that one specific subtraction caused the differences. Rotation rounding, constitutive gradients, residual assembly, FD subtraction and tangent action also participate. A genuine fixed analytical derivative bias can itself have 2h times its magnitude below a chord ULP; that provides a mathematical counterexample to treating this comparison as proof that all error is noise.

The reconstructed plus/minus quantities derive from stored derivative errors plus reconstructed Kd; they are not independently saved positive/negative residual differences. The original error used the numerical-package tangent action, whereas this reconstruction uses fsum of rounded products. `fsum` improves summation, not product formation or original matrix/constitutive construction. The close saved-versus-fsum linear residuals consequently do not certify an exact physical operator or tangent.

## Remaining mechanical question

`_linear_equilibrium` accepts using its actual-load global and active-row ratios, and compatibility has its own fixed scaling. The reconstructed combined KKT norm is a diagnostic, not those acceptance criteria. It does not replace any metric or tolerance.

The saved small Newton perturbations have unchanged activity masks and descend, but the failed dyadic interval changes fibre activity from eight to nine while shell and generalized activity remain zero. Counts are not complete branch identities, and accumulated-history masks do not certify every constitutive subbranch. ULP-scale FD discrepancies neither explain nor dismiss that finite nonlinear transition. They do not establish convergence, a limit load, structural instability, a tangent defect, or a remedy. The next mechanical discriminator must address the actual finite branch-changing increment under the existing law and gates; no new run, refinement, tolerance change or arithmetic cascade is authorized by this review.
