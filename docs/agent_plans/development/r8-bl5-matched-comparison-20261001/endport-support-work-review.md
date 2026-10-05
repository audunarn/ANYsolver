# Saved beam end-port/support-work decision analysis

The remaining beam-root ground difference is predominantly the **internal G term in an algebraic decomposition**, with substantial moment cancellation against the attachment term. This does not identify a defective beam law: G changes with the accepted state and interface action. No support mismatch, missing native torque, or inconsistent native endpoint-work map was found in this bounded check. Physical accuracy/convergence remains open.

Scope: all nine saved nx16/32/64 × Fy100N/Mx10Nm/Mz10Nm cases. Only JSON/NPZ reads and saved-array contractions were performed; no product/reference imports, model construction, matrix factorization or numerical solve. [The data](C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-endport-support-work.json) retains all six G, Cᵀλ, L and actual-ground covectors for every typed root node in both domains, their differences, common-origin aggregates, boundary traces and retained-work contributions. [The read-only analysis source](C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-endport-support-work.py) binds every consumed input by SHA256. An initial path/string hashing error stopped before reading arrays or creating the JSON; it was corrected locally, with no scientific solve attempted.

At root L=0. The actual equation is R=Pfixed(G+Cᵀλ−L), hence ΔR=Pfixed(ΔG+ΔCᵀλ), native minus external. Beam root components0..4 are fixed and normal spin5 is free; shell root components0..5 are fixed. All six raw components, including the free component, remain in the data. Common-origin moments use (0,0,.0675)m. The decomposition residual is at most4.62e−14 in the corresponding N/Nm component. Δbeam-ground equals minus the saved whole beam-interface difference within4.82e−9 absolute; total root-ground native/external difference is at most7.61e−9 absolute, consistent with the retained physical balance budgets.

The table uses the declared1m force-equivalent norm. G% is the signed projection (ΔG·ΔR)/(ΔR·ΔR), not a causal percentage; ΔC supplies the remaining projection. Shell projection results and every individual component are retained in JSON.

| nx | load | ‖Δbeam R‖ | ‖Δbeam G‖ | ‖Δbeam Cᵀλ‖ | beam G% | shell G% |
|---:|:---|---:|---:|---:|---:|---:|
|16|Fy|5.12688|4.57705|.969805|88.06|76.61|
|16|Mx|.206402|.198322|.103527|83.58|65.16|
|16|Mz|.380942|.350182|.0726703|90.43|81.09|
|32|Fy|3.62868|3.11175|.711081|84.85|69.76|
|32|Mx|.101198|.0963917|.0431570|86.27|69.57|
|32|Mz|.250056|.215540|.0500044|85.15|70.15|
|64|Fy|2.88413|2.46968|.520723|85.03|70.36|
|64|Mx|.0461557|.0430927|.0157756|87.74|73.21|
|64|Mz|.205705|.174759|.0386057|84.33|69.02|

For example, nx64/Fy beam ΔMy=+.248514−.293942=−.0454282Nm; nx64/Mz ΔMy=+.0178731−.0212344=−.00336134Nm. These cancellations prevent interpreting the overall G projection as a componentwise attribution. Beam ΔRz-moment is zero under the declared free normal spin. No other component or whole-interface observable is discarded.

The declared nodal supports, typed coordinates, material arms and reference frames match. The **discrete director traces differ intentionally**: [NativeHalfCellPort](C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver/_stiffened_shell_l1_local_experimental.py:131) interpolates translations and uses retained cell Θ; its active variation contains two nodal translation triples and one retained rotation triple. External P0 work uses continuous nodal P1 θ and shell-edge Q1 fields. Accordingly native beam-root rotational Cᵀλ is exactly zero, whereas external beam-root Mx/My attachment covectors are nonzero. Native torque acts on retained cells; it has not vanished. The full saved rigid-domain maps reproduce the recorded wrenches exactly and retain internal/interface angular contributions up to22.3724Nm, which a nodal-only beam sum would omit.

Native clamped nodal θx/θy are zero in every saved state; first-cell Θx/Θy are interior one-sided trace values, not an extra unconstrained nodal root. Their nonzero values cannot be substituted for boundary data. [The signed endpoint work](C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver/_ge_beam3_retained_generalized.py:106) has p=(n0,n1,m0L,m0R,m1L,m1R), giving first beam-root G=−[n0,m0L] at this virgin, identity-frame reference. This independently derived six-component map matches the saved Kq exactly in all nine cases. [Actual support publication](C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/src/anysolver/_stiffened_shell_ge_experimental.py:832) includes the fixed attachment term. Neither raw root G nor root interface load alone is ground. Vanishing admissible virtual work at fixed coordinates does not make these computed reactions arbitrary or unobservable.

The missing discriminator is **common physical P0-density loading**, not another refinement or law adjustment. Current states solve K_Nq_N+C_Nᵀλ_N=L_N and K_Eq_E+C_Eᵀλ_E=L_E with different λ, so this data cannot isolate bulk compliance from attachment feedback. For the same fixed-flat external coefficient μ=(μt,μx,μy), the native coefficient map is Tμ=(−μt,−μy,μx): translations reverse sign and the two director coefficients permute/sign-change. Verify each actual port transpose and full stationarity under K_Nq_N=L_N−C_NᵀTμ and K_Eq_E=L_E−C_Eᵀμ, preserving fixed-root action terms. An isolated beam with root normal spin free has the physical rigid Mz rotation mode: its load compatibility and any explicit common gauge must be recorded, with the retained cell rotations included. That is a subdomain compliance comparison only; this mode is restrained by the coupled attachment and must not be removed from the full coupled response. No such comparison was implemented or executed here.

The reviewed product seams match the saved388-module identity/wheel0c456666… byte-for-byte. Frozen collector sources are native143297217ec7… and external0e5435e0d389…; no product or historical evidence changed. This analysis supports a bounded next decision or parking M2; it supplies no1% accuracy, locking, limit-equivalence or F03 acceptance and does not justify another automatic mesh level.

Analysis source SHA256: fca21ef43f124649b1cec70aeff975fa4bb142589974b3409ecfd2c1d63bd4ef.
Data SHA256: 48f2132a483b19b803f6ad6623de8fab6cec83c56e9eb15432b39fd0e6ffc777.
