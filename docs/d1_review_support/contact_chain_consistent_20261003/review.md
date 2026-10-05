# Supporting source scrutiny — B2-chain consistent tangent

3 October 2026. Read reviewer `/root/beam_surface_contract` did not implement
the kernel or run its tests. This is same-family supporting scrutiny, not
independent engineering acceptance.

The reviewer independently derived the moving-nearest-owner boundary term,
confirmed its positive sign under active compression, half-directional weight
and shared-node/cross-target work mapping. Specific counterexamples identified:

1. Repeated active roots with unchanged selected owner and unequal-work ties at
   source-domain ends require explicit rejection.
2. Identical shared-vertex gradients alone do not establish a smooth branch:
   collinear projection-clamp plateaus must reject.
3. A plateau in a tied competing cell must be checked even when stable ID ordering
   selects another owner. Both numbering permutations are now tested.
4. Decimal arithmetic forming quadratic q before filtering could collapse
   `(s-1)^2-eps^2`, eps=1e-100, onto the domain endpoint. Exact verified radical
   enclosures and rational q/c/q now preserve the tiny interior root; overlap is
   checked before domain filtering.

These findings were corrected with focused source tests, then actual installed
checks. Final Read assessment found no specific error in the root-enclosure fix:
exact squaring verifies the radical bounds, rational q preserves tiny separation,
quotient sorting handles coefficient signs, and nonroot domain-end overlap fails.
Irrational cuts remain enclosure midpoints. Neither source scrutiny nor passing
checks provides a rigorous arbitrary-geometry integration certificate.

All initial spurious-root, panel, fixture and legacy integration failures remain
in raw.zip. No cap, physical law, acceptance tolerance or historical default
changed. The final public capability still reports no engineering/application
admission. Broader refinement, physical endpoints and full D3 remain open.
