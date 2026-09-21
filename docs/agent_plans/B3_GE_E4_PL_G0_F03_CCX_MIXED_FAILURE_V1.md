# F03 mixed U1/CPS execution feasibility: terminal failure

21 September 2026. **Failed exploratory preprocessing; no coupled response
was produced.** Generator source commit `545291b`, SHA-256
`c88e0b6cb87842c430d605740b6c67bd807b89fb381e60df10b9c0926b47699e`.
The single cold attempt used the verified CalculiX 2.23 executable SHA-256
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
The exclusive root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-coupled-v1-q4-ns2-nb4-smooth/`
holds the complete deck, stdout/stderr, partial solver files and result
record. SHA-256: deck
`d6f351c82f6c3d7644d68b98560ce466e1e80be9212d8a5e8f4889cef0acba3f`,
stdout `7328c35380f110d2a520b5ce6845edd575df55eda4c68d04a04452d288ff8d13`,
result `df25895d5b301ddfa7972339c83cfa313a31b5a3f8b0afad83e8687cad6b1ef5`.

The deck had eight CPS4 elements with 0.07 m thickness, four U1 beam
elements, twelve unique dependent beam-coordinate equations at `s=.25,.5,
.75,1`, and eight-point equivalent nodal integration of the smooth `1e6
(1+.25 cos 2πs) N/m` load. The beam root is fixed but its shell footprint
is **not** tied at `s=0`; finite station collocation is not the continuous
F03 line law. Pre-execution read-only review checked host interpolation,
four-sample centroid/yaw, rigid-motion patch, frames, shell and beam IDs,
supports, equation order and wrapping, thickness syntax and load signs.

The process returned **exit 201** before stiffness solve or displacement
output. Its stdout states `*ERROR in gen3delem: first thickness in node 1
of element 9 is zero`; element 9 is the first U1, not a CPS4 shell.
`result.json` has `failure: null` because that field was reserved for a
timeout; the nonzero exit and stdout are authoritative. No FRD or physical
result exists. Do not count the 12 assembled deck equations or the load
inventory as executed mechanics.

Independent postfailure review matched this to the open upstream
[CalculiX mixed-U1 defect #170](https://github.com/Dhondtguido/CalculiX/issues/170):
`gen3delem.f` enters a thickness expansion path for `U1` when another 1D/2D
element is present, although the valid U1 general beam section does not
populate that thickness. The working beam-only U1 run and this first mixed
failure are consistent with that mechanism. There is no evidence that
increasing shell thickness or assigning an invented U1 thickness would
correct the mechanics.

**Disposition:** preserve the failure unchanged. The stock 2.23 U1+CPS
route cannot supply this programme's mixed physical reference. Options for
a separately reviewed next route are a source-identified CalculiX build with
the narrow upstream exclusion and independent mixed canary; a conventional
beam external continuum comparator with explicitly different section/shear
idealization; or an independently implemented resolved operator. None has
yet produced the required four-sample coupled response. F03/G0B stay open.
