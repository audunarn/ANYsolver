# F03 external B31/CPS refinement screen: no converged target

21 September 2026. **12/12 exploratory external solves completed; F03/G0B
remain open.** Registration was committed at `4eed859` before execution.
The exclusive evidence root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-b31-refinement-v1/`.
`manifest.json` SHA-256
`ff5c14d9da1025b60f6bce75031545587591023b29587f5c902a0914888b4481`,
`inventory.json` SHA-256
`efc17bc28d9b488ff08d83c366855272469e3d5d02132a190d6b5fe9e3638dd5`.
An additive read-only raw-file adjudication, `artifact_hashes.json`, SHA-256
`3d8a840f7e5d60e0b88c8b47230dd18d168c54ffbd6b4cc78e6c1fc9ff1ff573`,
records the stored `.inp` and `.dat` byte hashes for all 12 cases. The
original inventory's `deck_sha256` is the generated LF content hash before
Windows text writing converted line endings to CRLF; it is **not** the stored
input byte hash. The original manifest and inventory were not rewritten.
The manifest binds the runner SHA-256
`329f2017187c16ca45c2f8f01f230fc8b6e1e167782bd2fa4e6f06b40e71eb4f`,
B31 deck generator `adc69c0f12b4c2fbb47d3bec77f8df3294cf51d4ce9e15867a50817985a59f89`,
trace generator `c88e0b6cb87842c430d605740b6c67bd807b89fb381e60df10b9c0926b47699e`,
stock CalculiX 2.23 executable
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`,
one OpenMP thread and the 12 frozen cases. Per-case raw deck, status, DAT,
FRD, stdout, stderr and solver files remain in their exclusive subdirectories.

Beam-tip vertical displacement in micrometres, from the seven-digit printed
nodal displacement field:

| Panel/load | Ns2 Nb4 | Ns4 Nb8 | Ns8 Nb16 |
|---|---:|---:|---:|
| CPS4 smooth | +37.56405 | +42.52594 | +40.58379 |
| CPS4 sine | -5.681550 | -6.688768 | -7.501939 |
| CPS3 smooth | +35.98799 | +39.71544 | +37.58503 |
| CPS3 sine | -5.614547 | -6.337305 | -6.914832 |

The smooth tip changes sign of refinement increment after the middle level:
CPS4 changes +13.2%, then -4.6%; CPS3 changes +10.4%, then -5.4%.
The signed-load tip magnitude continues to grow: CPS4 +17.7% then +12.2%,
CPS3 +12.9% then +9.1%. Fine-level CPS4/CPS3 tips differ by about 8% for
either load under this comparison. Thus this three-level run does not show a
converged physical response or an accepted cross-formulation comparator.

All printed translation gaps at the constrained stations are at most
`5.75e-12 m` for the smooth load and `5.25e-13 m` for sine. These numbers
mostly reflect rounded DAT output and do not establish off-station
compatibility, yaw agreement, or physical connection work. The DAT also has
an RF block, but it was not parsed or qualified as a support/interface
reaction; MPC force accounting requires a separate derivation. The model
uses an expanded conventional B31 rectangular section and finite station
collocation; it is neither native B3-GE/E4-PL nor a continuous exact weak
coupling. The panel width retains two transverse cells throughout the three
levels. No candidate multiplier space is selected from this trend.

**Disposition:** keep this complete external execution as independent
feasibility evidence. Before it can serve as a physical comparison, register
and execute a mesh-converged reference with matched beam/shear, shell,
support and load idealizations and a work/balance audit. The native
constraint-stability and physical-response problem also remains unresolved.
Independent read-only pre-execution and post-run reviews verified the case
inventory, source identities, outputs and limitations. The post-run review
identified the LF/CRLF deck-hash distinction recorded above; no correctness
or qualification acceptance was inferred from the completed processes.
