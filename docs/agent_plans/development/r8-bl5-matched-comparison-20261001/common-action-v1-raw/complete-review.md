# Independent completed common-density review

2026-10-01. Read-only source, binding, saved-array and derived-data review; no product import, assembly, factorization, solve or numerical rerun. Only this note was written. **No consequential implementation defect found within the admitted finest-grid isolated-domain control.** The control narrows the original discrepancy but does not make an uncoupled quotient state a coupled prediction, establish engineering convergence, or causally allocate the root-transfer discrepancy. Retaining the declared BL5/P0 candidate and ending this diagnostic slice is defensible; the remaining reference/root convergence, drilling-independence, CalculiX and formal F03 obligations remain open.

## Identities, inventory and numerical scope

Reviewed control SHA256 `594c8b73f7ca9b8fa5ecb809c7debbc4ee0e0fc5ae0f26dc0a1934c448a18d51`, design `3257f16b8b709b53200621c536dac183323c6d2153474379202f98e9f2707297`, and supervisor `8866357ab5469286172d07c519c99fe2bcdb44f241ebb9c878d32ab133f208eb`. These are the identities admitted by the retained pre-run review. Original prepared-v1 source/design remain preserved; the revised labels and explicit quotient semantics close those earlier findings without changing the equations or criteria.

| Completed TEMP route | Input hash bindings checked | Numerical work | Elapsed s | Sampled process-tree peak B |
|---|---:|---|---:|---:|
| r8-bl5-common-density-screen-v1 | 18/18 | Fy screen, zero LU | 0.621865800 | 96325632 |
| r8-bl5-common-density-fy-v1 | 18/18 | Two native sparse factors; Fy self/common | 0.698471500 | 110125056 |
| r8-bl5-common-density-moments-v1 | 24/24 | Two native sparse factors reused for Mx and Mz; no Fy replay | 0.815648900 | 117612544 |

All three supervisor records terminate exit 0. Copied source/design, actual result source identity and saved input hashes agree. Screen status is `PREPARED_NO_FACTORIZATION`; the source returns before `splu`. Both solve routes report `COMPLETED_DEVELOPMENT_ONLY` and two factorizations. NumPy and SciPy OpenBLAS runtime pools each report one thread (versions 0.3.31.188.0 and 0.3.30). No product/reference imports occur. These are measured short-route resource observations, not a performance comparison, lifetime thread certificate, or effective external OpenSees API-setting claim.

The fixture is nx64/ny16, 128 halfcells, c2/span4, 32 supports and 160 integrated rows. Full q has 8940 coordinates: 1105 shell nodes, 129 beam nodes and all 24 retained variables of each of 64 members. Exact typed geometry, section/arms/frame/zero-lift eligibility, original supports and applied loads are checked. The original shell root is fixed in six slots; beam root first five slots are fixed and normal yaw is free. This is not a universal point/L1/B2/finite-state contract.

## Physical action, kernel and work checks

Native rows are channel-major, external rows support-major. The explicit mapping is, for support j,
`lambdaN[j]=-muE[5j]`, `lambdaN[32+j]=-muE[5j+1]`, `lambdaN[64+j]=-muE[5j+2]`, `lambdaN[96+j]=-muE[5j+4]`, `lambdaN[128+j]=muE[5j+3]`.
Coefficients are densities multiplying integrated support rows (force N/m, couple Nm/m); support measure is 1/32 m. No second division by support width occurs. Full shell-coordinate action parity includes fixed slots and all 160 independent basis densities. Six rigid-work checks include nodal translations, nodal spins and both retained cell rotations. This is physical covector-work equivalence; it does not replace retained cell torques with external nodal torques or assert equality of different primal coordinates.

Reconstructed C relative difference is 3.46945e-18; all-basis shell difference is 3.46945e-18 and beam rigid-work difference 6.93889e-18. Full external transpose recovery is at most 8.25994e-18, native recovery zero; combined six-rigid imbalance is at most 1.99840e-15. Saved external free stationarity is at most 2.54833e-11. All prospective mapping/physical controls pass without tolerance changes.

The uncoupled bulk cross blocks are zero. Finite positive diagonal scales and skew are admitted without symmetrizing or assuming SPD for the mixed beam block. The bound local-kernel premise (`1d3ed66a7f1128254bc07d323d678ebca512af2dcd7662329752685d8447430f`) resolves the 18 negative resultant directions, the six rigid modes and no additional uncertain local mode for this geometry. Together with checked member connectivity and supports it identifies the isolated beam yaw. This remains a conditional nominal-binary64 argument, not exact or continuum coercivity.

The full rigid yaw contains translations about the one beam-root origin, nodal spin and retained spins; its original fixed entries are zero and K-annihilation is checked. Full RHS compatibility is checked before factorization. Worst external-common compatibility ratio is 2.92954e-11. Only isolated beam root yaw is removed for the solve. The saved coupled reference yaw is subsequently borrowed to align quotient representatives, and the original-free equilibrium and gauge reaction are retained. This cannot predict the coupled yaw amplitude, which is constrained by C in the coupled problem.

| Case / branch | Original-free equilibrium ratio | Gauge reaction Nm | Gauge ratio | Internal/RHS work relative error | Self replay max absolute coordinate difference |
|---|---:|---:|---:|---:|---:|
| Fy self | 4.66388e-10 | 5.79201e-15 | 2.12190e-16 | 8.86408e-13 | 8.12136e-12 |
| Fy common | 6.90327e-10 | -2.53400e-9 | 9.28206e-11 | 9.36484e-12 | — |
| Mx self | 3.47810e-11 | -7.79958e-17 | 7.79958e-18 | 8.81809e-14 | 6.10261e-13 |
| Mx common | 2.93067e-11 | -2.98913e-10 | 2.98913e-11 | 1.84330e-12 | — |
| Mz self | 5.47459e-10 | 1.13344e-15 | 1.13344e-16 | 7.04318e-13 | 1.71937e-12 |
| Mz common | 1.02252e-9 | 1.76173e-10 | 1.76173e-11 | 1.22463e-12 | — |

All six raw q/reference/RHS/Kq/gap sets are finite, with 8940 q entries and 160 Cq entries. Independent raw q-dot-RHS and q-dot-Kq contractions reproduce recorded totals to rounding. `internal_work_J=q.T K q` is twice stationary elastic energy; it is not elastic energy itself. Net RHS is L-C.T lambda, so exerted interface work is minus q-dot-C.T lambda. Domain totals correctly retain that sign.

| Common case | Native beam internal J | External beam reference internal J | Native shell internal J | External shell reference internal J |
|---|---:|---:|---:|---:|
| Fy | 1.6181169175887044e-4 | 1.6180560063525500e-4 | 2.6231387303662360e-4 | 2.6257622744318640e-4 |
| Mx | 5.4983193900752874e-5 | 5.4983219713727250e-5 | 8.7981950133427540e-6 | 8.7973947025288520e-6 |
| Mz | 1.0102247297242720e-5 | 1.0100465319880678e-5 | 6.5613933279609950e-6 | 6.5678449923758690e-6 |

Each domain's native internal equals native applied-plus-exerted-interface work within the reported residual budget; self replay also reproduces the domain partition. Borrowed yaw changes applied and interface work separately. Fy common adds +1.6590704345159732e-4 J applied and -1.6590704344739328e-4 J interface work, leaving only 4.20403e-15 J net increment. Mx/Mz common net increments are -1.21296e-16/-2.29571e-17 J. Thus an apparently accurate applied-work value with borrowed yaw is not an independently predicted coupled-work value.

Raw Cq is expressly diagnostic. Maximum support-average translation/director gaps for self states are, respectively, Fy 5.62105e-15 m/9.41889e-15 rad, Mx 2.09772e-15/2.99387e-14, Mz 1.46274e-15/1.83432e-15. Common states give Fy 3.30341e-9 m/4.19352e-10 rad, Mx 1.98105e-11/1.18172e-9, Mz 4.22191e-10/2.58208e-10. They are not accepted coupled equilibria; no Cq criterion was silently passed or substituted.

Native physical ground uses the original fixed mask. The external root diagnostic `G+C.T lambda-L` prints all six slots, including the free beam rz residual; that tiny free residual must not be called a physical support reaction. Root G and C individually differ because retained/native and nodal/external endpoint action allocations differ, while their ground combination balances. Fy common root Mx illustrates this: native G=11.329696789846956 Nm and C=0, external G=11.352411839503924 Nm and C=-0.02271504973943994 Nm. Ground equality is a balance control, not causal evidence or identical endpoint discretization.

## All six shell-component contractions

These are independent contractions of saved common-state q minus saved external q over all 1105 shell nodal samples. Translation units are m, rotation units rad. They are **unweighted Euclidean nodal-vector norms**, not integrated Q1/P1 L2. Relative values use the explicit reference norm below; none activates the 1e-12 denominator floor. All components remain visible.

| Case | Component | Difference norm | Reference norm (raw denominator) | Relative norm | Max absolute difference |
|---|---|---:|---:|---:|---:|
| Fy | ux | 6.065258174642799e-9 | 8.639520966159763e-6 | 7.020363974345194e-4 | 4.2694269366527986e-10 |
| Fy | uy | 6.188493318640228e-8 | 6.525059852915415e-5 | 9.484193950918613e-4 | 3.4025904266167357e-9 |
| Fy | uz | 9.991174186507613e-10 | 5.3693815922943015e-5 | 1.860768137777008e-5 | 6.723750565395598e-11 |
| Fy | rx | 1.0830866432601241e-8 | 8.850610910018746e-5 | 1.223742241379166e-4 | 1.2234558430833847e-9 |
| Fy | ry | 3.297025149504439e-9 | 1.2530436877348768e-4 | 2.6312132464147847e-5 | 1.8217366491184018e-9 |
| Fy | rz | 2.0783885199209805e-6 | 1.3789928755099888e-4 | 1.507178577084625e-2 | 5.121951533341315e-7 |
| Mx | ux | 1.621614553883635e-11 | 1.9407120780334656e-8 | 8.355770916450555e-4 | 3.2516401437393092e-12 |
| Mx | uy | 3.3021729770806615e-10 | 1.1159850360972296e-7 | 2.9589760348659026e-3 | 1.4972120242885803e-11 |
| Mx | uz | 1.4551352198147122e-9 | 1.3004990294791558e-5 | 1.1189052716152257e-4 | 9.497920042419990e-11 |
| Mx | rx | 1.0749025168808088e-8 | 1.1424456231624106e-4 | 9.408784935473469e-5 | 3.073882733364448e-9 |
| Mx | ry | 6.2649691370806245e-9 | 2.134067498938879e-5 | 2.9356939929012324e-4 | 3.899321833658883e-9 |
| Mx | rz | 2.0938066442190304e-8 | 2.2474949412255539e-7 | 9.316179564245348e-2 | 6.660788887019743e-9 |
| Mz | ux | 8.615223836027247e-10 | 1.2995440750864494e-6 | 6.629420272224424e-4 | 1.1545592659277419e-10 |
| Mz | uy | 6.734286078543411e-9 | 8.470124978910608e-6 | 7.950633662798145e-4 | 4.993891755280353e-10 |
| Mz | uz | 3.308224052954268e-11 | 7.822771130671261e-6 | 4.228966944953168e-6 | 6.4473696682469965e-12 |
| Mz | rx | 1.298053890214938e-9 | 4.946770820425614e-6 | 2.624042910690686e-4 | 8.324013946790409e-10 |
| Mz | ry | 1.478402371214610e-9 | 1.912822299894789e-5 | 7.728905979901670e-5 | 1.1304341975428504e-9 |
| Mz | rz | 2.0162027252861858e-7 | 2.0754509711277283e-5 | 9.714528328224737e-3 | 8.642643711598190e-8 |

For Fy, the aggregate shell rotation relative norm is 0.0100758031; 99.9970328% of its squared difference is normal rz. The constrained rx/ry-only relative norm is 7.37996293e-5. For Mz the corresponding values are 0.00703646338, 99.9904793%, and 9.95767102e-5. Mx rx/ry relative norm is 1.07050822e-4; rz contributes 73.9054376% of the squared rotation difference and has a very small reference denominator. These are component observations, not new engineering tolerances.

BL5 releases direct normal-spin coupling: the constrained director channels are rx/ry here. Released rz cannot be counted as disagreement of the constrained director law, but it cannot be silently removed from full engineering outputs or registered six-component criteria. Both shell bulk discretizations still carry their numerical drilling choices. Concentration of the discrepancy in rz does **not** prove drilling causation or drilling-stiffness independence; the required controlled independence check remains open.

## Bounded interpretation and disposition

Common-action beam sampled translation/rotation relative norms are Fy 1.464719e-5/1.521090e-10, Mx 2.757909e-5/1.310289e-11 and Mz 5.850604e-6/9.905967e-11. Retained-cell versus external P1-mean rotation differences are also recorded, rather than equated by assumption (difference/reference vector norms: Fy 2.044028e-9/7.508510e-5, Mx 1.869035e-10/4.109273e-5, Mz 1.076258e-9/1.092414e-5). These narrow the possibility of a gross retained beam action/work-map error on these three loads. They do not certify the complete beam operator, finite material response, or coupled yaw.

For the shell the same physical action is equal coordinate by coordinate, so its common-state response difference is a discrete shell compliance difference under this particular action, not a mismatch in the mapped load. It does not uniquely allocate the earlier coupled density/root partition difference to shell resolution, drilling, endpoint policy or feedback. Changing native self density to external density at fixed native K supplies an actual sensitivity discriminator; it does not establish causal percentages for the original coupled error.

The earlier matched-family engineering limitations survive: last Mz work changes exceed 1%, fixed-distance root action differences remain visible, and finest same-level agreement alone does not establish converged accuracy. No fourth grid, port/law repair, space selection, acceptance or formal F03 execution follows from this control. Carry the precise reference/root convergence and drilling-independence obligations to M4/M5; mandatory independent CalculiX/full-convergence work remains pending. Proceeding to the separate authorized staged-material/restart slice is compatible with this disposition.

Raw solved-state NPZ SHA256, retained for archive binding: Fy self `767f7db598210bf5b65c9f714ca31a09f356ef162af0b4db2051f3320e2c6fe1`; Fy common `58eff18e3f787fec4bc089f6724241b99f8912238253cf6a934c4a16b4773394`; Mx self `914f36ce31730585faef561ec70fd11e6765fd49a8c54dd80e0fcbb8b64388c2`; Mx common `28e2869e186b150cd15514f665d696089373b7ef3195b94b3e6b15fd6386e827`; Mz self `7484b1032aa8514456e2ba43c6cd869223cd32ea050fa74d0be321f3133c1749`; Mz common `3792918df73ca8f47c6792a7b817d96c709518fdac3af73c3be093a3d8cf14ab`. Result metadata binds source and inputs; these output-byte hashes supplement it and do not imply an already-sealed qualification archive.
