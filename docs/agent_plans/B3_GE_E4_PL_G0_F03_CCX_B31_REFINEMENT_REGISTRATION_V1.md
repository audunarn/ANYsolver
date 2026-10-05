# Exploratory B31/CPS refinement registration v1

21 September 2026. This is a **single-use, 12-case external feasibility and
refinement screen**, not the mandatory F03 comparison, the G0B line-space
selection, or release evidence. Execute once from the committed runner
`scripts/run_b3_ge_e4_pl_g0_f03_ccx_b31_refinement_v1.py`; preserve all cases
including failures. Its case inventory and parser were fixed before execution.

Executable: stock CalculiX 2.23 Windows binary SHA-256
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
Environment: Windows, one OpenMP thread, 120-second cap per case, serial cases,
fresh exclusive result root. Source identities and result-root hashes are to be
recorded in the terminal report. No baseline candidate is being timed.

For each Q4/CPS4 and S3-V2D/CPS3 topology, run the smooth and signed sine
load over `n_shell = 2, 4, 8` and `n_beam = 4, 8, 16`. The same 1 m long by
1 m wide, 0.07 m thick isotropic panel and 0.1 m square rectangular B31 beam
are used. Panel end columns and beam root are fixed. The beam load densities
are `1e6(1 + .25 cos(2πs)) N/m` and `1e6 sin(2πs) N/m`, respectively,
integrated to nodal forces by eight-point Gauss integration. Connection uses
the same material four-sample shell position/yaw trace at each non-root beam
station and twelve or more nodal constraint equations; the beam root shell
footprint remains untied. This is a collocation law with a distinct section
and shear idealization, and the model does not represent the qualified B3-GE
finite-rotation or E4-PL shell mechanics.

Record successful process completion, original-node displacement parsing,
tip and centerline shell displacement, station translation equation gaps,
and all raw solver files. Request nodal reaction data for later audit. A
solver success alone cannot certify balance, between-station compatibility,
mesh convergence or physical agreement. Parse failure, factorization failure,
timeout or incomplete cases are recorded and terminate this version's
feasibility conclusion rather than being replaced with an altered deck.

The diagnostic question is whether the conventional external model admits a
stable trend under the frozen mesh refinement in both signed cases and both
topologies. Three levels can reveal divergence or a strong topology effect,
but cannot alone prove asymptotic convergence. Any claim against the native
model requires a separately registered section, shear, trace, supports and
load mapping and an independent mechanics review. F03/G0B remain open even
if all 12 runs finish.
