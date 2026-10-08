# D1 fixed-pose two-body pressure-work reference — 29 September 2026

This is a development discriminator, not a coupled qualification run. It holds the accepted 4-Q4/8×8-S3 second press pose, ten physical source Q1 pressure functions, two settled active functions, source geometry, material, shell sides, offsets and controls fixed. Only the deformable S3 target test space is refined to 16×16. The source record is `d1_target_grid_8x8_prediction_20260929.json`.

## Question and method

Does target structural resolution materially change pressure-work detection even though the saved 8×8 coupled integrated force is close to its fixed-pressure predictor? The offline probe constructs an admissible structural prolongation, checks physical skin, support, normalized gap and the complete both-body work map `W=diag(S) D(gbar)`, and compares restricted and full pressure compliance under the **same fine contact-free structural stiffness**. The ratio uses only the two settled active pressure modes. Cholesky residuals and the positive fine-minus-restricted projector check guard the comparison. No new contact equilibrium is solved.

All runs use the isolated `c1c4e042` source, Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1 and one BLAS thread, with the existing 180 s / 1 GB limit. The probe SHA and saved-pose SHA are in each raw JSON.

## Preserved failed transfer and correction

The first run used the existing independently shifted 16×16 target knots. Its pose, physical skin and support matched the coarse field closely, but `W_f P` differed from coarse `W_c` by **2.1636374e−4 relative**, above the prospective 1e−7 development guard. It stopped before compliance with `development_two_body_work_transfer_non_success` in 32.69 s / 208.89 MB. The diagnostic replay took 32.48 s / 213.50 MB: the source free-coordinate difference was 1.29e−10 relative, while the target contribution was 2.1636374e−4. Its result remains a non-success.

Independent read-only review identified the cause: even knots coincide, but independently shifted odd knots are not coarse-cell midpoints. Fine triangles then cross old br–tl diagonals, so the coarse P1 target test space does not embed in the fine space. The maximum miss in cell coordinates is about 0.00933. Close physical-position agreement does not imply exact variation transfer.

One corrective run inserted **physical midpoints** of the saved coarse target knots while preserving the br–tl triangle split. The ordinary target-grid builder is unchanged by default. The nested run finished in 38.64 s / 243.90 MB. Its development guards pass:

| Check | Nested result |
|---|---:|
| Pose prolongation maximum | 1.36e−20 |
| Source/target physical skin maximum | 0 / 2.48e−16 m |
| Reference-support relative difference | 3.70e−16 |
| Normalized-gap maximum difference | 2.10e−19 m |
| Admissible-coordinate reconstruction | 0 |
| Complete pressure-work transfer relative difference | 4.12e−16 |
| Fine structural response residual | 3.14e−12 relative |
| Restricted structural response residual | 5.27e−13 relative |
| Active fine-minus-restricted scaled minimum eigenvalue | +0.05972 |

The two generalized **squared dual-response ratios** of the restricted to full fine space are **0.323571 and 0.495166**. This is strong fixed-pose evidence that target structural enrichment adds pressure-work response for both active combinations. Independent review found no concrete transfer or common-energy defect and confirmed this narrow interpretation.

## Decision and limits

The saved 8×8 coupled result is not a spatial-accuracy reference for the two-body pressure response. Define the later pressure/front and mesh-family check using a common two-body work space, with a genuinely nested target test space or an explicit transfer-error bound. Do not infer continuum saturation, mesh-uniform pressure stability, target-force convergence or a converged 16×16 contact solve from this fixed-pose result. The coupled 16×16 press remains unavailable under its unchanged 180 s cap; prior trace attributes most time to contact linearization. The next integrated slice should address that measured cost before repeating a larger coupled case.

Raw records: `d1_two_body_work_reference_20260929.json`, `d1_two_body_work_diagnostic_20260929.json`, `d1_two_body_nested_reference_20260929.json`, their sibling resource JSON and logs, and `d1_two_body_work_reference.py`.
