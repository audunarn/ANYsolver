# Same physical P0 action — development decision, 1 October 2026

Retain the declared BL5 law and complete P0 candidate. Stop mesh/port tuning in
this slice and advance staged material history. No support, endpoint-work or gross
beam action-map defect was identified. Root/reference convergence, drilling
independence and mandatory CalculiX evidence remain open; this is not M2/F03
acceptance or a production multiplier-space selection.

The [independent complete review](common-action-v1-raw/complete-review.md) checks
the actual raw states, all component differences and limitations. The
[manifest](common-action-v1-manifest.json) preserves 26 source/design/review,
launch and raw-state files. Prior comparison records remain unchanged.

The fixed finest fixture uses 1,024 Q4 shells, 64 native three-node members,
8,940 physical/retained coordinates and 160 integrated P0 rows. A zero-LU screen
verifies every independent action basis, shell coordinate map, six retained
rigid-work fields and isolated beam yaw/load compatibility. Native sparse domain
factors replay each saved native action and respond to the same physical external
density. Fy executes once, then Mx/Mz share a second pair of factors. No new mesh,
external model, dense inverse, stiffness modification or formal F03 execution.

| Load | Beam translation difference | Beam nodal rotation difference | Shell director rx/ry difference |
|---|---:|---:|---:|
| Fy | 0.001465% | 1.5211e-8% | 0.007380% |
| Mx | 0.002758% | 1.3103e-9% | 0.010705% |
| Mz | 0.000585% | 9.9060e-9% | 0.009958% |

These are unweighted sampled-vector relative norms, not the earlier integrated
Q1/P1 L2 metric or new acceptance criteria. Beam fields are compared modulo the
isolated free rigid yaw, borrowing the reference representative. They do not
predict coupled yaw. Retained cell orientations remain distinct from external
P1 averages. Fy/Mz aggregate shell rotation differences are predominantly normal
rz (99.9970%/99.9905% of squared discrepancy), released by BL5. All six components
remain visible; this does not prove drilling causation or independence.

Native self-replay physical roles differ at most 8.122e-12; original-free
equilibrium at most 1.023e-9 and gauge reaction ratio at most 9.283e-11, against
the unchanged 1e-8 control budget. All raw weak gaps remain; these uncoupled
stationary responses are not accepted coupled states. Internal work is qᵀKq,
twice elastic energy here. Separate applied/interface work is gauge dependent;
compatible net-RHS/internal work is invariant within the checked residual budget.
Ground-resultant agreement is a force/moment balance control, not attribution.

Common-action beam agreement narrows gross beam/port concerns on these flat
virgin loads. Equal shell action with different response identifies a discrete
shell-compliance difference. It does not uniquely allocate coupled density/root
partition differences among shell resolution, normal spin, trace representation
and feedback. The previous >1.3% Mz refinement and root-transfer discrepancy
remain unresolved. No automatic fourth mesh, law correction or tolerance change.

All three routes are terminal, below one second each and sampled peak 118 MB.
Actual exposed NumPy/SciPy OpenBLAS pools are one; these timings and sampled
resources are diagnostic observations, not performance or general resource
qualification. Product source and installed wheel are unchanged. Prepared-v1
label issues and their pre-run corrections are retained alongside final source.
