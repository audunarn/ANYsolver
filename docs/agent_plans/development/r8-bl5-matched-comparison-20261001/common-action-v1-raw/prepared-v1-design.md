# Common physical P0-action control: prepared, not executed

This one fixed-finest-grid control separates uncoupled native domain response from the coupled redistribution of interface density. It consumes only saved nx64×ny16 /128-halfcell/c2-span4 operators and the three saved external Fy100N/Mx10Nm/Mz10Nm densities. No model, section, mesh, law, support, reference or scientific criterion changes. The external coupled state already supplies the external isolated response under its own recovered density; no external solve is necessary. The source is [r8-bl5-common-density-control.py](C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-common-density-control.py). No factorization, numerical import, screen or solve was performed during preparation; only stdlib schema reads and AST parsing.

Run authority remains with root. First run `--screen-only --cases fy` into an exclusive directory. This constructs actions and verifies premises without LU. After independent clearance and the successful screen, root may execute one Fy control. Only if that establishes a usable discriminator should the remaining Mx/Mz controls run; never repeat Fy implicitly. The CLI can reuse two sparse factors for a supplied unique case list. Total scope is at most the three existing nx64 loads, no new/fourth grid or amplitude sweep.

## Exact measure, basis and coefficient map

Both formulations multiply **integrated** work rows, so coefficients are densities: the first three entries have N/m, the last two Nm/m. No support-width division, nodal-force reinterpretation, or direct copying of raw lambda is allowed. Every native saved station `density_basis` must be identity5, with row IDs `(j,32+j,64+j,96+j,128+j)` for its geometric P0 support; all256 positive union-quadrature measures must sum to1/32m in each support. All saved frames are identity, director z, zero beam-section lift, shell top arm rs=.0175m and beam attachment arm rb=−.05m.

At a virgin station, the external gaps are

`gE_t = ub + rb*(theta_b cross z) − us − rs*(theta_s cross z)`,
`gE_rot = (theta_bx−theta_sx, theta_by−theta_sy)`.

Native translations satisfy `gN_t=−gE_t`; native director gaps satisfy `(gN_3,gN_4)=(−gE_rot_y,+gE_rot_x)`. Therefore native/external scalar work is identical under

`lambdaN[j]=−muE[5j]`, `lambdaN[32+j]=−muE[5j+1]`, `lambdaN[64+j]=−muE[5j+2]`, `lambdaN[96+j]=−muE[5j+4]`, `lambdaN[128+j]=+muE[5j+3]`.

The script constructs this sparse T explicitly, checks external support records against their flat coefficient vector, independently reconstructs all160 native C rows from flat virgin derivatives and saved measures, and checks full matrix parity against saved C. It then checks every shell-coordinate action for all160 independent basis coefficients, including fixed root slots; every domain's six common-origin rigid actions and combined zero wrench must agree for the complete basis. External C is reconstructed from its saved equation triples, not from native rows. Its transpose must recover the complete recorded external action; native self-transpose must recover its published action. Signs remain: connection resisting `+C transpose lambda`, connection exerted `−C transpose lambda`.

Native beam translations are P1; its port rotations are384 retained cell variables. External beam rotations are continuous nodal P1. Their local rotational covectors intentionally act on different variables. The shell edge is the same Q1 trace. Shell common-action equality is consequently a full coordinate check; beam common-action equality is a physical-functional/full-rigid-work check, not a claimed coordinate equivalence of different trial spaces.

## Isolated nullspace and support semantics

The raw full q has8940 slots:1105 shell nodes,129 typed beam physical stations and64 native members with24 retained variables each (six cell rotations +18 resultants). All native resultants remain in the indefinite mixed operator. Typed node mapping is shell n→external n and beam n→100001+(n−101); overlapping native shell/beam integer IDs never share a namespace.

Bulk K is required to have zero shell/beam off-diagonal blocks. The script checks its stored skew without averaging, the original fixed/free inventory and independent six rigid fields including every retained cell rotation and zero rigid resultant increments. The already independently reviewed local-kernel V2 record is hash-bound and must cover this exact geometry, with resolved local complement/negative18 block. Its conditional numerical nullspace argument is reused; no exact PSD/coercivity certification is invented. Full K must annihilate all six independent rigid fields within the prospective rowwise absolute-contribution budget.

Connected beam members share nodal poses. Local six-rigid kernels therefore share one global rigid field; fixing beam-root translations and x/y spins removes five modes, leaving only normal spin. Its generator is nodal `delta u = ez cross (X−Xroot)`, nodal `delta theta=ez`, all retained cell `delta Theta=ez`, and zero resultant increments. The original normal spin remains physically free. For every prepared RHS `f=L−C transpose lambda`, the script requires `r transpose f=0` within the existing1e−8 physical work/balance budget before LU. Failure stops at incompatible isolated loading; no artificial stiffness or silent reaction is introduced.

A diagnostic gauge q(root beam rz)=0 removes only that proven mode for the beam solve. Its full original free-coordinate residual and gauge reaction are retained and must pass. After solution, one exact rigid shift aligns the root rz to the relevant saved native/external reference for field comparison; source-supported K-null parity was checked first. The gauge is never treated as physical ground or applied to the coupled product response. Any extra singularity causes LU failure, preserved as non-success rather than hidden mode removal.

## Minimal solve and output

The saved shell and beam submatrices, original supports and this single beam gauge give two sparse LU factors. Positive saved coordinate scales form a diagonal congruence only; no global inverse, SPD interpretation, tangent symmetrization, stiffness, penalty or DOF elimination beyond supports/gauge is used. Each factor first replays the native coupled action `L−CN transpose lambda_saved`, then receives the mapped external action `L−CN transpose T mu_external`. One same-equation residual correction is prescribed; failure of unchanged budgets aborts, with no accuracy-tuning loop.

Self-replay must recover nodal, retained-cell, resultant and internal-G roles within the prospective1e−8 numerical consistency limit after gauge alignment. Stationarity uses the frozen owner's load-based global and active-row residual criterion1e−8. Work and gauge-reaction checks use1e−8; mapping, matrix-skew and rigid-field checks use1e−10. These are control-validity predicates, not a native/external accuracy target. Binary64 evaluation remains nominal, not interval certification. Effective BLAS pools must be1; the script imports neither product/OpenSees nor Numba and executes no JIT code.

Only necessary new inputs/actions and solved vectors are retained: q, original L, net domain RHS, mapped resisting action, Kq, physical fixed-ground residual, original free residual, gauge reaction, saved reference q/G and fixed/free IDs. Raw arrays precede solve predicates, and source/input SHA bindings plus explicit exceptions are saved even on failure. Existing campaign operators/geometry are referenced by hash rather than duplicated. Summaries retain separate translation/rotation and1m combined field errors, per-domain internal/applied/interface work, full rigid cuts, every root G/C/ground component, and retained native Theta versus external P1 cell means as a distinct trace observable. External resultant variables do not exist and are not fabricated.

## How outcomes change the decision

A failed basis/work/kernel/compatibility premise stops the experiment at that precise obstruction. A failed native self-replay means the isolated extraction or numerical route cannot support attribution; inspect that failure before any common-action inference. No discrepancy is turned into a pass by candidate-fitted thresholds.

If mapped common-action fields, work and local root-G responses substantially close the previously observed difference, the evidence localizes its dominant component to coupled density redistribution. If a substantial common-action discrepancy persists, it localizes the uncertainty to domain compliance and/or the intentionally different beam director traces/end-port response, motivating examination of those saved roles. This control alone cannot separate bulk discretization from port trial-space differences. Both domains may contribute, and cancellation remains visible.

Equal full action wrenches imply equal ground resultants by balance, so ground equality alone is **not** the discriminator. Informative outputs are gauge-aligned fields, domain work, retained trace response and the componentwise root G versus fixed-C compensation. No preset native/external error cutoff, causal percentage, 1% convergence, locking, limit equivalence, qualification or formal F03 acceptance follows. The existing external Mz reference refinement remains above its1% convergence boundary. There is no automatic follow-on refinement or larger programme in this control.
