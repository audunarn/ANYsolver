# F03 external B31/CPS feasibility canary (exploratory)

21 September 2026. **Executed mixed response, not an F03/G0B pass or a matched
native B3-GE reference.** The single cold run used CalculiX 2.23 executable
SHA-256 `27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`,
one CPU thread, and the source-identified generator
`scripts/probe_b3_ge_e4_pl_g0_f03_ccx_b31_mixed.py` SHA-256
`adc69c0f12b4c2fbb47d3bec77f8df3294cf51d4ce9e15867a50817985a59f89`.

Exclusive raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-b31-mixed-q4-ns2-nb4-smooth-v1/`.
Generated LF deck-content SHA-256 `3a9074fb6a12fa5ce4877c0b14eca14158ae5230e9da24bc6d78791eb2cc13ad`;
stored CRLF `b31mixed.inp` SHA-256
`06bdea2e4280b0c74b7830b4b30b73d84a1fb0bd188505e99cbadab2251b6cd8`;
DAT `0ebaa1a9d8ab9c71384bce52281cd184ebc2a0c118b87449b336826830c55ea1`;
result record `8e6eba4118a5607d42f36e3f12a135f00FDB43D795BCB3AD7FEC9465B536795B`.
The raw stdout, stderr, status, FRD, solver files and deck are retained there.

Eight CPS4 elements of thickness 0.07 m and four B31 rectangular 0.1 m by
0.1 m beam elements were connected at four non-root beam stations by twelve
four-sample nodal equations. End columns of the panel and the beam root were
fixed. The beam received an integrated smooth 1 MN total vertical line load.
The root shell footprint is not tied. This is a finite station collocation
model, not the exact continuous multiplier line law. B31's rectangular section
and its expanded formulation have a different shear/section idealization from
the native B3-GE and U1 generalized section. It is useful as an independent
external execution and physical-response check only after matching the
idealizations and studying convergence.

The process exited zero and reported a finished linear solve (103 equations,
2318 lower-triangular nonzeros). The beam tip displacement was
`+3.756405e-5 m` vertically. Reconstructing four-sample shell trace
translations from the printed shell nodes gave beam-minus-trace station gaps
of `+3.2e-12, -3.2e-12, +0.1e-12, +3.16e-12 m` in the printed seven-digit
data; x gaps were below `5e-21 m`. These are nodal equation checks at printed
precision, not evidence of between-station compatibility, torque transfer,
reaction balance, refinement or native-law agreement. The output did not
request rotations or reactions and those cannot be inferred from the three
printed displacement columns.

The separate U1/CPS mixed attempt ended before a response, while B31/CPS
completed. This establishes a viable stock-executable path for a distinct
external comparator. Next register exact geometries, load/support and
idealization mapping, output parsing including rotations and reactions,
refinement levels and pass/fail quantities before a numerical comparison.
F03/G0B remain open. Preserve the earlier failed U1 evidence unchanged.
