# F03 continuous-trace spring sensitivity: exploratory v1

21 September 2026. **A diagnostic spring law, not the required exact
multiplier attachment or F03/G0B acceptance.** Source and runner commit
`e409e1c`. Exclusive raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-continuous-penalty-v1/`.
The 48 JSONL records have SHA-256
`78fbb5f41c02db09afac6da4726c086ff9e5eca4ebc9dd205fcbac5ea3cdeddf`.
The manifest binds the three source hashes, runner, Python/NumPy/SciPy and
all Q4/S3, smooth/sine, 8/16/32 joint meshes and four declared stiffnesses.

The independent classical plane-stress panel and conventional beam use the
v3 homogeneous exact-static test field. At every shell-host and beam-field
break, the material attachment interval is split, then integrated with
four-point Gauss quadrature. The regularizing energy is

`0.5 ∫ κ_t [c_x²+c_y²+L_pose² c_θ²] ds`,

where `L_pose=sqrt(.2²+.23²) m` and `κ_t=1e11,1e12,1e13,1e14 N/m²`.
Four- and five-point segmented matrices matched in a bounded oracle;
the integrated energy, sparse tangent, directional derivative, Q4/S3
reaction recovery and two-sided interface-work signs passed local checks.
Only active trace columns are retained at quadrature stations, including
fixed columns for physical reactions; the production solver is untouched.

All 48 cases completed in 18.48 seconds serially. Maximum relative free
equilibrium and work imbalance were `2.13e-12` and `7.74e-13`; maximum
vertical support-force and support-moment imbalance were `6.49e-7 N` and
`4.59e-7 N·m`, and two-sided interface work closed within `4.53e-14 J`.
The high-stiffness cases are therefore numerically balanced in this
discrete spring problem, but the spring parameter changes the physics.

For Q4 at `N_s=N_y=N_b=32` with smooth load, increasing `κ_t` from
`1e11` to `1e14` changes tip `u_y` from `6.08969e-5` to `2.95109e-5 m`.
S3 changes from `6.07695e-5` to `2.96599e-5 m`. At `κ_t=1e14`, Q4 tip
response still changes `1.85498e-5 → 2.42004e-5 → 2.95109e-5 m` across
joint 8/16/32 meshes. Those are not a stiffness-independent, converged
reference. Raising the penalty at a fixed mesh can also lock the
nonmatching discrete fields. The sampled gap is only a lower bound on
pointwise misfit.

Independent read-only code/mechanics review confirmed dimensional work,
exact segmented quadrature order, local sparse storage, fixed-column
reaction recovery, force/moment and interface-work signs and raw evidence
identity. It explicitly rejected any exact-mortar or physical-target claim
from finite spring data. Next candidate selection must use the actual
native retained KKT, signed stability norm, independent physical response
and full interface mechanics; this spring sweep supplies sensitivity only.
