# F03 classical plane-stress endpoint: point rows lack an energy bound

22 September 2026. This is a **continuum regularity derivation for the proposed independent planar reference**, not a production E4-PL/B3-GE attachment qualification. The reference shell's in-plane displacement is in `H¹(Ω)^2` on a two-dimensional panel, with a positive plane-stress energy equivalent to the relevant supported `H¹` norm. Each of the four material shell samples at the attachment start is an isolated physical point in the panel interior. A direct translational root equation would evaluate their weighted centroid at those four points.

Fix one sample point `x0` and a disk of radius `R` lying inside the panel and excluding the other three sample points. For `0<ε<R`, define a continuous radial scalar field

```text
vε(r) = 1                         for 0 ≤ r ≤ ε,
        log(R/r)/log(R/ε)          for ε < r < R,
        0                         for r ≥ R.
```

It has `vε(x0)=1`, while direct polar integration gives

```text
∫Ω |∇vε|² dA = 2π / log(R/ε) → 0.
```

Also `vε→0` almost everywhere and `|vε|≤1` on a fixed disk, so its `L²` norm tends to zero. Thus its `H¹` norm tends to zero although its value at `x0` remains one. A vector displacement supported at that one sample changes the nonzero-weight four-sample centroid but costs vanishing continuum shell energy. Point evaluation, and hence the proposed exact two-row root-centroid evaluation, is **not a bounded linear functional** on this shell's energy space. The shell trace on a one-dimensional material line supports an integrated weak pairing, but this calculation gives no separate bounded endpoint point row.

An algebraically independent finite-element root row is therefore insufficient evidence for a mesh-stable continuum endpoint law. Refining an exact point tie can create a localized response with changing stiffness and point reaction, even when its assembled rank stays full. The same bump construction applies at an isolated sample at **any interior station** along the line: removing an endpoint band does not make pointwise evaluation uniformly controlled by shell H¹ energy. The supported trace on the one-dimensional line admits an integrated L² pairing; a maximum of a particular finite-element polynomial gap is a valid *discrete diagnostic*, not by itself a mesh-uniform continuum trace bound. No exact root translation or yaw point equation is added to the primary classical variational line comparator. The rooted beam boundary condition remains, and the shell/beam line gap is paired weakly on the physical open interval; the endpoints have zero measure in that integral. Report discrete endpoint and interior pointwise behavior explicitly. If the engineering connection requires physical transfer through a root region, derive a **fixed-physical-extent** integral footprint/patch with its own work, quadrature, moment transfer and refinement tests, then call it a distinct model.

This proof rejects the *point-row premise* of the provisional independent reference design; it does not prove an exact-multiplier line law stable, select P0/P1, remove G0's point-attachment requirement, or establish actual E4-PL shell pose regularity in all supported formulations. A point attachment in the final mixed programme needs its own physically justified shell pose/footprint contract and independent tests. The earlier root-included and root-omitted **finite station** comparators are different models and remain useful sensitivity evidence, not continuum endpoint oracles.
