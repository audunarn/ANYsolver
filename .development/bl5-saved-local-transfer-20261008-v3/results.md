# Saved BL5 local transfer — development result

The same 1 m shell/bar geometry, supports, material, 20 five-channel P0 rows,
and declared Fy=100 N/Mx=10 N·m resultants were used on the already executed
CalculiX C3D20 reference and the native B3-GE/E4-PL owner. The CalculiX
displacements were read from the pinned DOUBLE FRD output; no new external
solve ran. The recovered physical multipliers agree with the independently
assembled continuum KKT to relative error `6.90e-10` (Fy) and `6.52e-10`
(Mx). Native and resolved gap/action stations are the same eight two-point
Gauss locations. Each side's integrated station work reconstructs its assembled
weak rows to below `3e-19 J` absolute. CPU0, one Numba thread, JIT disabled and
two one-thread OpenBLAS pools were observed. [Exact receipt](receipt.json) and
[raw profiles](local-transfer.json) bind the source and saved inputs.

| Load and side | Position-gap RMS | Director-gap RMS | Sum of absolute local work / applied work |
|---|---:|---:|---:|
| Fy, resolved | `2.03e-8 m` | `2.31e-7` | `0.00728` |
| Fy, native | `1.34e-7 m` | `3.08e-6` | `0.04905` |
| Mx, resolved | `2.45e-8 m` | `7.15e-7` | `0.01848` |
| Mx, native | `2.05e-7 m` | `6.85e-6` | `0.10860` |

The local-work quantity is the sum of absolute quadrature contributions
`|w λ·g|`. It is a diagnostic for cancellation inside weak rows, not stored
energy or connection compliance. Signed interface work is approximately zero
on both equilibrated models. Fy local action is dominated by transverse
translation and one director component; Mx is dominated by the latter.

The first runner attempt failed its own near-zero signed-work scale and is
preserved at `../bl5-saved-local-transfer-20261008-v1/`. The corrected second
attempt passed; the third adds an explicit independent-multiplier guard. This
is one coarse development geometry, two loads and a different beam body/
traction representation. It does not identify whether native P0 resolution,
beam warping, end traction or support idealization causes the tip-response
difference, select a multiplier space, or satisfy F03/M2 acceptance.

Next discriminator: keep the native body, geometry, supports and both loads
fixed and compare one coherent continuous-P1 five-channel multiplier space
against P0. If the richer space does not materially change local gaps/work,
do not spend an external comparison on that basis. If it does, assess rank,
locking and physical transfer across the required ratios before selection.
