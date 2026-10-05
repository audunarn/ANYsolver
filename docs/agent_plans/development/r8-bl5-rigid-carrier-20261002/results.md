# Native BL5 rigid-carrier normal-spin discriminator — 2 October 2026

Decision: retain the five-channel law and complete c2 P0 candidate for development. The bounded three-level batch is complete; no fourth refinement is authorized by this record. Correct released-spin/work maps and decreasing discrepancies support that decision, but transfer accuracy remains unresolved. No M2/F03/G0B acceptance or release follows.

## Physical comparison

One metre beam, diagonal generalized section EI_z=1.75e6 Nm² and kGA_y=646153846.1538463 N, native retained half-cell variables. Beam axis z=.0675 m; shell top z=.0175 m; connection arm −.05 m. All carrier coordinates fixed. Beam root coordinates0–4 fixed, normal spin free; beam tip uy fixed and Mz=10 Nm applied. Continuous BL5 gives v=0 with normal spin phi free. From Timoshenko virtual work:

    Vy=−GA phi; Mz=EI phi'; EI phi''−GA phi=0
    Mz(0)=0; Mz(L)=10
    phi(L)=M coth(kappa L)/(EI kappa), kappa=sqrt(GA/EI)
    beam-side line force py=GA phi'
    beam endpoint reactions Ry0=−Vy(0), RyL=Vy(L)

The physical boundary-layer length is .0520416499867 m. Finite weak P0 enforcement is not the exact continuous constraint. This exercises normal-spin release and bending EI_z; it is not beam-axis Saint-Venant torsion.

| Shell/beam half-cells | Tip response error | Integrated Fy error | First root-Mz error | Tip Fy reaction error |
|---|---:|---:|---:|---:|
|16x4 /32|+3.01643%|−23.59458%|−24.88539%|−23.59031%|
|32x8 /64|+0.48517%|−8.44501%|−8.90863%|−8.44501%|
|64x16 /128|+0.10052%|−2.50232%|−2.63970%|−2.50232%|

Tip work and spin are one observable, W=M phi(L). Independently integrated zeroth/first/second station transfer moments and individual endpoint reactions expose the slower physical transfer convergence. The highest moment error remains −2.91350%. Finest root Ry=1.65758e−6 N versus1.73599e−6 N (about−4.52%); its small error on an applied-force normalization does not prove relative root-force accuracy. No near-zero root denominator is used as the sole accuracy criterion.

Actual port gradient pullback and assembled −C.T lambda agree under the existing independent physical_transfer check. Work, equilibrium and total force/moment controls are near1e−15; weak constraints≤3.72e−26. Physical direct normal couples and axis-normal moment densities are zero. Orthogonality by construction alone would not verify the implementation; actual pullback parity supplies that check. Raw sparse indefinite K,C,A and complete state/reactions/multipliers precede checks in every run.

## Execution and assurance

Product base613e43f7/checkpoint84649e34 unchanged. Reused installed wheel SHA4c14d0942410f97b6e2ab397eb0d4e567cbff4169c05b391c5685c4df40d3b7c, with all391 source/wheel/site modules matched before each pilot; each run records211 onsite imports, no escapes. One effective numerical thread, JIT off, serial600s/1GiB. Observed full-route times4.9263/14.4753/51.0288s; sampled process-tree RSS166965248/198012928/332464128B. These are diagnostic costs, not a performance claim or scale qualification. All runs exited0 with no limit.

Two independent analytical tests pass (equilibrium/end conditions, integrated energy/work, derivative, sign, equivalent units and overflow-resistant slender evaluation). Initial source collection failed with ModuleNotFoundError for the unqualified script import; repaired by scripts-qualified import and lazy assembly dependencies. Failed/repaired records and exact test versions are retained. No unchanged regression campaign was rerun.

Separate read-only OpenAI reviewer found no blocking mechanics, sign, origin or identity defect; its transfer-profile finding was addressed using saved state without another solve. Reviewer was not the implementer. This is independent-source scrutiny, not a different-model-family qualification claim. See review.md.

[Raw payload and checksums](raw-v1.json) bind53 members in raw-v1.zip, SHAcd5116af3b4fb37686ab1200881772b85cfcc47c20b7606890e203ebae600f6b. Includes fixtures, launcher, supervisor, source failure/repair, all three sparse operators/states/import/resource records and independent postprocessor. The exact reused wheel remains in the preceding linked B2 installed evidence, not recopied here. New payload scan for known inherited credential values is clear; the historical dissemination restriction remains.

## Resulting action

Retain normal-spin semantics/candidate; stop this bounded refinement. Boundary-layer force-transfer resolution remains an explicit M2 ticket: finest 2.5–2.9% transfer discrepancy is above1%, notwithstanding0.101% tip agreement. This result does not identify beam versus weak enforcement separately, certify elastic coupled torque/shear, prove drilling independence or qualify the complete mechanical mesh-ratio envelope. Preserve required external references and actual constrained-system assessment. No penalty, stabilization tuning, equation/criterion change or formal F03 execution occurred.

Advance a concrete independent GE material/load integration slice after inspecting current owner contracts, instead of automatically extending this reference. Reopen the transfer ticket only with a discriminator that separates beam interpolation from weak enforcement or a matched physical reference needed by the advertised scope. Full Revision8 goal remains incomplete.
