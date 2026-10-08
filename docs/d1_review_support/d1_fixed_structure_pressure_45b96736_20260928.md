# Independent fixed-structure pressure comparison — development evidence

The [exact-source scalar comparator](../../scripts/general_contact_d1_fixed_structure_pressure_probe.py)
at `45b96736` holds a 32×8 Q1 structural mesh and the near-rim y knots fixed.
It changes only the x pressure basis: matching 32×8 nodal Q1 versus a 16×8
Q1 basis. The independent Q1 mortar oracle and saved FV256×320 reference
retain the same 8×9 support-aligned physical bins. The matching case
reproduces the independent oracle's pressure and bin forces before the
coarser-space comparison. The [raw result](d1_fixed_structure_pressure_45b96736_20260928.json)
binds source and reference hashes; the [resource record](d1_fixed_structure_pressure_resource_45b96736_20260928.json)
retains the bounded command.

| Fixed 32×8 structure | Matching 32×8 pressure | Coarser 16×8 pressure |
|---|---:|---:|
| FV bin L2 error | 0.4811% | 0.1330% |
| Minimum physical Q1 gap | −17.9 nm | −41.2 nm |
| Active pressure modes | 96 | 48 |
| Active unit-diagonal compliance eigenvalue ratio | 2.34×10⁻⁵ | 1.00×10⁻⁴ |

The two pressure representations differ by **0.5040%** on the physical bins
and **0.03567%** in integrated reaction. Equilibrium is below 2×10⁻¹⁵ N and
the reported complementarity product is below 9×10⁻¹⁸ Pa·m in both scalar
solves. The independent reviewer found no material cross-mass, KKT, bin or
physical-gap calculation defect.

This establishes that pressure representation materially affects this
observable with the structural mesh fixed. The coarser basis's closer FV
agreement can be error cancellation, and its larger eigenvalue ratio is a
comparison across spaces of different dimension. Neither result justifies
changing the production fine Q1 basis or establishes pressure-space
stability. The y/rim pressure resolution and nonlinear deformable-target
response remain untested by this scalar comparison. It is development
evidence, not D1 acceptance.
