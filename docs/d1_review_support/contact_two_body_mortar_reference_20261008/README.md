# Independent two-body mortar reference

This is code verification and a frozen-pose response discriminator. It changes no product, contact law, structural mesh, pressure space or public admission. Engineering acceptance, pressure/spatial acceptance and mesh-uniform stability remain open.

## Independent contact reference

oracle.py has no solver imports. It constructs the source corner-0 projection chart, clips convex projected polygons, independently inverts both original bilinear Q4 maps, and integrates their original material shape values. Integration triangles partition the projected domain only; neither surface is replaced by triangular interpolation. Pointwise reference/current projected Jacobians and the moving source physical normal remain in the integrand.

For every positive source support, S_i=integral(N_i dAref), a_i=integral(N_i g dAref), and fixed-supported-force work psi=sum(z_i a_i/S_i). Differentiating this scalar retains moving overlap, support normalization, source normals and both-body inverse-map terms. Independent finite differences use frozen skin-coordinate steps 2e-6/1e-6 m with Richardson extrapolation. Tensor Gauss/Duffy orders 8/12 verify scalar self-resolution first. An exact Fraction rectangle reference at a common 60-degree rigid frame separately checks Q1 support, cross-body normal work and nominal 0.2 um clearance.

The independent physical-spin map uses h*d_current cross force for nodal couples. Additive chart perturbations use the separately reconstructed exponential left Jacobian. Spatial residual derivatives remain generally nonsymmetric. The q/z directional test uses outer steps 2e-4/1e-4 and asserts both outer-step resolution and inner-FD influence before the 1e-5 tangent gate.

Force and moment scales are separately Fref=1e-4 N and Mref=1e-4 N m. Their SI numerical values happen to agree in this fixture, allowing the reported combined residual sums; this is not a general unequal-scale implementation. Translation/angle response norms use 1 m/1 rad separately. The force/work code gate remains 1e-6. Accepted physical equilibrium, complementarity and exact dimensional gap gates are reused unchanged, including control reactions on all static-BC-free coordinates. Only compliance removes prescribed path coordinates.

## Overlap-only work allocation

Two registered source-material X bins, [.1,.6] and [.6,1.1], integrate a_i_bin only inside actual projected overlap. Differentiate psi_bin=sum(z_i a_i_bin/S_i), retaining the whole-pose support normalization. Their forces/moments allocate mortar work/reactions and sum to the physical total. The normalization contribution is nonlocal. These bins are not recovered pointwise lambda*n traction or the historical continuum-bin acceptance criterion.

## Fixed-structure discriminator

The actual refined slide-14 geometry, footprint, constraints and one constrained Kcommon=Kstruct+baseline-fine fixed-z contact K are held identical. Coarse six-node pressure shapes are represented by the material interpolation E on the ten-node fine source geometry. S_C=E.T S_F and a_C=E.T a_F are differentiated before normalization; normalized gap rows cannot simply be coarsened.

One registered signed checkerboard trace is projected into the coarse subspace using the independent overlap-reference consistent Q1 mass. It demonstrates approximation/response differences, without attributing the earlier physical resultant shift. Separately, each accepted base/refined lambda=z/S field is mapped to this common geometry and K. These are frozen linear response diagnostics, not alternative coarse nonlinear equilibria or pressure histories. The accepted lambda fields already reflect both structural and pressure-space changes, so the mapped comparison is not a causal decomposition.

The old poses are authenticated immutable fixtures only. They are never resealed, migrated or resumed under another package. See OUTCOME.md and IMPACT.md; raw per-attempt evidence is C:/ANYworkspaceWork/contact_two_body_mortar_reference_20261008.
