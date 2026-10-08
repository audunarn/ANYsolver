# Fixed-beam coupled Mx shell refinement — development result

The resolved beam was held at 8×8×4 C3D20 elements. The five-channel P0 law,
20 weak rows, 10 N m section-dual torque, physical offsets and full shell-root
clamp were unchanged. Only the resolved C3D20 shell mesh changed. The coarse
shell stiffness independently matched the earlier assembly to `1.31e-15`
relative entry difference, and its coupled work reproduced the fixed-shell/
fine-beam predecessor.

| Resolved shell elements | Coupled resolved work | Native/resolved work ratio |
|---|---:|---:|
| 2×2×1 | `0.000910019 J` | `1.10994` |
| 4×4×2 | `0.000989371 J` | `1.02092` |
| 8×8×4 | `0.001061106 J` | `0.95190` |

The native eight-Q4/two-B3 work remains the saved `0.001010067 J`. The ratio
crosses unity; agreement at the middle level is accidental evidence, not
converged physical validation. Both solid domains materially affected the
original coarse CalculiX contrast. The final shell increment still changes
work by about 7.25%, so a resolved-shell limit is not established. The fixed
20-row weak interface also does not prove stability or fidelity under growing
trace spaces. All levels passed equation, weak-gap, physical interface-wrench
and work checks.

Decision: stop using the coarse C3D20 result or a single refined level to
select a BL5 multiplier space or connection law. The next qualifying reference
must converge shell, beam and interface resolution together under the declared
physical connection, and compare with native Q4/S3/B3 refinement at matching
physical idealizations. Existing native refinement fixtures require checking
their root and line policies before reuse; their saved ratios are not silently
transferred to this specimen. This development series is not F03 or external
accuracy acceptance.

[Receipt](receipt.json) and [raw levels](levels/) record the source/parent
identities, observed CPU0/one thread/JIT-off, `6.27 s` process wall and
`336.7 MB` sampled peak process-tree RSS. No new CalculiX execution ran.
