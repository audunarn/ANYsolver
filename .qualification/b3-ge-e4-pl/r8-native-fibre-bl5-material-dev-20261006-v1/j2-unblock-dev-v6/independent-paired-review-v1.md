# Independent paired-data Read assessment

B supports the original rich-direction **fixed-base smooth-branch derivative criterion at the two prescribed finer h**. The coarse h crosses a material branch and is ineligible for that smooth comparison. This is a scientifically supported disposition for root to adopt, not a pass of the unchanged historical test or the full material/programme gate. No product/test/original-evidence edits, solver evaluations, numerical imports, inverse/factorization, new mechanical jobs or new stencils were performed. Saved JSON/NPY were inspected with stdlib parsing, equality/role checks and comparisons. The immutable derivative-contract note is unchanged.

## Actual route, field and metric

`capture.py:175-209` restores B from v5 `accepted-0002.bin`, frozen SHA256 `487db8581a5a93517fd8e4956c092cd48c7473302ddb626b2886d2c477c91f03`, then asserts generation2, factor1 and checkpoint byte equality. It uses `definition(shell_material=False)` and the exact original rich direction from `tests/test_stiffened_shell_native_fibre_bl5_material.py:230-242`. No smaller/alternative direction, projected residual or changed origin is used. Base K and R are saved before the six `_advance` samples. The reported calculation at capture:199-204 is exactly

`norm((((Rplus-Rminus)/(2*h))-K0*d)*W)/max(norm((K0*d)*W),1)`.

It compares to **K0**, not a better-scoring candidate matrix. All three original h are evaluated. This review inspected the executed calculation and reported outputs rather than independently recomputing the FD norm or applying the global operator anew.

Saved R/d/W/expected are length146; K is146x146 CSC; q has126 coordinates and multipliers20. Saved CSC lengths/indices are consistent. Direct saved-array comparisons confirm all six ordinary binary64 resultant updates, shell/beam translation updates and multiplier updates against the original `base+h*d` two-operation update; physical/generalized callback p inputs equal the corresponding saved state.resultants. Frames/cells are captured from the original `_advance`, whose left-exponential update remains unchanged; rotations were not independently reevaluated. The field retains shell translations/rotations, all five beam nodal translations/rotations, both retained rotation and force/moment groups, and all20 multipliers. All12 fixed-direction entries are zero; all W entries are positive and all multiplier weights1. No support-reaction or compatibility rows are omitted. Saved expected row0=-161370.25900555347 with W0=.3783465619944816, so the denominator exceeds60000 and is not floor1-dominated.

Every B sample has factor1, generation2 and combined predecessor digest `0de32bf182709916e707c99aebded2f0bab3f6a8bbeeb01f08f1052d17498556`. This digest was independently matched to B-origin shell+beam contents. All individual callback origins match those saved predecessors, preserve object IDs/hashes across samples, and saved beam candidate histories match the actual cell responses. The source asserts origin/checkpoint/generation preservation after all samples. Counts record7 assemblies,6 advances,21 Q4 responses and7 responses for each retained/cell family, consistent with base plus six samples. Entry/runtime confirm source imports, exact CI dependency versions, affinity[0], JITdisabled and three effective numerical pools each1 thread. Terminal capture exit0,56.5716s/184254464B is execution evidence, not resource qualification.

## Actual branch evidence and intervening crossings

B's three Q4 callbacks have curve=null, so no J2 branch/tolerance-switch assessment is being smuggled into this claim. The generalized member's eight station labels remain ELASTIC with margins near-1e20. The physical member has32 fibre points. Base and every finer +/- sample have16 ELASTIC and16 PLASTIC_NEGATIVE, with **identical per-fibre sign, algorithmic modulus and interval tags**. Neither YIELD_BOUNDARY nor HARDENING_KNOT appears. Elastic margin magnitudes at fine samples are at least about19214Pa; the smallest active-plastic trial margin is384682Pa. These are separated from equality, rather than activity booleans standing in for branch identity.

Exactly one coarse change occurs: station0/fibre0 switches PLASTIC_NEGATIVE to ELASTIC at +1e-4. Its base trial margin is428992.340464Pa; at +1e-4 it is-122.535514Pa, with modulus changing from995260663.507109Pa to210000000000Pa. Its +1e-5/-1e-5 margins are384682.340464/473302.340464Pa. Other signs/moduli/intervals remain unchanged. The original coarse activity failure therefore has concrete constitutive support.

The fixture explicitly uses `FlowCurve((0.,),(1e5,),1e9)` (`examples/stiffened_shell_native_fibre_bl5.py:18-20` through the material definition). There are no positive hardening-table knots. Capture's interval tag is `sum(a>k)`; tag0 at a=0 and knot_distance0 merely denote the initial accumulation origin, **not** a HARDENING_KNOT. Actual recovery labels and source `_return` govern that distinction.

There is a useful stronger argument than endpoint activity equality here: with this fixed-origin linear-hardening law, the material potential is piecewise quadratic. Within a fixed signed active pattern, station/cell T is constant and the conjugate solution x is affine in retained p. Its signed elastic/plastic inequalities define a convex branch region. The fine endpoint patterns and strict inequalities thus support the entire intervening affine material-force segment; a hidden yield/return excursion is incompatible with that branch's affine solution and uniqueness. This argument applies to the cell's p input, independent of the nonlinear pose kinematics. It does not generalize automatically to arbitrary nonlinear hardening, changing histories or a nonlinear material-input path. The generalized elastic norm region is convex as well. The saved ordinary binary64 input checks support the implemented samples; no certified all-intermediate floating-point error bound or formal global-chart differentiability proof is claimed.

## Quantitative disposition and limits

| h | Recorded all-row weighted error | Eligibility |
|---|---:|---|
| 1e-4 | .0012606383580454328 | Coarse material crossing; preserve, not a smooth-base error |
| 1e-5 | 4.795468605368447e-10 | Same signed smooth branch |
| 1e-6 | 2.2327768902329827e-9 | Same signed smooth branch |

Both finer errors satisfy the original `max(errors[1:])<=1e-5` quantitative bound by a wide margin. Their modest increase at the smaller h is not a demonstrated tangent defect; no larger-h crossing need be counted as a smooth-branch plateau sample. Existing programme:214 defines smooth-plastic1e-5 with actual charts, and the original quantitative test already scores the two finer h. A branch-eligible assessment of those finer samples is legitimate without weakening the threshold, floor, field or fixtures. It does require root's explicit assessment/test disposition: the unchanged original test still fails its coarse same-activity assertion before these errors. Preserve that failure and source history; do not relabel the historical pytest run PASS. This evidence supports one original directional check at this accepted fixed-predecessor state, not whole-matrix identity, all directions, simultaneous J2 plasticity, Newton convergence, capacity or qualification.

No consequential B field/origin/metric defect was found. Capture branch margins are diagnostics reconstructed from high/low recovery and the fixed law, not a new constitutive backend. Their finite Decimal representation is not a universal error certificate. Endpoints plus source structure are sufficient for the bounded branch eligibility claim above; they do not justify a blanket endpoint-only branch rule.

## Limited A review

The three saved parent factors1/.9375/.90625 have parent relative equilibrium .11982400297/.06190043944/.02545860031 and gaps below1e-12. For each parent, all13 saved ordinary dyadic amounts1..1/4096 use the same origin digest; comparison of saved max(relative,gap) finds **no strict merit decrease**. Thus the captured rejection is consistent with the current acceptance condition and is not event-proposal starvation. These comparisons do not establish why the Newton direction/global merit fails.

A's recorded rich-direction errors (.0811159,6.58317e-5,.000350837) do not pass1e-5 at the two finer h. A is J2-active; its Q4 callback snapshots contain origin/candidate data but this capture does not attach explicit pointwise J2 numerical-switch/hardening-interval labels. This review did not reconstruct the J2 return map or establish the full stencil's branch eligibility. Consequently those errors establish neither an eligible smooth tangent defect nor a derivative pass. No cause, instability claim, backend/tolerance change, extra budget or new run follows. A remains the separate unresolved scientific decision.

## Exact identities

Current source/tool hashes match every entry of binding-paired-v1, SHA256 `32cee42c38941d541fa92b082303851a36f5e7e868d9f1626d1af376adbc3b23`. Relevant runtime source hashes match it too: cell `eec240e30d5818a84c197984db1c74e2a59a2fe377ff32193925f24aca76fa88`; retained `8502ce1f85474002cfa15d6ca3dcade9c837a8cd764c2ec19dc1c6e349184bab`; driver `2444b034b679cb5539af8b068b77133b02181d4bd1cd7215029ae7814f7d3c6b`; owner `5e69826bf4d10a0d0d82969eec9ca3aade301d1e56ffb9de3d3f7ab6c8e9efe1`; strict test `da08cde385f96718b922378f8735adabe98e2c6c5eee4760caa8391712f2d279`. Current and executed-paired-v1 copies of capture/entry match `eea6efc48cbd7246e4d83263debff39229f2d64bf33aca54b8ff54cf6520fb6c` / `f88ad96e4bdc68520133d27cbbcc4f81a6e6eaa752f7c83d4f479165597e710e`.

All following files are relative to paired-v1, SHA256:

| File stem | .json | .npz |
|---|---|---|
| B-base | f97566f36fb0a21c26935163aa4fa13bc1799459ae5235ade67d3d3b3d62c209 | 89d0d510168e1ab1a6ec45500d435df368acf506cd205846c528898d4a855391 |
| B-plus-0.0001 | ac599ce6c8d8de164eb1d0503e187dccd0126e7fb92490f29188735c6da26156 | 3ad00377c095113ebe74a456f408efd5c3bc3bd329feabafc27389fbff1cfcf5 |
| B-minus-0.0001 | 90c3496ba703262e70373d502c83f62559e12a3960a0870f0a4ba18f7f4b13e7 | 3932830e7e6c45e1f7be3a7e98053ac485fe51e8cc3d0c4e189c90b8775a3463 |
| B-plus-1e-05 | f3efbe5e2bea5537e1beea3a72b072901f07318a60c78b86a26de6518ea48cda | 205d51625f7d42f9859c1caa8bd81306b07df06b9bf07d702cc7be9527600df4 |
| B-minus-1e-05 | afb82780302f611dff71def418c5ed6e69f0ec04aba9be5ab1c0da35323ce039 | 02acc2b62605153995f21ee50faaf64240c74c2b540fcbf4ea09fbb781f1efb5 |
| B-plus-1e-06 | 54d9fcd39a03f6f69e4b1ffbd6f871842ed41c2e59c81e13919998009978dde8 | 307e386c10ca0044d676933dd766cf760db928e2eb44f72715b4e8c7bfc84937 |
| B-minus-1e-06 | b8ce74b7a38a0cf26ec86b52acc57a4ed3845c3b925a0e0dee9a8cff2b3e5a7f | 4dd96111b32ff452e24d35ae3636fb36d1cb5d71b58ecce22811d9148d6d6818 |

B-origin.json `8db5cd8054d36f22b6940d137c2112007291d70bc2051f6d8186e68546f0540b`; B-direction.npz `add4e42f6c6503667c9318722cff32a41c05549c874f9842a46d603bec958ebb`; result.json `76befe08e12107f2d35159b5ee4af07d70cb54f8a066cff4b1d0d2f978d98c64`; runtime.json `293de44d6911292b27b38981a0473245bc1e40528e5fe2a27f90c5df60357083`; execution.json `7b24b186b6e8dd41397b8b4f2a068f241e7c71cbd79d2473166c6ecfaa188446`; counts.json `5e1d2ae95b2b471e72dd3857e22b09b6bf20d6e6338a287a9d43c7788ffb0faa`.

Limited A merit inspection binds all42 A-failure-{1,2,3}-{parent,candidate-00..12}.json. SHA256 of sorted records `relative_name + NUL + file_sha256_hex + LF` is `436911487183809f8dde2d32824047280dd67cf422e3ce58d9b6b30e1df5bf33`. This binding denotes saved-merit/origin comparison, not complete A branch/operator validation.

Independent non-author OpenAI fallback. No different-family qualification or aggregate acceptance.
