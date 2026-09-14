# Independent MO16 source assessment

Reviewer `/root/g3b_independent_review`; read-only subject `58ad1f094b6707c6e7ad2b70c8e425d2f3dad144`, tree `49d7db624d907d83c468efe804807dc65912058d`. This is source-level adjudication, not a mechanics run, recovery implementation, waiver or qualification acceptance.

## B2: proved incompatibility under the retained requirements

`elements.py` defines `_SMALL=1e-12` at line 101. Its actual scalar `_local_linear_stiffness` computes each Timoshenko parameter as `12 EI / max(S L^2, _SMALL)` at lines 3852 and 3864. Therefore the unchanged stiffness is the force-based operator with effective shear rigidity `Seff=max(S,1e-12/L^2)`, not always physical `S=G A k`. The private local admission at `_ge_beam3_g3c_local_beam.py:115-129` requires positive finite section/material values but imposes no lower positive shear-rigidity floor.

The scalar nonlinear response at `elements.py:4574-4615` adds only the source von-Karman axial potential to the nonaxial linear operator. With `e=du/L+(dv^2+dw^2)/(2 L^2)`, its potential is `U=.5 d^T K_noax d+.5 EA L e^2`. The force-equilibrium interpolation is explicitly defined at `elements.py:851-870`: constant shear and linearly varying moments. Once the actual nonaxial end forces are fixed, these source-equilibrium fields are fixed. Physical constitutive recovery then fixes strains through the original physical section compliance.

For a clamp-active shear direction with nonzero V, the corresponding physical section-energy integral exceeds the actual operator potential by

`Delta = L V^2 (1/S - 1/Seff)/2 > 0`.

The axial nonlinear string term cancels from this comparison; it is not an extra physical shear resultant. Thus **unchanged actual scalar operator + original physical section + source-equilibrium resultants + physical constitutive/work/energy recovery cannot all hold over the admitted all-positive domain**. This is more than an unimplemented output routine. It does not claim that arbitrary fabricated fields or an altered physical/numerical decomposition cannot be constructed; those would violate the retained recovery interpretation.

Independent rational check of the source equations (stdlib `Fraction`, no production imports, 0.069-second process): choose L=E=1, nu=0, A=1/10^14, Iy=Iz=J=1/10^12, ky=kz=1, dv=1 and all other relative components zero. All rotations are identity; a centered translation vector gives the same relative dv. Then S=1/(2*10^14), Seff=1/10^12, phi=12 and V=3/3250000000000. Including the same axial potential in both sides:

- Actual U = 4813/10400000000000000.
- Physical section-energy integral = 11524969/135200000000000000.
- Difference = 1791/21125000000000, exactly positive.

This independently reproduces the general obstruction. It is exact arithmetic reconstruction of source equations, not a call to the binary64 element or a new scientific qualification result. The existing explicit `PhysicalRecoveryBlocked` branch at `_ge_beam3_g3c_recovery.py:48-52` correctly prevents a successful physical-recovery claim. Passing the unclamped registered fixtures cannot remove the full-domain obstruction.

The existing generalized-section flexibility route (`elements.py:873-889`) offers a source-backed *different route* without this scalar denominator floor. Silently selecting it, changing units to evade the fixed dimensional floor, replacing S by Seff, weakening the energy check, or adding an undisclosed numerical correction is not a recovery-only completion of the original route. Any such selected remedy requires a separately reviewed successor formulation/route/interpretation and new relevant validation. Restricting admission would be an explicit loss of the requested all-positive scope, not full closure.

## Q4: specific recovery failure established, general impossibility not established

For the frozen scalar virgin-elastic planar route, `_qualified_linear_correction` (`e4_pl_element.py:5641-5693`) subtracts the inherited zero tangent and installs the qualified baseline. `compute_nonlinear_response` adds this correction to force and tangent at lines 5756-5769. The preserved source derivation is

`U=.5 d^T Kqualified d + sum w*(ev^T A ev - el^T A el)/2`,

where `ev=Bm y+n(Gw y)` and `y=T0 d`. The additional force is `sum w*(Beff^T A ev-Bm^T A el)`, with its full derivative and geometric term. The unchanged `_recover_planar_mixed_fields` instead uses linear stationary parameters `-solution @ local_displacement` (`5962-6040`); public planar `compute_stresses` delegates to it (`6408` onward). It cannot, by itself, become finite source-native work recovery.

The naive sum `Nsum=Nmixed+Nv-Nl` contracted through one `Beff=Bm+Bnl` generates an unwanted `Bnl^T(Nmixed-Nl)` relative to the required source work, even in the simplified coincident-frame comparison. The retained local sentinel `test_q4_checkerboard_and_independent_signed_work_sentinels` at test lines 292 onward already distinguishes zero linear membrane from nonzero VK contribution and detects the mixed/compatible difference. That evidence is preserved, not rerun here. Mixed-baseline weak work, distinct source frames and all numerical exclusions must also be respected; a single-field shortcut cannot erase them.

These observations disprove the existing linear recovery as complete finite recovery and disprove this particular one-Beff summation. They **do not prove that every possible nonlinear mixed stationary recovery representation is impossible** while retaining the condensed nodal potential. A candidate representation would still need independent derivation showing the original physical constitutive relations, stationary work, exact condensed force/tangent, meaningful tensor resultants and numerical separation without changing K or the finite potential. No such representation has yet been established. Arbitrary energy square roots, projected forces, a diagnostic multichannel tuple relabeled as one physical resultant, or a newly solved nonlinear mixed operator whose condensed response differs would not satisfy the original claim.

## MO16 disposition

The original owner inventory names `MO16_REAL_RECOVERY_AND_OPEN_OBLIGATION_ENFORCEMENT`; its adapter schema deliberately keeps `physical_recovery_complete=false`. Recording and enforcing this source obstruction can complete an honest **blocked obligation-enforcement checkpoint**, not full physical recovery or full G3c. B2 alone prevents simultaneous full original all-positive closure under unchanged mechanics. Q4 remains an unresolved derivation/implementation gate, not a proved universal impossibility.

Recommended next decision: preserve a source-bound B2 exact witness and explicit Q4 limitation, then separately review the smallest proposed remedy/authority change. No silent narrowing, coefficient/tolerance change, default activation or qualification rewrite. Existing accepted rehearsal and Q4/S3 evidence remain untouched.

## Source fingerprints inspected

| Path | SHA-256 |
| --- | --- |
| src/anysolver/elements.py | f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37 |
| src/anysolver/e4_pl_element.py | 7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38 |
| src/anysolver/_ge_beam3_g3c_local_beam.py | 36cf60943c7e307acb4160df4883811b8decb8630a1e4bb96cc10c4d2ab12372 |
| src/anysolver/_ge_beam3_g3c_recovery.py | a2100556f3ed682d6880b0387d5f7c2131ac6a869aa2d8b60a2844fa22d6691a |
| docs/GE_BEAM3_G3C_LOCAL_RECOVERY_EQUATIONS.md | 0f81a43804b4874402d7ff09dc158de95888bc4f7e3c734e76548688f7235e67 |
| docs/GE_BEAM3_G3C_MATRIX_SHELL_CONTRACT.md | 59a09dc7db6256a145520ae7b4f2d325dee1abca5d5b5c381a7ada57a2ad92fd |
