# F03 fixed-Q6 second nested-x pilot

23 September 2026. **Predeclared preparatory diagnostic, not a scientific
registration.** X0 is the original default Q6 grid. X1 is the previously
frozen grid that bisects every X0 x-cell wider than `0.25`. The X1
Q4/Q5/Q6 p pilot failed one absolute-change row, which remains failed.
This second pilot examines fixed-Q6 spatial sensitivity without replacing
or altering that result.

Construct `X2` from exact binary64 `X1` by bisecting every X1 x-cell
whose width is **greater than or equal to `0.25`**, then sorting the union.
This caps the four remaining quarter-length cells at half a beam quarter
without selecting a cell from any observed response. It adds exactly
`-0.375`, `0.375`, `0.625`, `1.375`. Keep default y, pads, represented `J`,
supports, load, section, material, and normalizations unchanged. X2 has
16 x-cells, 25 represented station intervals, three one-ulp intervals,
5,890 free Q6 coordinates, and 6,014 total physical nodal coordinates.
An independent read-only exact-float/Fraction crossing check found no
displaced interior event. Resource admission must be raised exactly for
this declared X2 case and verified before its solve.

Before execution, verify h-prolongation and the nested shell/beam work,
load, root, tip, and solved Ritz-energy identities on a bounded model.
Then run Q6 on X2 once with the same full signed output and precise
functional route used on X1. Compare Q6 X0→X1 and X1→X2 on all 49 signed
components and the complete H1-dual functional. Retain the unchanged
pairwise `1%` normalized limit, final absolute-change rule
`|X2-X1| <= |X1-X0| + 1e-5*S`, and functional final-change allowance
`10 N`. Include the eight physical bands, notably the previously failed
quarter-2 moment, quarter-3 Fy, and near-root Fy. Preserve all numerical
guards, full raw state, timings, source and environment identities, and
independent band-wrench checks.

The prior X0 and X1 records are exploratory inputs for this unregistered
pilot. Any eventual one-use scientific gate must freeze source, cases,
criteria, hardware and limits, then rerun all three levels. A passing
three-grid screen cannot by itself qualify native B3-GE/E4-PL coupling or
complete G0B. A failed component remains failed; do not change the
criterion after seeing X2.

Independent read-only mechanics review recommended this bounded sequence
and found no preparatory objection. The reviewer did not edit or solve it.
