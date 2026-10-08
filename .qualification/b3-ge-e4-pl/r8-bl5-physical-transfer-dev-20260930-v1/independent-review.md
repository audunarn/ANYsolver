# Independent review — bounded BL5 physical transfer

Reviewed the recorder, unchanged direct external reference, raw/derived Fy and Mx outputs, native three-case recovery, comparison script and `results.md`. No numerical jobs or source edits were performed. No actionable mechanical or recording defect was found in this fixed reference-linear scope; the disposition in `results.md` is supported.

## Identities and evidence

- Source parent: `8b8bf6bb4726f1550d987e844e7ea0ea43813e5b`.
- Installed ANYsolver wheel: `615596739690168a5ecc7f02ac3a20a078cda5490e79604a50440a61a7d2f597`.
- External recorder: `506c5259afddfab1872c50c2a2544a7cb706b4cf14e6e7c6b4771d80a0ff98cc`.
- Unchanged direct reference: `5d3616e5fc6f198adc8c0442e01c27c5b7b719e73059f5088561d0027e826f47`.
- OpenSees binary: `25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96` (3.8.0, Python 3.12.14).
- Native three-case recorder: `d47f92d925b009f2852484286c0b9e76d3126553f51bda4b8aa923321d8cb4df`.

Both external cases retain 51 primary poses, 32 finite global element covectors and 85 actual equation rows. Shell nodes 1/18 are fixed in all six components; the only applied load is the declared beam-tip Fy or Mx. Source hashes match the summaries, and the direct reference has no working-tree diff. The installed impact inventory independently confirms nine cases, no failures or skips.

## Mechanics and support roles

The recovery correctly derives `C_b.T lambda = L_b-G_b` from unsupported beam equilibrium. Loads exerted by the connection are `-C.T lambda`; fixed-shell ground loads are `G+C.T lambda-L`. Read-only reconstruction from raw element covectors and recorded equations reproduces the retained transpose action and ground action exactly. Raw covector work agrees with retained internal work to rounding. The sixth beam spin component and free shell rows provide independent equilibrium checks beyond the five beam components used to derive multipliers. Work is covector work, not half the linear strain energy.

External root equations transfer into the fixed shell. Their beam-side action corresponds to the native direct beam-ground role, with the opposite shell-side action kept separate. The five root kinematics are equivalent here; the full discrete operators are not. Comparison uses the correct beam-ID offset (+900), common beam-root moment origin and declared 1 m pose normalization. Summing both domains would cancel the interface observable.

The Mz witness independently transfers ±10.000000000000007 Nm through force arms, with zero direct normal couple and drilling constraint columns. Reference-lift moments are included in the native work pullback. This is a distributed normal-couple load path, not an independent normal-spin moment multiplier.

## Disposition and limits

Small applied-work differences (Fy −0.46499%, Mx +0.08721%) do not establish transfer accuracy. In Fy, native/external root Fy is 153.48163/124.17015 N and root Mx about the beam root is 14.07137/12.14927 Nm. Shell pose difference is 1.92789%. These material differences remain visible despite total balance; nodal root/nonroot splits are resolution-dependent.

Retain BL5 ports and the declared supports. A bounded growing-space/ratio screen and integrated or fixed-distance transfer/work comparison is justified, using common physical regions or test fields and treating termination contributions separately. Freeze supports, actions, metrics and outcome decisions before execution; do not tune multiplier spaces to tip agreement or resume isolated axial refinement.

No whole-response drilling independence, axial torsion fidelity, finite moment admission, convergence, 1% acceptance, F02/F03/M2/G0B/G2 qualification or release follows. Nodal GE six-row, L1 six-channel, BL5 five-channel and B2 finite-vertex laws remain distinct. The initial unmonitored Mz output is not resource evidence; external environment requests do not establish effective OpenSees thread count or sampled peak memory. This review does not authorize new F03 execution.
