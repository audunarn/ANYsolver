# F03-K3 P0 line-space comparison: completed diagnostic, no selection

21 September 2026. Candidate `52ed330f00963456589c41e3537f0fe0ad82c6bf`.
The frozen registration is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-k3-p0-v1-registration.json`
(SHA-256 `da7d1721c69d7a93a566caa929958de8b45a8534cad552d4ddd122155519d63d`).
The single execution produced immutable raw records under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-k3-p0-v1/`
(raw SHA-256 `82d150caea366d1181a367c2d844609fb6ae2ebb54020d8c63c9c7b09c6e4725`)
and a sibling `.attestation.json`. Historical K2P/K2L evidence remains unchanged.

The external supervisor recorded exit 0, no violation or read error,
94.63 s and 346,324,992 bytes sampled peak child RSS. All 26 ordered
Q4/S3-V2D meshes, 52 P0 candidate slots and 104 smooth/sine physical
loads completed locally. The maximum forward full/condensed parity was
`8.9166e-11` (frozen limit `1e-10`); maximum normalized weak residual
`3.51e-14`, free equilibrium `9.31e-14`, support force/moment imbalance
`3.24e-13`, and load-quadrature difference `1.70e-15`. All nine-station
traces and one-sided traction evaluations are present. P0 has zero
within-cell derivative and nonzero cell jumps, retained in the record.
These checks establish a complete local numerical diagnostic, not
physically acceptable coupling.

Selected smooth-load physical observations (gaps normalized by the
registered K2P displacement scale):

| Mesh | Space | Max pointwise gap | Active shell energy (J) |
|---|---|---:|---:|
| Q4, beam 8 / shell 1 | P0-beam | 0.098709 | 0.894952 |
| Q4, beam 8 / shell 1 | P0-shell-grid | 1.017444 | 17.58080 |
| Q4, beam 8 / shell 64 | P0-beam | 0.125318 | 13.08610 |
| Q4, beam 8 / shell 64 | P0-shell-grid | 0.004879 | 5.432758 |
| S3-V2D, beam 8 / shell 1 | P0-beam | 0.097953 | 1.130928 |
| S3-V2D, beam 8 / shell 1 | P0-shell-grid | 1.014965 | 17.57708 |
| S3-V2D, beam 8 / shell 64 | P0-beam | 0.115811 | 11.86928 |
| S3-V2D, beam 8 / shell 64 | P0-shell-grid | 0.002933 | 4.909113 |

The coarse Q4 P0-beam sine response transfers only `1.03e-30 J` of
active shell energy, whereas P0-shell-grid has a `0.6531` pointwise gap.
At fixed Q4 beam count 8, shell counts 8, 16, 32, 64 give P0-shell-grid
smooth shell energies `12.2805, 6.09899, 5.62843, 5.43276 J`, with
traction-y oscillation measures `5.153, 6.560, 9.033, 14.294` and
increasing squared jumps. P0-beam shell energies tend toward `13.0861 J`
while its pointwise gap grows from `0.1121` to `0.1253` under that
shell-only refinement. These responses differ substantially despite
small algebraic residuals. Three-level core refinement and isolated
reciprocal reaches are separately preserved in raw data.

The lower-dimensional coarse-side hypothesis selects shell-grid in ten
meshes and beam-grid in sixteen. It inherits the large coarse-shell
gap and the fine-shell beam-grid gap; it does not cure the reciprocal
behavior. No independent physical response oracle was registered in
K3, so neither the smaller gap nor a nonzero energy proves correct
transfer. **Disposition: complete diagnostic; reject both P0 spaces and
the coarse-side switch as an F03 production selection. G0B and G1
remain open.** Derive and register a different trace-stable interface
candidate with the actual native jump graph, six physical channels,
moment/director/shear tests, and independent response references.
